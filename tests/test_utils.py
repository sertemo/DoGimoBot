
import os
from unittest.mock import patch, mock_open

import pytest

from dogimobot.utils import get_project_version, get_openai_key

def test_get_project_version_success():
    mock_toml_content = """
    [tool.poetry]
    version = "1.2.0"
    """
    with patch("builtins.open", mock_open(read_data=mock_toml_content)):
        with patch("toml.load", return_value={"tool": {"poetry": {"version": "1.2.0"}}}):
            assert get_project_version() == "1.2.0"

def test_get_project_version_missing_key():
    mock_toml_content = """
    [tool.poetry]
    """
    with patch("builtins.open", mock_open(read_data=mock_toml_content)):
        with patch("toml.load", return_value={"tool": {"poetry": {}}}):
            with pytest.raises(KeyError):
                get_project_version()

def test_get_project_version_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            get_project_version()

def test_get_openai_key_success():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        assert get_openai_key() == "test_key"

def test_get_openai_key_failure():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="La API key de OpenAI no está configurada en las variables de entorno"):
            get_openai_key()