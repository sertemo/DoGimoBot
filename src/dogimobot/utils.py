# Copyright 2024 Sergio Tejedor Moreno

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import Any

from dotenv import load_dotenv
import toml

load_dotenv()


def get_project_version() -> str:
    """Devuelve la versión del proyecto
    extraido del pyproject.toml"""
    with open("pyproject.toml", "r") as file:
        data: dict[str, Any] = toml.load(file)
        version: str = data["tool"]["poetry"]["version"]
    return version


def get_openai_key() -> str:
    """Devuelve la API KEY de openAI

    Returns
    -------
    str
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY is None:
        raise ValueError(
            "La API key de OpenAI no está configurada en las variables de entorno"
        )
    return OPENAI_API_KEY


def get_discord_key() -> str:
    """Devuelve el token del bot

    Returns
    -------
    str
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    if DISCORD_TOKEN is None:
        raise ValueError(
            "El token de Discord no está configurado en las variables de entorno"
        )
    return DISCORD_TOKEN
