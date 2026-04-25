"""Claude Code CLI adapter - spawns claude subprocess with stream-json I/O."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import AsyncIterator, Optional
from uuid import uuid4

from .base import SessionInterface, SessionEvent, EventType, QuestionData

logger = logging.getLogger(__name__)


class ClaudeCLIAdapter(SessionInterface):
    """Adapter that wraps Claude Code CLI for local use.

    Uses --print --output-format stream-json --verbose --include-partial-messages
    for real-time token-by-token streaming.
    Multi-turn conversations use --resume with session IDs.
    """

    def __init__(self, working_dir: str):
        self.working_dir = working_dir
        self.session_id: str | None = None
        self.claude_session_id: str | None = None  # Claude's internal session ID
        self.process: asyncio.subprocess.Process | None = None
        self._event_queue: asyncio.Queue[SessionEvent] = asyncio.Queue()
        self._reader_task: asyncio.Task | None = None
        self._has_streaming: bool = False  # Set True when we see stream_event

    async def start(self, prompt: str) -> str:
        self.session_id = str(uuid4())
        self._has_streaming = False
        await self._spawn_claude(prompt)
        return self.session_id

    async def send_message(self, message: str) -> None:
        """Send a follow-up message using --resume."""
        # Kill previous process if still running
        await self._cleanup_process()
        if not self.claude_session_id:
            raise RuntimeError("No active claude session to resume")
        # Drain stale events but keep the same queue reference
        # (SSE generators hold a reference to self._event_queue — replacing it
        # would cause reconnected SSE streams to read from a dead queue)
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._has_streaming = False
        await self._spawn_claude(message, resume=True)

    async def events(self) -> AsyncIterator[SessionEvent]:
        while True:
            event = await self._event_queue.get()
            yield event
            if event.type in (EventType.DONE, EventType.ERROR):
                break

    async def stop(self) -> None:
        await self._cleanup_process()

    async def _spawn_claude(self, prompt: str, resume: bool = False) -> None:
        cmd = [
            "claude",
            "-p",
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--allowedTools",
            "Read,Write,Edit,Bash,Glob,Grep,Skill,Agent,AskUserQuestion,ToolSearch",
        ]

        if resume and self.claude_session_id:
            cmd.extend(["--resume", self.claude_session_id])

        # Pass prompt via stdin to avoid --allowedTools consuming it as a tool name
        logger.info(f"Spawning claude: {' '.join(cmd[:6])}...")

        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir,
            limit=4 * 1024 * 1024,  # 4MB line buffer (default 64KB too small for verbose output)
        )
        # Write prompt to stdin and close it
        if self.process.stdin:
            self.process.stdin.write(prompt.encode("utf-8"))
            self.process.stdin.close()

        self._reader_task = asyncio.create_task(self._read_output())

    async def _read_output(self) -> None:
        """Read stream-json output from claude and parse into events."""
        if not self.process or not self.process.stdout:
            return

        try:
            async for line in self.process.stdout:
                line = line.decode("utf-8").strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Non-JSON output: {line[:100]}")
                    continue

                events = self._parse_event(data)
                for event in events:
                    await self._event_queue.put(event)

            # Process ended
            return_code = await self.process.wait()
            if return_code != 0 and self.process.stderr:
                stderr = await self.process.stderr.read()
                error_msg = stderr.decode("utf-8").strip()
                if error_msg:
                    logger.error(f"Claude stderr: {error_msg}")

            await self._event_queue.put(SessionEvent(type=EventType.DONE))

        except Exception as e:
            logger.error(f"Error reading claude output: {e}")
            await self._event_queue.put(
                SessionEvent(type=EventType.ERROR, data=str(e))
            )

    def _parse_event(self, data: dict) -> list[SessionEvent]:
        """Parse a single stream-json event into SessionEvents.

        With --include-partial-messages, we get two types of events:
        1. stream_event — real-time deltas (text chunks, tool starts)
        2. assistant — complete turn summary (tool inputs with full args)

        Strategy: use stream_events for real-time UI, assistant for structured data
        (AskUserQuestion questions, Write/Edit file paths).
        """
        events = []
        event_type = data.get("type")

        if event_type == "system" and data.get("subtype") == "init":
            self.claude_session_id = data.get("session_id")
            events.append(SessionEvent(
                type=EventType.STATUS,
                data={"status": "initialized", "session_id": self.claude_session_id}
            ))

        elif event_type == "stream_event":
            self._has_streaming = True
            inner = data.get("event", {})
            events.extend(self._parse_stream_event(inner))

        elif event_type == "assistant":
            # Complete turn summary. If streaming was active, text was already
            # sent via stream_events — only extract structured tool data.
            if not self._has_streaming:
                events.append(SessionEvent(
                    type=EventType.STATUS, data={"status": "new_turn"}
                ))
            message = data.get("message", {})
            content_blocks = message.get("content", [])

            # Emit usage if present (for token meter)
            usage = message.get("usage", {})
            if usage:
                events.append(SessionEvent(
                    type=EventType.USAGE,
                    data={
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                    },
                ))

            for block in content_blocks:
                if block.get("type") == "text" and not self._has_streaming:
                    text = block.get("text", "")
                    if text:
                        events.append(SessionEvent(
                            type=EventType.TEXT_DELTA, data=text
                        ))

                elif block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    tool_input = block.get("input", {})
                    tool_id = block.get("id", "")

                    # AskUserQuestion is handled specially
                    if tool_name == "AskUserQuestion":
                        questions = tool_input.get("questions", [])
                        events.append(SessionEvent(
                            type=EventType.QUESTION,
                            data=QuestionData(questions=questions)
                        ))
                        continue

                    # File saving toast (on top of generic tool_use)
                    if tool_name in ("Write", "Edit"):
                        file_path = tool_input.get("file_path", "")
                        if file_path:
                            events.append(SessionEvent(
                                type=EventType.FILE_SAVED,
                                data={"path": file_path, "tool": tool_name}
                            ))

                    # Always emit generic TOOL_USE with full input + id so the
                    # frontend can render a rich tool card and match it with a
                    # later tool_result by id.
                    events.append(SessionEvent(
                        type=EventType.TOOL_USE,
                        data={"tool": tool_name, "input": tool_input, "id": tool_id},
                    ))

        elif event_type == "user":
            # User messages from the CLI contain tool_result blocks
            message = data.get("message", {})
            content_blocks = message.get("content", [])
            if isinstance(content_blocks, list):
                for block in content_blocks:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_id = block.get("tool_use_id", "")
                        is_error = bool(block.get("is_error", False))
                        raw_content = block.get("content", "")
                        # content can be string or list[{type:"text", text:"..."}]
                        if isinstance(raw_content, list):
                            parts = []
                            for p in raw_content:
                                if isinstance(p, dict):
                                    parts.append(p.get("text", ""))
                                else:
                                    parts.append(str(p))
                            content_text = "\n".join(parts)
                        else:
                            content_text = str(raw_content)
                        events.append(SessionEvent(
                            type=EventType.TOOL_RESULT,
                            data={
                                "id": tool_id,
                                "content": content_text,
                                "is_error": is_error,
                            },
                        ))

        elif event_type == "result":
            result_text = data.get("result", "")
            if result_text:
                events.append(SessionEvent(
                    type=EventType.STATUS,
                    data={"status": "completed", "result_preview": result_text[:200]}
                ))

        return events

    def _parse_stream_event(self, inner: dict) -> list[SessionEvent]:
        """Parse an inner stream_event (Anthropic Messages API format)."""
        events = []
        inner_type = inner.get("type")

        if inner_type == "message_start":
            # New assistant turn — clear tool indicator & reset text
            events.append(SessionEvent(
                type=EventType.STATUS, data={"status": "new_turn"}
            ))

        elif inner_type == "content_block_start":
            block = inner.get("content_block", {})
            if block.get("type") == "tool_use":
                tool_name = block.get("name", "")
                tool_id = block.get("id", "")
                if tool_name:
                    # Emit partial tool_use with id so the frontend can create
                    # a card immediately; the full input is filled in later
                    # by the assistant complete block event.
                    events.append(SessionEvent(
                        type=EventType.TOOL_USE,
                        data={"tool": tool_name, "id": tool_id}
                    ))

        elif inner_type == "content_block_delta":
            delta = inner.get("delta", {})
            delta_type = delta.get("type")
            if delta_type == "text_delta":
                text = delta.get("text", "")
                if text:
                    events.append(SessionEvent(
                        type=EventType.TEXT_DELTA, data=text
                    ))
            elif delta_type == "thinking_delta":
                text = delta.get("thinking", "")
                if text:
                    events.append(SessionEvent(
                        type=EventType.THINKING_DELTA, data=text
                    ))

        elif inner_type == "content_block_stop":
            # Content block finished — could be text or tool_use.
            # Tool indicator will be cleared by next text_delta or new_turn.
            pass

        elif inner_type == "message_delta":
            # Contains stop_reason — turn is ending
            pass

        elif inner_type == "message_stop":
            # Turn fully complete — assistant summary follows
            pass

        return events

    async def _cleanup_process(self) -> None:
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    self.process.kill()
                except ProcessLookupError:
                    pass
            self.process = None
