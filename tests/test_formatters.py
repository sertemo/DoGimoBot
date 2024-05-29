import pytest
from pathlib import Path
from string import Template
from unittest.mock import patch
from dogimobot.formatters import format_stats, format_help
from dogimobot.exceptions import FormatterException

# Simular USERS para los tests
USERS = {
    "user1": "User One",
    "user2": "User Two",
    "user3": "User Three",
}

@pytest.fixture
def sample_template():
    return Path("sample_template.md")

@pytest.fixture
def sample_help_template():
    return Path("sample_help_template.md")

def test_format_stats(sample_template):
    template_content = (
        "Session ID: $session_id\n"
        "Elapsed Time: $elapsed_hours:$elapsed_minutes:$elapsed_seconds\n"
        "Total Tokens: $total_tokens\n"
        "Total Queries: $total_queries\n"
        "Total Cost: $total_cost\n"
        "User Stats:\n"
        "$user_stats\n"
        "Max Cost: $max_cost\n"
        "Session Start Time: $session_start_time\n"
    )

    with patch("pathlib.Path.read_text", return_value=template_content):
        with patch("dogimobot.formatters.USERS", USERS):
            formatted = format_stats(
                template=sample_template,
                session_id="12345",
                elapsed_hours=1,
                elapsed_minutes=2,
                elapsed_seconds=3,
                total_tokens=456,
                total_queries=7,
                total_cost=89.01,
                user_stats={
                    "user1": {"tokens": 100, "cost": 1.23, "queries": 2},
                    "user2": {"tokens": 200, "cost": 2.34, "queries": 3},
                },
                max_cost=3.45,
                session_start_time="2023-01-01 00:00:00"
            )

            expected_output = (
                "Session ID: 12345\n"
                "Elapsed Time: 01:02:03\n"
                "Total Tokens: 456\n"
                "Total Queries: 7\n"
                "Total Cost: 89.01\n"
                "User Stats:\n"
                "```\n"
                "| Usuario         | Tokens Consumidos    | Coste ($)  | Peticiones |\n"
                "| --------------- | -------------------- | ---------- | ---------- |\n"
                "| User One        | 100                  | 1.2300     | 2          | \n"
                "| User Two        | 200                  | 2.3400     | 3          | \n"
                "```\n"
                "Max Cost: 3.45\n"
                "Session Start Time: 2023-01-01 00:00:00\n"
            )

            assert formatted == expected_output

def test_format_help(sample_help_template):
    template_content = (
        "# Comandos\n"
        "## Chatear con el bot\n"
        "```\n"
        "$chat_command <mensaje>\n"
        "```\n"
        "Manda una pregunta a openAI y el bot te contesta\n"
        "## Información de sesión\n"
        "```\n"
        "$stats_command\n"
        "```\n"
        "Da información de la sesión como el coste total y los tokens utilizados\n"
        "## Comandos disponibles\n"
        "```\n"
        "$help_command\n"
        "```\n"
        "Devuelve los comandos disponibles\n"
    )

    with patch("pathlib.Path.read_text", return_value=template_content):
        formatted = format_help(
            template=sample_help_template,
            chat_command="!chat",
            stats_command="!stats",
            help_command="!help"
        )

        expected_output = (
            "# Comandos\n"
            "## Chatear con el bot\n"
            "```\n"
            "!chat <mensaje>\n"
            "```\n"
            "Manda una pregunta a openAI y el bot te contesta\n"
            "## Información de sesión\n"
            "```\n"
            "!stats\n"
            "```\n"
            "Da información de la sesión como el coste total y los tokens utilizados\n"
            "## Comandos disponibles\n"
            "```\n"
            "!help\n"
            "```\n"
            "Devuelve los comandos disponibles\n"
        )

        assert formatted == expected_output

def test_format_stats_raises_exception(sample_template):
    with patch("pathlib.Path.read_text", side_effect=Exception("File read error")), \
        pytest.raises(FormatterException, match="Se ha producido un problema al formatear"):
        format_stats(
            template=sample_template,
            session_id="12345",
            elapsed_hours=1,
            elapsed_minutes=2,
            elapsed_seconds=3,
            total_tokens=456,
            total_queries=7,
            total_cost=89.01,
            user_stats={
                "user1": {"tokens": 100, "cost": 1.23, "queries": 2},
                "user2": {"tokens": 200, "cost": 2.34, "queries": 3},
            },
            max_cost=3.45,
            session_start_time="2023-01-01 00:00:00"
        )

def test_format_help_raises_exception(sample_help_template):
    with patch("pathlib.Path.read_text", side_effect=Exception("File read error")), \
        pytest.raises(FormatterException, match="Se ha producido un problema al formatear"):
        format_help(
            template=sample_help_template,
            chat_command="!chat",
            stats_command="!stats",
            help_command="!help"
        )

