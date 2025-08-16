"""Utilities for running Athos demos in Jupyter notebooks."""

from __future__ import annotations

import os
import sys
from typing import Tuple

from smolagents import GradioUI


def add_conda_bin_to_path() -> str:
    """Add the current conda environment's ``bin`` directory to ``PATH``.

    Returns
    -------
    str
        The bin directory that was added.
    """

    bin_dir = os.path.join(sys.prefix, "bin")
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    return bin_dir


def get_jupyter_proxy_url(port: int) -> Tuple[str, str]:
    """Compute proxy URL and root path for accessing a Gradio server.

    Parameters
    ----------
    port:
        The port on which the Gradio server will listen.

    Returns
    -------
    tuple[str, str]
        A tuple of ``(proxy_url, root_path)`` suitable for passing to
        :class:`~smolagents.GradioUI`.
    """

    service_prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "/")
    root_path = f"{service_prefix}proxy/{port}/"
    proxy_url = f"https://jupyter.nersc.gov{root_path}"
    return proxy_url, root_path


def launch_gradio_ui(agent, port: int = 8989) -> None:
    """Launch a ``smolagents`` :class:`GradioUI` for the given agent.

    The Gradio server will be exposed via the Jupyter proxy and a helpful
    message will be printed with the URL.
    """

    proxy_url, root_path = get_jupyter_proxy_url(port)
    print(f"Access your Gradio app at: {proxy_url}")
    GradioUI(agent).launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        root_path=root_path,
        inline=False,
    )

import gradio as gr
from smolagents import stream_to_gradio

def launch_custom_ui(agent, port: int = 8989):
    proxy_url, root_path = get_jupyter_proxy_url(port)
    print(f"Access your Gradio app at: {proxy_url}")

    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("### 🚀 My SmolAgents Console")
        chat = gr.Chatbot(height=420, type="messages", label="Chat")
        user = gr.Textbox(placeholder="Ask the agent…", lines=3)
        run = gr.Button("Run", variant="primary")
        reset_mem = gr.Checkbox(label="Reset agent memory", value=False)
        files = gr.File(file_count="multiple", file_types=[".txt", ".pdf", ".docx"], label="Add files")

        def on_run(prompt, history, reset_flag, files_list):
            # Ensure history is a list of ChatMessage
            history = history or []

            # Wrap smolagents stream so we always yield the full list
            for chunk in stream_to_gradio(
                agent,
                task=prompt,
                task_images=None,
                reset_agent_memory=bool(reset_flag),
                additional_args={"uploaded_files": files_list or []},
            ):
                # Normalize chunk into a ChatMessage, then append & yield the whole history
                if isinstance(chunk, gr.ChatMessage):
                    history.append(chunk)
                elif isinstance(chunk, dict) and "role" in chunk and "content" in chunk:
                    history.append(gr.ChatMessage(**chunk))
                else:
                    # Fallback: treat as assistant text
                    history.append(gr.ChatMessage(role="assistant", content=str(chunk)))
                yield history

        run.click(on_run, inputs=[user, chat, reset_mem, files], outputs=[chat])

    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        root_path=root_path,
        inline=False,
    )