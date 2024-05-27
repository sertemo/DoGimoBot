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
from textwrap import dedent
import time
from typing import Deque, Union, Dict
import uuid

import discord
from discord import Message
from icecream import ic
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

from dogimobot import settings
from dogimobot.logging_config import logger
from dogimobot.utils import get_discord_key, get_openai_key


MessageType = Union[Dict[str, str], Dict[str, Union[str, Dict[str, str]]]]


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory: Deque[MessageType] = deque(maxlen=settings.MEMORY_SIZE)
        self.model: str = settings.MODELO
        self.session_id: str = f"{uuid.uuid4()}"
        self.total_cost = 0.0
        self.max_cost: float = 0.0
        self.total_tokens: int = 0
        # Iniciamos contar de sesión
        self.session_start: float = time.perf_counter()
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
        return message.content.replace(settings.CHAT_COMMAND, "").strip()

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
                "author": str(message.author),
            }
        )

    def _get_context(self) -> list[MessageType]:
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
        context: list[MessageType] = [
            {"role": "system", "content": settings.SYSTEM_PROMPT}
        ] + [
            {
                "role": msg["role"],
                "content": f"{msg['author']} dijo: {msg['content']}",
            }
            for msg in self.memory
        ]
        return context

    def _get_response_from_openai(
        self, message: Message, context: list[MessageType]
    ) -> ChatCompletion:
        """Realiza la query a la API de openAI
        y devuelve la respuesta

        Returns
        -------
        ChatCompletion
            _description_
        """
        response: ChatCompletion = client_openai.chat.completions.create(
            model=self.model,
            messages=context
            + [
                {
                    "role": "user",
                    "content": self._remove_command_from_msg(message),
                }
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
        prompt_tokens = int(response.usage.prompt_tokens)
        completion_tokens = int(response.usage.completion_tokens)

        return prompt_tokens, completion_tokens

    def _add_total_tokens(self, total_tokens: int) -> None:
        """Suma a total_tokens los tokens de la query
        para llevar un registro

        Parameters
        ----------
        total_tokens : int
            _description_
        """
        self.total_tokens += total_tokens

    def _calculate_total_cost(self, in_tokens: int, out_tokens: int) -> float:
        """Devuelve el coste total en función
        de los tokens in y out y el modelo
        escogido

        Parameters
        ----------
        in_tokens : int
            _description_
        out_tokens : int
            _description_

        Returns
        -------
        float
            _description_
        """
        in_cost: float = (in_tokens / 1e6) * settings.OPENAI_PRICING[self.model]["in"]
        out_cost: float = (out_tokens / 1e6) * settings.OPENAI_PRICING[self.model][
            "out"
        ]

        return in_cost + out_cost

    def _add_total_cost(self, total_cost: float) -> None:
        """Suma a la sesión el coste de la query

        Parameters
        ----------
        total_cost : float
            _description_
        """

        self.total_cost += total_cost

    async def on_ready(self):
        logger.info(f"********* SESSION ID {self.session_id} *********")
        ic(f"Logged on as {self.user}")

    async def on_message(self, message: Message):
        # No respondas a ti mismo o a otros bots
        if message.author == self.user or message.author.bot:
            return

        # Guarda el mensaje en la memoria
        self._save_in_memory(message)

        # Logging
        logger.info(
            f"SESSION ID: {self.session_id} | {message.author} dijo: {message.content}"
        )

        # Si el mensaje contiene el comando, responde
        if message.content.startswith(settings.CHAT_COMMAND):

            # Prepara el contexto incluyendo las últimas interacciones
            context = self._get_context()

            try:
                response = self._get_response_from_openai(
                    message=message, context=context
                )
            except Exception as exc:
                print(f"Se ha producido un error: {exc}")
                return

            reply: str = self._get_reply_from_openai(response)
            # Sacamos los in y out tokens
            in_tokens, out_tokens = self._get_tokens_from_response(response)
            total_tokens = in_tokens + out_tokens
            # Sumamos los tokens totales a la sesión
            self._add_total_tokens(total_tokens)

            # Calculamos el coste total
            total_cost: float = self._calculate_total_cost(in_tokens, out_tokens)
            # Actualizamos el coste maximo
            self.max_cost = max(self.max_cost, total_cost)
            # Sumamos al coste total de la sesión
            self._add_total_cost(total_cost)

            # Añadimos la respuesta a memoria
            self.memory.append(
                {"role": "assistant", "content": reply, "author": settings.BOT_NAME}
            )

            # Añadimos respuesta de openAI junto con costes al logging
            logger.info(
                f"SESSION ID: {self.session_id} \
                        | {settings.BOT_NAME} dijo: {reply} \
                            | Tokens totales: {total_tokens} \
                                | Coste total: {total_cost}"
            )

            await message.channel.send(reply)

        elif message.content.startswith(settings.INFO_COMMAND):
            elapsed_time = time.perf_counter() - self.session_start
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            reply = dedent(f"""
            # ID SESIÓN
            {self.session_id}

            ## Tiempo transcurrido
            {int(hours)} horas, {int(minutes)} minutos, {int(seconds)} segundos

            ## Tokens totales consumidos
            {self.total_tokens}

            ## Coste total ($)
            {round(self.total_cost, 4)}

            ## Coste máximo de petición ($)
            {round(self.max_cost, 4)}
            """)
            await message.channel.send(reply)

        elif message.content.startswith(settings.HELP_COMMAND):
            reply = dedent(f"""
            # Comandos
            ## Chatear con el bot
            ```
            {settings.CHAT_COMMAND} <mensaje>
            ```
            Manda una pregunta a openAI y el bot te contesta

            ## Información de sesión
            ```
            {settings.INFO_COMMAND}
            ```
            Da información de la sesión como el coste total y los tokens utilizados

            ## Comandos disponibles
            ```
            {settings.HELP_COMMAND}
            ```
            Devuelve los comandos disponibles
            """)
            await message.channel.send(reply)


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    client_openai = OpenAI(api_key=get_openai_key())
    client = MyClient(intents=intents)
    client.run(get_discord_key())
