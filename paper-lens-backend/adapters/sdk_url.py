"""Claude Code --sdk-url WebSocket adapter.

Spawns the CLI with --sdk-url pointing back to our server's WebSocket endpoint.
The CLI connects as a WS client, speaks NDJSON. We parse messages and emit
SessionEvent objects through the same interface as the old ClaudeCLIAdapter.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator, Optional
from uuid import uuid4

from fastapi import WebSocket

from .base import SessionInterface, SessionEvent, EventType, QuestionData

logger = logging.getLogger(__name__)


class SdkUrlAdapter(SessionInterface):
    """Adapter using claude --sdk-url for bidirectional WebSocket communication.

    Lifecycle:
      1. start(prompt) — stores prompt, spawns CLI subprocess pointing at our WS
      2. CLI connects to /ws/cli/{session_id} → on_cli_connect() is called
      3. CLI sends system/init, we send user message with the prompt
      4. We parse incoming NDJSON, auto-approve tools, emit events
      5. send_message(text) — sends a new user message over the WS
    """

    def __init__(self, working_dir: str, server_port: int):
        self.working_dir = working_dir
        self.server_port = server_port
        self.session_id: str = str(uuid4())
        self.claude_session_id: str = ""

        self._event_queue: asyncio.Queue[SessionEvent] = asyncio.Queue()
        self._cli_ws: Optional[WebSocket] = None
        self._cli_connected = asyncio.Event()
        self._pending_prompt: Optional[str] = None
        self._message_buffer: list[dict] = []  # queued until CLI connects
        self._process: Optional[asyncio.subprocess.Process] = None
        self._process_monitor: Optional[asyncio.Task] = None
        self._stopped = False

        # Parked AskUserQuestion permission requests:
        #   request_id -> original tool input (dict with "questions" key)
        # Waiting for server-side resolution via answer_question().
        self._pending_questions: dict[str, dict] = {}

    async def start(self, prompt: str) -> str:
        """Store prompt and spawn CLI. Returns session_id."""
        self._pending_prompt = prompt
        await self._spawn_cli()
        return self.session_id

    async def answer_question(self, answers_text: str) -> bool:
        """Resolve the oldest parked AskUserQuestion with the user's answers.

        We reply to the can_use_tool request with behavior=deny + a message
        containing the formatted answers. The CLI feeds that message back to
        Claude as the tool result, so Claude sees the user's choices.

        Returns True if a pending question was found and resolved; False
        otherwise (in which case the caller should fall back to send_message).
        """
        if not self._pending_questions:
            return False
        # Pop the oldest parked request
        request_id = next(iter(self._pending_questions))
        original_input = self._pending_questions.pop(request_id)
        questions_meta = original_input.get("questions", [])
        logger.info(f"Resolving parked AskUserQuestion request_id={request_id}")

        deny_message = (
            f"[User answer]\n{answers_text}\n\n"
            f"(The user replied to AskUserQuestion directly. "
            f"Proceed using these choices.)"
        )
        response = {
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": request_id,
                "response": {
                    "behavior": "deny",
                    "message": deny_message,
                },
            },
        }
        try:
            await self._send_ndjson(response)
        except Exception as e:
            logger.error(f"Failed to send question answer: {e}")
            return False
        return True

    async def send_message(self, message: str) -> None:
        """Send a follow-up user message over the WebSocket."""
        msg = {
            "type": "user",
            "message": {"role": "user", "content": message},
            "parent_tool_use_id": None,
            "session_id": self.claude_session_id,
        }
        if self._cli_ws:
            try:
                await self._send_ndjson(msg)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                raise RuntimeError(f"发送失败：CLI 连接已断开") from e
        else:
            self._message_buffer.append(msg)

    async def events(self) -> AsyncIterator[SessionEvent]:
        """Yield events continuously.

        Only breaks on EventType.DONE (session fully ended — subprocess exit
        or explicit stop) or EventType.ERROR. TURN_DONE does NOT break the
        loop: it signals "current assistant turn complete, session still
        alive waiting for next user message", so the SSE stream stays open
        for multi-turn conversations.
        """
        while True:
            event = await self._event_queue.get()
            yield event
            if event.type in (EventType.DONE, EventType.ERROR):
                break

    async def stop(self) -> None:
        """Clean up subprocess and connection."""
        self._stopped = True
        if self._process_monitor and not self._process_monitor.done():
            self._process_monitor.cancel()
            try:
                await self._process_monitor
            except asyncio.CancelledError:
                pass
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    self._process.kill()
                except ProcessLookupError:
                    pass
            self._process = None

    # ── CLI WebSocket connection handling ──────────────────────────────

    async def on_cli_connect(self, ws: WebSocket) -> None:
        """Called when the CLI subprocess connects to our WS endpoint.

        Runs the full receive loop — returns when CLI disconnects.
        Per protocol, the SERVER must send the first user message — the CLI
        waits for it before responding with system/init.
        """
        self._cli_ws = ws
        self._cli_connected.set()
        logger.info(f"CLI connected for session {self.session_id}")

        # Send initial user prompt immediately (don't wait for init)
        if self._pending_prompt:
            user_msg = {
                "type": "user",
                "message": {"role": "user", "content": self._pending_prompt},
                "parent_tool_use_id": None,
                "session_id": self.claude_session_id or "",
            }
            try:
                await self._send_ndjson(user_msg)
                logger.info(f"Sent initial prompt ({len(self._pending_prompt)} chars)")
                self._pending_prompt = None
            except Exception as e:
                logger.error(f"Failed to send initial prompt: {e}")

        try:
            while True:
                msg = await ws.receive()
                logger.info(f"CLI WS frame: type={msg.get('type','?')} keys={list(msg.keys())}")
                if msg['type'] == 'websocket.receive':
                    raw = msg.get('text') or (msg.get('bytes', b'').decode('utf-8', errors='replace'))
                elif msg['type'] == 'websocket.disconnect':
                    logger.info("CLI disconnected")
                    break
                else:
                    continue
                logger.info(f"CLI raw ({len(raw)} chars): {raw[:300]}")
                for line in raw.strip().split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning(f"Non-JSON from CLI: {line[:120]}")
                        continue
                    await self._handle_cli_message(data)
        except Exception as e:
            if not self._stopped:
                logger.error(f"CLI WS error: {e}")
                await self._event_queue.put(
                    SessionEvent(type=EventType.ERROR, data=f"CLI disconnected: {e}")
                )
        finally:
            self._cli_ws = None
            if not self._stopped:
                await self._event_queue.put(SessionEvent(type=EventType.DONE))

    # ── Internal ──────────────────────────────────────────────────────

    async def _spawn_cli(self) -> None:
        """Spawn claude subprocess with --sdk-url pointing at us.

        Required flags (see claude-code-websocket-protocol.md):
          --print / -p                   — headless mode
          --output-format stream-json    — NDJSON output
          --input-format stream-json     — NDJSON input
          --verbose                      — include stream_event deltas
          --include-partial-messages     — token-by-token streaming chunks
        The `-p "placeholder"` prompt arg is ignored by CLI; the CLI waits for
        the first `user` message over the WebSocket.
        """
        ws_url = f"ws://localhost:{self.server_port}/ws/cli/{self.session_id}"
        cmd = [
            "claude",
            "--sdk-url", ws_url,
            "-p", "placeholder",
            "--output-format", "stream-json",
            "--input-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        logger.info(f"Spawning CLI: {' '.join(cmd)}")
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir,
        )
        self._process_monitor = asyncio.create_task(self._monitor_process())

    async def _monitor_process(self) -> None:
        """Watch for subprocess exit and report errors."""
        if not self._process:
            return
        try:
            return_code = await self._process.wait()
            if return_code != 0 and not self._stopped:
                stderr_bytes = b""
                if self._process.stderr:
                    stderr_bytes = await self._process.stderr.read()
                err = stderr_bytes.decode("utf-8", errors="replace").strip()
                logger.error(f"CLI exited with code {return_code}: {err[:500]}")
                await self._event_queue.put(
                    SessionEvent(type=EventType.ERROR, data=f"CLI exited ({return_code}): {err[:300]}")
                )
        except asyncio.CancelledError:
            pass

    async def _send_ndjson(self, msg: dict) -> None:
        """Send an NDJSON message to the CLI via WebSocket."""
        if self._cli_ws:
            text = json.dumps(msg, ensure_ascii=False) + "\n"
            await self._cli_ws.send_text(text)

    async def _handle_cli_message(self, data: dict) -> None:
        """Route a parsed NDJSON message from the CLI."""
        msg_type = data.get("type")

        if msg_type == "system":
            await self._handle_system(data)
        elif msg_type == "assistant":
            await self._handle_assistant(data)
        elif msg_type == "user":
            await self._handle_user(data)
        elif msg_type == "stream_event":
            await self._handle_stream_event(data)
        elif msg_type == "result":
            await self._handle_result(data)
        elif msg_type == "control_request":
            await self._handle_control_request(data)
        elif msg_type == "keep_alive":
            # Respond with keep_alive
            await self._send_ndjson({"type": "keep_alive"})
        elif msg_type in ("tool_progress", "tool_use_summary", "auth_status",
                          "streamlined_text", "streamlined_tool_use_summary",
                          "prompt_suggestion", "rate_limit_event"):
            # Informational — ignore or log
            pass
        else:
            logger.debug(f"Unhandled CLI message type: {msg_type}")

    async def _handle_system(self, data: dict) -> None:
        subtype = data.get("subtype")
        if subtype == "init":
            self.claude_session_id = data.get("session_id", "")
            logger.info(f"CLI initialized, session={self.claude_session_id}")
            await self._event_queue.put(SessionEvent(
                type=EventType.STATUS,
                data={"status": "initialized", "session_id": self.claude_session_id}
            ))
            # Now send the initial prompt
            if self._pending_prompt:
                user_msg = {
                    "type": "user",
                    "message": {"role": "user", "content": self._pending_prompt},
                    "parent_tool_use_id": None,
                    "session_id": self.claude_session_id,
                }
                await self._send_ndjson(user_msg)
                self._pending_prompt = None
            # Flush any buffered messages
            for msg in self._message_buffer:
                msg["session_id"] = self.claude_session_id
                await self._send_ndjson(msg)
            self._message_buffer.clear()

    async def _handle_assistant(self, data: dict) -> None:
        message = data.get("message", {})
        content_blocks = message.get("content", [])

        # Emit usage if present
        usage = message.get("usage", {})
        if usage:
            await self._event_queue.put(SessionEvent(
                type=EventType.USAGE,
                data={
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                },
            ))

        for block in content_blocks:
            btype = block.get("type")
            if btype == "text":
                # Text is typically handled via stream_event deltas already;
                # skip here to avoid duplication.
                pass
            elif btype == "tool_use":
                tool_name = block.get("name", "")
                tool_input = block.get("input", {})
                tool_id = block.get("id", "")

                if tool_name == "AskUserQuestion":
                    # QUESTION event is emitted from _handle_control_request
                    # (can_use_tool) where the request is parked for user input.
                    # Skip here to avoid duplicate cards.
                    continue

                if tool_name in ("Write", "Edit"):
                    file_path = tool_input.get("file_path", "")
                    if file_path:
                        await self._event_queue.put(SessionEvent(
                            type=EventType.FILE_SAVED,
                            data={"path": file_path, "tool": tool_name}
                        ))

                # Generic TOOL_USE with id + input so the frontend can match
                # tool cards with later tool_result by id.
                await self._event_queue.put(SessionEvent(
                    type=EventType.TOOL_USE,
                    data={"tool": tool_name, "input": tool_input, "id": tool_id},
                ))

    async def _handle_user(self, data: dict) -> None:
        """Handle user messages (contain tool_result blocks)."""
        message = data.get("message", {})
        content_blocks = message.get("content", [])
        if not isinstance(content_blocks, list):
            return
        for block in content_blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_result":
                continue
            tool_id = block.get("tool_use_id", "")
            is_error = bool(block.get("is_error", False))
            raw = block.get("content", "")
            if isinstance(raw, list):
                parts = []
                for p in raw:
                    if isinstance(p, dict):
                        parts.append(p.get("text", ""))
                    else:
                        parts.append(str(p))
                content_text = "\n".join(parts)
            else:
                content_text = str(raw)
            await self._event_queue.put(SessionEvent(
                type=EventType.TOOL_RESULT,
                data={
                    "id": tool_id,
                    "content": content_text,
                    "is_error": is_error,
                },
            ))

    async def _handle_stream_event(self, data: dict) -> None:
        """Extract deltas from streaming events."""
        event = data.get("event", {})
        event_type = event.get("type", "")

        if event_type == "content_block_start":
            block = event.get("content_block", {})
            if block.get("type") == "tool_use":
                tool_name = block.get("name", "")
                tool_id = block.get("id", "")
                if tool_name:
                    await self._event_queue.put(SessionEvent(
                        type=EventType.TOOL_USE,
                        data={"tool": tool_name, "id": tool_id},
                    ))

        elif event_type == "content_block_delta":
            delta = event.get("delta", {})
            delta_type = delta.get("type")
            if delta_type == "text_delta":
                text = delta.get("text", "")
                if text:
                    await self._event_queue.put(SessionEvent(
                        type=EventType.TEXT_DELTA, data=text
                    ))
            elif delta_type == "thinking_delta":
                text = delta.get("thinking", "")
                if text:
                    await self._event_queue.put(SessionEvent(
                        type=EventType.THINKING_DELTA, data=text
                    ))

    async def _handle_result(self, data: dict) -> None:
        """Claude CLI emits `result` at the end of each assistant turn.

        We emit TURN_DONE (not DONE) so the client knows the current turn
        is complete but keeps the SSE stream open for the next user message.
        DONE is only emitted when the CLI subprocess actually exits (see
        on_cli_connect finally / _monitor_process).
        """
        is_error = data.get("is_error", False)
        if is_error:
            errors = data.get("errors", [])
            await self._event_queue.put(SessionEvent(
                type=EventType.ERROR,
                data="; ".join(errors) if errors else "Unknown error"
            ))
            return

        result_text = data.get("result", "")
        cost = data.get("total_cost_usd", 0)
        await self._event_queue.put(SessionEvent(
            type=EventType.TURN_DONE,
            data={
                "result_preview": result_text[:200],
                "cost_usd": cost,
            },
        ))

    async def _handle_control_request(self, data: dict) -> None:
        """Handle permission requests from CLI.

        Auto-approve everything EXCEPT AskUserQuestion — that one is parked
        until the server-side receives the real user answer via
        answer_question(), at which point we reply with deny + message so the
        answers flow back to Claude as the tool result.
        """
        request_id = data.get("request_id", "")
        request = data.get("request", {})
        subtype = request.get("subtype", "")

        if subtype == "can_use_tool":
            tool_name = request.get("tool_name", "")
            tool_input = request.get("input", {})

            if tool_name == "AskUserQuestion":
                # Park the request_id and emit a QUESTION event to the UI.
                # Do NOT respond until answer_question() is called.
                questions = tool_input.get("questions", [])
                self._pending_questions[request_id] = tool_input
                logger.info(
                    f"Parking AskUserQuestion request_id={request_id} "
                    f"with {len(questions)} questions"
                )
                await self._event_queue.put(SessionEvent(
                    type=EventType.QUESTION,
                    data=QuestionData(questions=questions),
                ))
                return

            logger.info(f"Auto-approving tool: {tool_name}")
            response = {
                "type": "control_response",
                "response": {
                    "subtype": "success",
                    "request_id": request_id,
                    "response": {
                        "behavior": "allow",
                        "updatedInput": tool_input,
                    },
                },
            }
            await self._send_ndjson(response)

        elif subtype == "hook_callback":
            # Auto-approve hooks
            response = {
                "type": "control_response",
                "response": {
                    "subtype": "success",
                    "request_id": request_id,
                    "response": {},
                },
            }
            await self._send_ndjson(response)
        else:
            # Generic success response for unknown control subtypes
            response = {
                "type": "control_response",
                "response": {
                    "subtype": "success",
                    "request_id": request_id,
                    "response": {},
                },
            }
            await self._send_ndjson(response)
