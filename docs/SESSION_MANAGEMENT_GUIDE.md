# Developer's Guide to Session Management in Pipelines

This guide provides a comprehensive overview of how to implement session management in your custom pipelines. Proper session management is crucial for maintaining chat history and enabling stateful, multi-turn conversations.

## 1. The `chat_id` Identifier

The key to session tracking in the Pipelines framework is the `chat_id`. This is a unique string that identifies a single conversation thread.

- **Responsibility**: The client application (e.g., Open WebUI) is responsible for generating a `chat_id` for each new conversation and sending it with every subsequent request for that same conversation.
- **Location**: The location of the `chat_id` in the request body is a matter of convention between the client and the pipeline. The framework itself is flexible.

## 2. Implementing Session Management

How you access the `chat_id` depends on whether you are building a **filter** pipeline or a **standard** pipeline.

### For Standard (non-filter) Pipelines

If you have a standard pipeline with a `pipe` method, you can access the `chat_id` directly from the `body` parameter.

**Scenario: Using Open WebUI as the client**

Open WebUI sends the `chat_id` within the `metadata` object of the request body. Here’s how to access it in your `pipe` method:

```python
import uuid

class Pipeline:
    def __init__(self):
        self.type = "pipe"
        self.name = "My Session-Aware Pipeline"
        # A dictionary to store session-specific data
        self.chat_sessions = {}

    def pipe(self, user_message: str, model_id: str, messages: list, body: dict) -> str:
        """
        This method is called for each request.

        Args:
            user_message (str): The last message from the user.
            model_id (str): The ID of the pipeline model.
            messages (list): The entire list of messages in the conversation.
            body (dict): The full request body from the client.
        """
        
        # 1. Extract chat_id from the request body's metadata
        metadata = body.get("metadata", {})
        chat_id = metadata.get("chat_id")

        # 2. Handle new or existing conversations
        if not chat_id:
            chat_id = f"fallback-session-{uuid.uuid4()}"
            print(f"Warning: No chat_id from client. Created a new one: {chat_id}")

        if chat_id not in self.chat_sessions:
            print(f"New conversation detected. ID: {chat_id}")
            # Initialize history or other data for a new chat
            self.chat_sessions[chat_id] = {"history": []}
        else:
            print(f"Continuing conversation. ID: {chat_id}")

        # 3. Use the session data
        self.chat_sessions[chat_id]["history"] = messages
        print(f"History for {chat_id} has {len(self.chat_sessions[chat_id]['history'])} messages.")

        # 4. Your pipeline's core logic
        response = f"You said: '{user_message}'. This is conversation {chat_id}."
        return response
```

### For Filter Pipelines

Filter pipelines use `inlet` and `outlet` methods. The principle is the same: you extract the `chat_id` from the request body.

```python
import uuid
from typing import List, Optional
from pydantic import BaseModel

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = []
        priority: int = 0

    def __init__(self):
        self.type = "filter"
        self.name = "Session Tracking Filter"
        self.valves = self.Valves(pipelines=["*"])
        self.sessions = {}

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        metadata = body.get("metadata", {})
        chat_id = metadata.get("chat_id")

        if not chat_id:
            chat_id = f"session-{uuid.uuid4()}"
        
        # Add chat_id to the top-level of the body for easy access later
        body["chat_id"] = chat_id

        if chat_id not in self.sessions:
            self.sessions[chat_id] = {"history": []}
        
        # Append the latest user message to our history
        for message in body.get("messages", []):
            if message["role"] == "user":
                self.sessions[chat_id]["history"].append(message)

        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        chat_id = body.get("chat_id")

        if chat_id and chat_id in self.sessions:
            # Append the latest assistant message to our history
            for message in body.get("messages", []):
                if message["role"] == "assistant":
                    self.sessions[chat_id]["history"].append(message)
                    break
        return body
```

## 3. Client-Side Responsibility

For session tracking to work, the client must consistently send the `chat_id` for every request in a given conversation.

Here is an example of a JSON payload that a client like Open WebUI would send:

```json
{
  "model": "your_pipeline_model_id",
  "messages": [
    {
      "role": "user",
      "content": "Hello, world!"
    }
  ],
  "metadata": {
    "chat_id": "conversation-12345"
  }
}
```

By following this guide, you can effectively manage sessions in your pipelines, enabling you to build more complex and stateful conversational AI applications.
