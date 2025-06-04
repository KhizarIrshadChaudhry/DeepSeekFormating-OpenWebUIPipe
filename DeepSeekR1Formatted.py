"""
title: deepseek-ai/DeepSeek-R1-Distill-Qwen-7B Thought Formatter
authors: Neptel
version: 0.1
required_open_webui_version: 0.5.5
license: MIT
"""

import json
import httpx
from typing import AsyncGenerator, Awaitable, Callable
from pydantic import BaseModel, Field


class Pipe:
    """A minimal OpenWebUI pipe that forwards requests to any OpenAI‑compatible
    backend (vLLM, LM Studio, Ollama, etc.) **and** guarantees that the very
    first tokens streamed to the UI begin with `<think>` so OpenWebUI ≥ 0.5.5
    shows its purple “Thinking… ⏳” animation.

    ### 2025‑06‑04 · v0.1.1
    * **Fix 404 «model … does not exist»** ― we now **always overwrite** the
      `model` field in the outgoing JSON with the value from `MODEL_NAME` so
      any stale model names coming from the UI cannot leak through to vLLM.
    * Trimmed a few comments and kept the rest identical.
    """

    class Valves(BaseModel):
        API_BASE_URL: str = Field(
            default="http://localhost:8000/v1",
            description="Base URL of your vLLM / OpenAI-compatible server",
        )
        API_KEY: str = Field(
            default="",
            description="Optional API key for the upstream server (leave blank if your vLLM server is unsecured)",
        )
        MODEL_NAME: str = Field(
            default="deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
            description="**Exact** model name that vLLM reports (see your vLLM logs)",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.data_prefix = "data: "
        self._think_inserted = False

    async def pipe(
        self,
        body: dict,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
    ) -> AsyncGenerator[str, None]:
        """Forward the prompt to vLLM and stream the reply, adding `<think>` if
        the model forgets to start with it.
        """
        self._think_inserted = False

        # -------------------------- HEADERS ------------------------------------
        req_headers = {"Content-Type": "application/json"}
        key = self.valves.API_KEY.strip()
        if key:
            req_headers["Authorization"] = f"Bearer {key}"

        # --------------------------- BODY --------------------------------------
        request_data = body.copy()
        # Always use the valve‑defined model name, overriding whatever the UI sent
        request_data["model"] = self.valves.MODEL_NAME
        request_data["stream"] = True

        # ----------------------- FORWARD REQUEST -------------------------------
        try:
            async with httpx.AsyncClient(http2=True, timeout=60) as client:
                async with client.stream(
                    "POST",
                    f"{self.valves.API_BASE_URL}/chat/completions",
                    headers=req_headers,
                    json=request_data,
                ) as resp:
                    if resp.status_code != 200:
                        msg = (await resp.aread()).decode()[:200]
                        yield json.dumps(
                            {"error": f"Upstream returned {resp.status_code}: {msg}"}
                        )
                        return

                    async for line in resp.aiter_lines():
                        if line == "data: [DONE]":
                            return
                        if not line.startswith(self.data_prefix):
                            continue

                        fragment = json.loads(line[len(self.data_prefix) :])
                        delta = fragment.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content == "":
                            continue

                        # Insert <think> at the very beginning if absent
                        if not self._think_inserted:
                            stripped = content.lstrip()
                            if not (
                                stripped.startswith("<think>")
                                or stripped.startswith("<thinking>")
                            ):
                                yield "<think>\n"
                            self._think_inserted = True

                        yield content
        except Exception as exc:
            yield json.dumps({"error": f"{type(exc).__name__}: {str(exc)}"})
