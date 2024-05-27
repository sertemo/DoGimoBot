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

from collections import deque
import time

from openai import OpenAI
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from dogimobot.main import MyClient

# Mock settings to use in tests
class MockSettings:
    MEMORY_SIZE = 10
    MODELO = "gpt-3.5-turbo"
    CHAT_COMMAND = "!chat"
    INFO_COMMAND = "!info"
    HELP_COMMAND = "!help"
    SYSTEM_PROMPT = "Test system prompt."
    DEFAULT_ERR_ANSWER = "Sorry, something went wrong."
    BOT_NAME = "Dogimo"
    USERS = {"testuser": "Test User"}
    OPENAI_PRICING = {
        "gpt-3.5-turbo": {
            "in": 0.0001,
            "out": 0.0002,
        }
    }

@pytest.fixture(scope="session")
def mock_settings():
    with patch("dogimobot.main.settings", new=MockSettings):
        yield

@pytest.fixture(scope="session")
def mock_openai():
    with patch("dogimobot.main.OpenAI", new=AsyncMock) as mock:
        yield mock

@pytest.fixture(scope="session")
def client(mock_settings, mock_openai):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    client = MyClient(intents=intents)
    client.client_openai = AsyncMock(spec=OpenAI)
    client.session_id = "test_session_id"
    client.memory = deque(maxlen=MockSettings.MEMORY_SIZE)
    client.model = MockSettings.MODELO
    client.total_cost = 0.0
    client.max_cost = 0.0
    client.total_tokens = 0
    client.session_start = time.perf_counter()
    return client
