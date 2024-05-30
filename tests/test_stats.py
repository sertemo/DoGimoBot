
import pytest
from collections import defaultdict
from unittest.mock import MagicMock
from discord import Message

from dogimobot.stats import BotStats
from dogimobot import settings

# Mock settings for testing
settings.OPENAI_PRICING = {
    "gpt-3.5-turbo": {"in": 0.0001, "out": 0.0002}
}
settings.MODELO = "gpt-3.5-turbo"

def test_initialization(bot_stats: BotStats):
    assert bot_stats.total_queries == 0
    assert bot_stats.total_cost == 0.0
    assert bot_stats.max_cost == 0.0
    assert bot_stats.total_tokens == 0
    assert isinstance(bot_stats.user_stats, defaultdict)

def test_add_total_tokens(bot_stats: BotStats):
    bot_stats.add_total_tokens(100)
    assert bot_stats.total_tokens == 100
    bot_stats.add_total_tokens(200)
    assert bot_stats.total_tokens == 300

def test_add_total_queries(bot_stats: BotStats):
    bot_stats.add_total_queries()
    assert bot_stats.total_queries == 1
    bot_stats.add_total_queries()
    assert bot_stats.total_queries == 2

def test_calculate_total_cost(bot_stats: BotStats):
    in_tokens = 1000
    out_tokens = 2000
    total_cost = bot_stats.calculate_total_cost(in_tokens, out_tokens)
    expected_cost = (in_tokens / 1e6) * 0.0001 + (out_tokens / 1e6) * 0.0002
    assert total_cost == pytest.approx(expected_cost, rel=1e-6)

def test_add_total_and_max_cost(bot_stats: BotStats):
    bot_stats.add_total_and_max_cost(0.001)
    assert bot_stats.total_cost == 0.001
    assert bot_stats.max_cost == 0.001

    bot_stats.add_total_and_max_cost(0.002)
    assert bot_stats.total_cost == 0.003
    assert bot_stats.max_cost == 0.002

    bot_stats.add_total_and_max_cost(0.0015)
    assert pytest.approx(bot_stats.total_cost) == 0.0045
    assert bot_stats.max_cost == 0.002

def test_add_user_stats(bot_stats: BotStats):
    message = MagicMock(spec=Message)
    message.author.name = "test_user"

    bot_stats.add_user_stats(message, 100, 0.001)
    assert bot_stats.user_stats["test_user"]["tokens"] == 100
    assert bot_stats.user_stats["test_user"]["cost"] == 0.001
    assert bot_stats.user_stats["test_user"]["queries"] == 1

    bot_stats.add_user_stats(message, 200, 0.002)
    assert bot_stats.user_stats["test_user"]["tokens"] == 300
    assert bot_stats.user_stats["test_user"]["cost"] == 0.003
    assert bot_stats.user_stats["test_user"]["queries"] == 2
