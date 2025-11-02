# Streaming updates for langchain/langgraph flows

Here’s a compact migration guide to move from `astream_events` to `astream` (with `stream_mode`) while keeping your **Open WebUI Pipelines** + **OpenAI-compatible server** setup.

# 1) What to upgrade/confirm

* **LangGraph/LangChain**: use a recent version that supports `stream_mode` on `stream/astream`.
* **Your graph**: still a `CompiledStateGraph` (Runnable). No graph changes needed.
* **Server**: continues to expose `POST /v1/chat/completions` and stream SSE frames in OpenAI format.

# 2) Core change (events → modes)

Replace:

```python
async for ev in graph.astream_events(inputs, version="v2"):
    ...
```

with:

```python
modes = ["messages","updates","custom"]  # start with messages; add others as needed
async for mode, payload in graph.astream(inputs, stream_mode=modes):
    ...
```

# 3) Mapping to Open WebUI (OpenAI-compatible SSE)

**A) Text streaming (required)**

```python
if mode == "messages":
    token, meta = payload  # token is a string (or text fragment)
    yield f'data: {{"choices":[{{"delta":{{"content":{token!r}}}}]}}}\n\n'
```

This keeps the normal typing UI working.

**B) Agent/tool status (optional but recommended)**
Use `"updates"` to emit step-level snapshots (e.g., model step, tool result).

```python
elif mode == "updates":
    # Forward as side-channel event for your Pipeline (same shape you used before, if you had one):
    yield f'data: {{"event":"agent_update","data":{json.dumps(payload)}}}\n\n'
```

**C) Arbitrary progress (optional)**
Use `"custom"` (from `get_stream_writer()` inside tools) for long-running work.

```python
elif mode == "custom":
    yield f'data: {{"event":"agent_custom","data":{json.dumps(payload)}}}\n\n'
```

Finish the stream:

```python
yield "data: [DONE]\n\n"
```

> If your Pipeline doesn’t currently route custom `"event"` frames, you can either (1) keep them as no-ops, or (2) adapt your Pipeline’s server-side “pipe” to catch and surface them (e.g., status chips, timeline).

# 4) Input/Output contract (no change for Open WebUI)

* **Input**: keep accepting OpenAI-style payloads:

  * `model`, `messages`, optional `tools`, etc.
* **Output**: continue streaming `choices[].delta.content` frames.
* **Final message**: either a final `delta` with remaining text or just terminate with `[DONE]`. (Open WebUI handles both patterns.)

# 5) Practical defaults

* Start with: `stream_mode="messages"` for 1:1 parity with your current chat typing UX.
* Add: `["messages","updates"]` to show step/status cards.
* Add `"custom"` only if your tools report granular progress.

# 6) Backward-compat shims (if you previously relied on events)

* **Node/tool boundaries**: `updates` gives step snapshots; if you still need strict start/end, keep a **debug endpoint** that uses `astream_events` for tracing.
* **Volume control**: throttle/aggregate `"updates"` and `"custom"` to avoid spamming the SSE stream.

# 7) Error handling & timeouts

* Wrap the async generator; on exceptions, emit a final SSE with an error “event” (non-critical) and then `[DONE]`.
* Ensure graceful cancellation: if client disconnects, stop the `astream` loop.

# 8) Observability (drop-in)

* Record per-request timings around `astream`; optional counters for:

  * tokens sent, tools invoked, steps completed, cancellations.
* If you used event logs for metrics, mirror the key counters from `updates`.

# 9) Minimal FastAPI endpoint (sketch)

```python
@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    body = await req.json()
    user_msgs = body.get("messages", [])
    modes = os.getenv("STREAM_MODES", "messages").split(",")
    inputs = {"messages": user_msgs}

    async def gen():
        try:
            async for mode, payload in graph.astream(inputs, stream_mode=modes):
                if mode == "messages":
                    token, _meta = payload
                    yield f'data: {{"choices":[{{"delta":{{"content":{token!r}}}}]}}}\n\n'
                elif mode == "updates":
                    yield f'data: {{"event":"agent_update","data":{json.dumps(payload)}}}\n\n'
                elif mode == "custom":
                    yield f'data: {{"event":"agent_custom","data":{json.dumps(payload)}}}\n\n'
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
```

# 10) Migration checklist

* [ ] Bump LangChain/LangGraph to a version with `stream_mode`.
* [ ] Swap `astream_events` → `astream(stream_mode=...)`.
* [ ] Keep OpenAI SSE deltas for `"messages"`.
* [ ] (Optional) Pipe `"updates"`/`"custom"` as side-channel events; adjust Pipeline to display them.
* [ ] Add env toggle (e.g., `STREAM_MODES=messages,updates`).
* [ ] Test: plain chat, single tool call, long-running tool, cancellation, error paths.

That’s it—you’ll keep your OpenAI-compatible surface for Open WebUI, gain a cleaner public API, and still have a path to rich agent UX without the heavier lifecycle event stream.

