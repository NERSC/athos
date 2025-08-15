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
