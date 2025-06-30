# Nano-GeminiCLI: Design & Implementation Plan

This document outlines the design and step-by-step plan for creating `nano-gemini-cli`, a minimal, Python-based implementation of the Gemini CLI. The project is inspired by the "nano" series of projects (like `nano-gpt`), focusing on a clean, understandable, and extensible core.

This design incorporates a `core`/`cli` separation, a `NanoGeminiClient` engine, and a feature-rich TUI that mirrors the architecture and user experience of the official Gemini CLI.

## 1. Core Philosophy & Technologies
_(This section remains the same)_

## 2. Proposed Project Structure

The project will be structured as a monorepo with two main packages: `core` and `cli`.

```
nano-gemini-cli/
├── .gitignore
├── pyproject.toml
├── README.md
├── packages/
│   ├── nano_gemini_cli_core/
│   │   ├── __init__.py
│   │   ├── client.py       # The main NanoGeminiClient class
│   │   ├── server.py       # <-- New FastAPI server for conversational API
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── ask_remote_agent.py # <-- New tool for agent-to-agent chat
│   │       # ... etc.
│   │
│   └── nano_gemini_cli/
│       ├── __init__.py
│       └── main.py         # The main TUI application and chat loop
│       └── processors/
│           └── ...
```

## 3. Implementation Steps

### Step 1: Project Setup
_(This section remains the same)_

### Step 2: Implement the `core` Package
_(This section remains the same, but we will add a new method to the client)_

### Step 3: Implement the `cli` Package
_(This section remains the same)_

### Step 4: Advanced Features (Out of Scope for Nano)
_(This section remains the same)_

### Step 5: Agent-to-Agent Conversation via API

To allow two instances of `nano-gemini-cli` to converse, one instance will run as a "server agent," exposing its conversational ability via a simple API. The other "client agent" will use a special tool to send prompts to this API.

#### A. The Server Agent (`core` package)
The `server.py` will use **FastAPI** to expose a single `/chat` endpoint. This endpoint will take a user's prompt, pass it to its own internal `NanoGeminiClient`, and wait for a final text response.

```python
# packages/nano_gemini_cli_core/server.py
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from .client import NanoGeminiClient
import os

app = FastAPI()
# The server has its own instance of the agent client
server_client = NanoGeminiClient(root_dir=os.getcwd())

class ChatRequest(BaseModel):
    prompt: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Receives a prompt and returns the agent's final response."""
    final_response = ""
    # We need a synchronous way to get the full response
    # This requires a new method on our client.
    try:
        final_response = await server_client.get_final_response(request.prompt)
        return {"response": final_response}
    except Exception as e:
        return {"error": str(e)}

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

To support this, we'll add a new method to `NanoGeminiClient`:
```python
# packages/nano_gemini_cli_core/client.py (New Method)
class NanoGeminiClient:
    # ... (existing methods) ...
    async def get_final_response(self, prompt: str) -> str:
        """Runs a full turn and returns only the final text response."""
        current_input = self.history + [{"role": "user", "content": prompt}]
        
        # Use the non-streaming runner for a single result
        run_result = await Runner.run(self.agent, current_input)
        
        if run_result.final_output:
            # Update history for the next conversation with this server
            self.history = run_result.to_input_list()
            return run_result.final_output
        
        return "Error: Agent did not produce a final output."
```

#### B. The Client Agent's New Tool
The "client agent" uses a new tool, `ask_remote_agent`, to communicate with the server.

```python
# packages/nano_gemini_cli_core/tools/ask_remote_agent.py
from openai_agents import function_tool
import requests

@function_tool
def ask_remote_agent(agent_url: str, prompt: str) -> str:
    """
    Sends a prompt to another nano-gemini-cli agent running as a server and returns its response.

    Args:
        agent_url: The base URL of the remote agent server (e.g., http://localhost:8000).
        prompt: The natural language prompt to send to the remote agent.
    """
    try:
        response = requests.post(f"{agent_url}/chat", json={"prompt": prompt})
        response.raise_for_status()
        data = response.json()
        return data.get("response", f"Error from remote agent: {data.get('error', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        return f"Error communicating with remote agent: {e}"
```

### Step 6: Key Design Principles (Revisited)

- **Conversational API:** Agents communicate via natural language prompts and responses, not by calling each other's tools directly.
- **Stateful Server Agent:** The server instance maintains its own conversational history, allowing for follow-up questions from the client agent.
- **Simple Client Tool:** The client agent only needs a single, simple tool (`ask_remote_agent`) to enable this powerful interaction.
- **Clear API:** The `cli` interacts with the `core` through a single, clean method: `client.send_message_stream()`.
