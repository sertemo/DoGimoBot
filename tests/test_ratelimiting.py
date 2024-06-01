import pytest
from unittest.mock import MagicMock, patch
from collections import defaultdict
from datetime import datetime, timedelta

from discord import Message
from icecream import ic
from openai.types.chat.chat_completion import ChatCompletion, Choice

from openai.types.chat.chat_completion_message import ChatCompletionMessage

from dogimobot.main import DiscordClient
from dogimobot import settings
from dogimobot.rate_limiting import RateLimiter, default_response

# Decorador para la función de ejemplo
@RateLimiter.limit()
def example_get_response(self: DiscordClient, message: Message, context: list) -> ChatCompletion:
    # Esta función solo es un ejemplo
    return ChatCompletion(
        id="test",
        object="chat.completion",
        created=1677652288,
        model=settings.MODELO,
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=(
                        "No tan rápido, "
                        "Has excedido el límite de mensajes por minuto"
                        )
                    ),
                logprobs=None,
                finish_reason="stop",
            ),
        ])


def test_rate_limit_not_exceeded(client, mock_message, reset_rate_limiter):
    response: ChatCompletion = example_get_response(client, message=mock_message, context=[])
    assert response.id == "test"
    assert RateLimiter.track[mock_message.author.name]["num_peticiones"] == 1

def test_rate_limit_exceeded(client, mock_message, reset_rate_limiter):
    RateLimiter.track["Test User"] = {"num_peticiones": settings.MAX_MSG_PER_MINUTES + 1, "start": datetime.now()}
    response: ChatCompletion = example_get_response(client, message=mock_message, context=[])
    assert response.choices[0].message.content.startswith("No tan rápido,")
    assert "Has excedido el límite de mensajes por minuto" in response.choices[0].message.content

def test_rate_limit_reset(client, mock_message, reset_rate_limiter):
    RateLimiter.track[mock_message.author.name] = {"num_peticiones": settings.MAX_MSG_PER_MINUTES, "start": datetime.now() - timedelta(seconds=settings.RATE_LIMIT + 1)}
    response: ChatCompletion = example_get_response(client, message=mock_message, context=[])
    assert response.id == "test"
    assert RateLimiter.track[mock_message.author.name]["num_peticiones"] == 1

def test_rate_limit_multiple_users(client, reset_rate_limiter):
    user1 = "user1"
    user2 = "user2"
    msg1 = MagicMock(spec=Message)
    msg1.author.name = user1
    msg1.content = "message from user1"
    msg2 = MagicMock(spec=Message)
    msg2.author.name = user2
    msg2.content = "message from user2"
    response1: ChatCompletion = example_get_response(client, message=msg1, context=[])
    response2: ChatCompletion = example_get_response(client, message=msg2, context=[])
    assert response1.id == "test"
    assert response2.id == "test"
    assert RateLimiter.track[user1]["num_peticiones"] == 1
    assert RateLimiter.track[user2]["num_peticiones"] == 1