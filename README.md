# Prepend Think Tag Pipeline

A **2‑minute drop‑in** that makes any OpenAI‑compatible backend (vLLM, Ollama, LM Studio …) work with OpenWebUI’s **“Thinking… ⏳”** animation.

---

## 📂 Install

```bash
mkdir -p ~/.local/share/open-webui/plugins/functions/
cp -r prepend_think_pipeline ~/.local/share/open-webui/plugins/functions/
# (the folder must contain __init__.py with the Pipe class you dropped earlier)
```

Restart OpenWebUI (or click **Settings ▸ Plugins ▸ Reload**).

---

## ⚙️ Configure once

1. **Settings ▸ Models ▸ ➕ Add model** → *OpenAI‑Compatible*
2. **Base URL** → `http://YOUR-VLLM-HOST:8000/v1`
3. **Model name** → whatever you passed to `vllm serve` (e.g. `deepseek-r1-7b-chat`)
4. **Functions & Filters** → tick **Prepend Think Tag Pipeline**
5. *(Optional)* paste an API key if your server enforces one.

Save → Done.

---

## 🚀 Use

Pick the model in chat and send a prompt. If the model forgets to start with `<think>`, the pipe inserts it automatically, so OpenWebUI shows the **Thinking…** placeholder and collapsible chain‑of‑thought.

That’s all - good luck.


