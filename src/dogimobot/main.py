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
from datetime import datetime
import time
from typing import Deque, Union
import uuid

import discord
from discord import Message
from icecream import ic
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
from dogimobot.exceptions import FormatterException
from dogimobot.formatters import format_stats, format_help
from dogimobot.logging_config import logger
from dogimobot.stats import BotStats
from dogimobot.utils import get_discord_key, get_openai_key, get_project_version

OpenAIMessageType = Union[
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
]


class DiscordClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory: Deque[dict[str, str]] = deque(maxlen=settings.MEMORY_SIZE)
        self.model: str = settings.MODELO
        self.client_openai: OpenAI = OpenAI(api_key=get_openai_key())
        self.session_id: str = f"{uuid.uuid4()}"
        # Inicializamos estadísticas
        self.bot_stats: BotStats = BotStats()
        # Iniciamos contar de sesión
        self.session_start: float = time.perf_counter()
        self.session_start_date: str = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
        # Validamos que el modelo sea válido
        self._validate_model()

    def _validate_model(self) -> None:
        """Valida si el modelo especificado en settings
        corresponde con la lista de modelos válidos
        de Pricing, también en settings.
        """
        if settings.MODELO not in settings.OPENAI_PRICING:
            msg = f"El modelo escogido no es válido. Modelos válidos: {', '.join(settings.OPENAI_PRICING.keys())}"
            logger.error(f"SESSION ID: {self.session_id} | {msg}")
            raise ValueError(msg)

    def _remove_command_from_msg(self, message: Message) -> str:
        """Quita del mensaje el comando del principio

        Parameters
        ----------
        message : Message
            _description_

        Returns
        -------
        str
            _description_
        """
        mensaje: str = message.content.replace(settings.CHAT_COMMAND, "").strip()
        return mensaje

    def _save_in_memory(self, message: Message) -> None:
        """Guarda un dict en memoria para

        Parameters
        ----------
        message : Message
            _description_
        """
        mensaje = self._remove_command_from_msg(message)
        self.memory.append(
            {
                "role": (
                    "user" if message.author.name in settings.USERS else "assistant"
                ),
                "content": mensaje,
                "author": str(message.author.name),
            }
        )

    def _get_context(self) -> list[ChatCompletionMessageParam]:
        """Devuelve una lista con el formato
        apropiado para enviar a openai.
        Esta lista consta de los mensajes anteriores
        y del system prompt en el formato "role" y "content".

        En el content se añade quien dijo el mensaje para que
        el chatbot sepa identificarlo.

        Returns
        -------
        list[dict[str, Any]]
            _description_
        """
        context: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system", content=settings.SYSTEM_PROMPT
            )
        ]
        for msg in self.memory:
            if msg["role"] == "assistant":
                context.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant",
                        content=f"{msg['author']} dijo: {msg['content']}",
                    )
                )
            else:
                context.append(
                    ChatCompletionUserMessageParam(
                        role="user", content=f"{msg['author']} dijo: {msg['content']}"
                    )
                )
        return context

    def _get_response_from_openai(
        self, message: Message, context: list[ChatCompletionMessageParam]
    ) -> ChatCompletion:
        """Realiza la query a la API de openAI
        y devuelve la respuesta

        Returns
        -------
        ChatCompletion
            _description_
        """
        response: ChatCompletion = self.client_openai.chat.completions.create(
            model=self.model,
            messages=context
            + [
                ChatCompletionUserMessageParam(
                    role="user",
                    content=self._remove_command_from_msg(message),
                )
            ],
        )
        return response

    def _get_reply_from_openai(self, response: ChatCompletion) -> str:
        """Devuelve el contenido de la respuesta
        de openAI. Si lo que devuelve openAI
        es None, la respuesta será una contestación
        por defecto parametrizada en settings

        Parameters
        ----------
        response : ChatCompletion
            _description_

        Returns
        -------
        str
            _description_
        """
        response_content = (
            response.choices[0].message.content
            if response and response.choices
            else None
        )
        reply: str = (
            response_content.strip()
            if response_content
            else settings.DEFAULT_ERR_ANSWER
        )
        return reply

    def _get_tokens_from_response(self, response: ChatCompletion) -> tuple[int, int]:
        """Devuelve el número

        Parameters
        ----------
        response : ChatCompletion
            _description_

        Returns
        -------
        tuple[int, int]
            Devuelve prompt_tokens y completion_tokens
        """
        prompt_tokens = completion_tokens = 0

        if response.usage is not None:
            prompt_tokens = int(response.usage.prompt_tokens)
            completion_tokens = int(response.usage.completion_tokens)

        return prompt_tokens, completion_tokens

    async def on_ready(self):
        logger.info(f"********* SESSION ID {self.session_id} *********")
        ic(f"Logged on as {self.user}")

    async def on_message(self, message: Message):
        # No respondas a ti mismo o a otros bots
        if message.author == self.user or message.author.bot:
            return

        # Inicializamos reply para evitar errores
        reply = ""

        # Guarda el mensaje en la memoria
        self._save_in_memory(message)

        # Logging
        logger.info(
            f"SESSION STARTED\nSESSION ID: {self.session_id} | {message.author} dijo: {message.content}"
        )

        # Si el mensaje contiene el comando, responde
        if message.content.lower().startswith(settings.CHAT_COMMAND):

            # Prepara el contexto incluyendo las últimas interacciones
            context = self._get_context()

            try:
                response = self._get_response_from_openai(
                    message=message, context=context
                )
            except Exception as exc:
                print(f"Se ha producido un error: {exc}")
                return

            reply = self._get_reply_from_openai(response)
            # Sacamos los in y out tokens
            in_tokens, out_tokens = self._get_tokens_from_response(response)
            total_tokens = in_tokens + out_tokens

            # Sumamos los tokens totales a la sesión
            self.bot_stats.add_total_tokens(total_tokens)
            # Añadimos 1 a las queries totales
            self.bot_stats.add_total_queries()

            # Calculamos el coste total
            total_cost: float = self.bot_stats.calculate_total_cost(
                in_tokens, out_tokens
            )

            # Sumamos al coste total de la sesión
            self.bot_stats.add_total_and_max_cost(total_cost)

            # Alimentamos las estadísticas
            self.bot_stats.add_user_stats(message, total_tokens, total_cost)

            # Añadimos la respuesta a memoria
            self.memory.append(
                {"role": "assistant", "content": reply, "author": settings.BOT_NAME}
            )

            # Añadimos respuesta de openAI junto con costes al logging
            log_msg = (
                f"SESSION ID: {self.session_id} | "
                f"{settings.BOT_NAME} dijo: {reply} | "
                f"Tokens totales: {total_tokens} | "
                f"Coste total: {total_cost}"
            )
            logger.info(log_msg)

        elif message.content.lower().startswith(settings.INFO_COMMAND):
            elapsed_time = time.perf_counter() - self.session_start
            days, remainder = divmod(elapsed_time, 86400)  # 86400 segundos en un día
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)

            try:
                reply = format_stats(
                    template=settings.STATS_REPLY_TEMPLATE,
                    session_id=self.session_id,
                    version=get_project_version(),
                    model=self.model,
                    elapsed_days=int(days),
                    elapsed_hours=int(hours),
                    elapsed_minutes=int(minutes),
                    elapsed_seconds=int(seconds),
                    total_tokens=self.bot_stats.total_tokens,
                    total_queries=self.bot_stats.total_queries,
                    total_cost=round(self.bot_stats.total_cost, 4),
                    user_stats=self.bot_stats.user_stats,
                    max_cost=round(self.bot_stats.max_cost, 4),
                    session_start_time=self.session_start_date,
                )
            except FormatterException as fexc:
                reply = f"Se ha producido un error al formatear {fexc}"
                logger.error(reply)
                print(reply)

            except Exception as exc:
                reply = f"Se ha producido un error {exc}"
                logger.error(reply)
                print(reply)

        elif message.content.lower().startswith(settings.HELP_COMMAND):
            reply = format_help(
                settings.HELP_REPLY_TEMPLATE,
                chat_command=settings.CHAT_COMMAND,
                stats_command=settings.INFO_COMMAND,
                help_command=settings.HELP_COMMAND,
            )

        await message.channel.send(reply)


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    client = DiscordClient(intents=intents)
    client.run(get_discord_key())
