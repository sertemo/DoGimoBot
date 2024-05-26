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
from typing import Deque, Union, Dict

import discord
from discord import Message
from icecream import ic
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

from dogimobot import settings
from dogimobot.logging_config import logger
from dogimobot.utils import get_discord_key, get_openai_key


# TODO : Llevar log del coste y de la sesión

MessageType = Union[Dict[str, str], Dict[str, Union[str, Dict[str, str]]]]


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory: Deque[MessageType] = deque(maxlen=settings.MEMORY_SIZE)

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
        return message.content.replace(settings.COMMAND, "").strip()

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

    async def on_ready(self):
        ic(f"Logged on as {self.user}")

    async def on_message(self, message: Message):
        ic(message.author)
        # No respondas a ti mismo o a otros bots
        if message.author == self.user or message.author.bot:
            return

        # Guarda el mensaje en la memoria
        self._save_in_memory(message)

        # Logging
        logger.info(f"{message.author} dijo: {message.content}")

        # Si el mensaje contiene el comando, responde
        if message.content.startswith(settings.COMMAND):

            # Prepara el contexto incluyendo las últimas interacciones
            context = self._get_context()

            try:
                response = client_openai.chat.completions.create(
                    model=settings.MODELO,
                    messages=context
                    + [
                        {
                            "role": "user",
                            "content": self._remove_command_from_msg(message),
                        }
                    ],
                )
            except Exception as exc:
                print(f"Se ha producido un error: {exc}")
                return

            reply_content = (
                response.choices[0].message.content
                if response and response.choices
                else None
            )
            reply: str = (
                reply_content.strip() if reply_content else settings.DEFAULT_ERR_ANSWER
            )

            # Añadimos la respuesta a memoria
            self.memory.append(
                {"role": "assistant", "content": reply, "author": "Dogimo"}
            )

            # Añadimos la respuesta al logging
            logger.info(f"Dogimo dijo: {reply}")

            await message.channel.send(reply)


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    client_openai = OpenAI(api_key=get_openai_key())
    client = MyClient(intents=intents)
    client.run(get_discord_key())
