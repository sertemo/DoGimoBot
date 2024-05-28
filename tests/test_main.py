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

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from discord import Message
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)

from dogimobot import settings
from dogimobot.main import DiscordClient, OpenAIMessageType



def test_remove_command_from_msg(client: DiscordClient):
    message = MagicMock(spec=Message)
    message.content = "!chat test message"
    result = client._remove_command_from_msg(message)
    assert result == "test message"

def test_save_in_memory(client: DiscordClient):
    message = MagicMock(spec=Message)
    message.content = "!chat test message"
    message.author.name = "testuser"
    client._save_in_memory(message)
    assert len(client.memory) == 1
    assert client.memory[0]['role'] == 'user'
    assert client.memory[0]['content'] == 'test message'
    assert client.memory[0]['author'] == 'testuser'

def test_get_context(client: DiscordClient):
    message = MagicMock(spec=Message)
    message.content = "!chat test message"
    message.author.name = "testuser"
    client._save_in_memory(message)
    context = client._get_context()
    print(context)
    print(client.memory)
    assert len(context) == 2  # System prompt + 1 message
    assert context[0]['role'] == 'system'
    assert context[1]['role'] == 'user'
    assert 'testuser dijo: test message' in context[1]['content']

@pytest.mark.asyncio
async def test_get_response_from_openai(client: DiscordClient):
    message = MagicMock(spec=Message)
    message.content = "!dog test message"
    context = client._get_context()

    # Ensure the OpenAI client's chat.completions.create method is patched
    client.client_openai.chat = MagicMock()
    client.client_openai.chat.completions.create = AsyncMock(return_value=MagicMock(spec=ChatCompletion))

    response = await client._get_response_from_openai(message, context)
    client.client_openai.chat.completions.create.assert_called_once()
    assert response

def test_calculate_total_cost(client: DiscordClient):
    in_tokens = 1000
    out_tokens = 2000

    with patch('dogimobot.settings.OPENAI_PRICING', {
        "gpt-3.5-turbo": {
            "in": 0.0001,
            "out": 0.0002,
        }
    }):
        with patch('dogimobot.settings.MODELO', "gpt-3.5-turbo"):
            total_cost = client.bot_stats.calculate_total_cost(in_tokens, out_tokens)
            expected_cost = (in_tokens / 1e6) * 0.0001 + (out_tokens / 1e6) * 0.0002
            assert total_cost == pytest.approx(expected_cost, rel=1e-6)

def test_get_tokens_from_response(client: DiscordClient):
    mock_response = MagicMock(spec=ChatCompletion)
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    in_tokens, out_tokens = client._get_tokens_from_response(mock_response)
    assert in_tokens == 10
    assert out_tokens == 20

