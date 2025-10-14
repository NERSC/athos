import os
from unittest.mock import MagicMock, patch

from athos.utils.notebook_utils import (
    add_conda_bin_to_path,
    get_jupyter_proxy_url,
    launch_gradio_ui,
)


def test_add_conda_bin_to_path(monkeypatch):
    monkeypatch.setenv("PATH", "orig")
    bin_dir = add_conda_bin_to_path()
    assert os.environ["PATH"].startswith(bin_dir + os.pathsep)


def test_get_jupyter_proxy_url(monkeypatch):
    monkeypatch.setenv("JUPYTERHUB_SERVICE_PREFIX", "/user/test/")
    proxy_url, root_path = get_jupyter_proxy_url(1234)
    assert proxy_url == "https://jupyter.nersc.gov/user/test/proxy/1234/"
    assert root_path == "/user/test/proxy/1234/"


def test_launch_gradio_ui(monkeypatch):
    monkeypatch.setenv("JUPYTERHUB_SERVICE_PREFIX", "/user/test/")
    dummy_agent = MagicMock()
    with patch("athos.utils.notebook_utils.GradioUI") as MockUI:
        ui_instance = MockUI.return_value
        launch_gradio_ui(dummy_agent, port=1234)
        MockUI.assert_called_once_with(dummy_agent)
        ui_instance.launch.assert_called_once_with(
            server_name="0.0.0.0",
            server_port=1234,
            share=False,
            root_path="/user/test/proxy/1234/",
            inline=False,
        )
