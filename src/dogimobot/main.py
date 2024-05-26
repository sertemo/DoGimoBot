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
from typing import Deque, Any

import discord
from discord import Message
from icecream import ic
from openai import OpenAI

from dogimobot import settings
from dogimobot.utils import get_discord_key, get_openai_key

# TODO : Agregar Logging


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory: Deque[dict[str, Any]] = deque(maxlen=settings.MEMORY_SIZE)

    async def on_ready(self):
        ic(f"Logged on as {self.user}")

    async def on_message(self, message: Message):
        ic(message.author)
        # No respondas a ti mismo o a otros bots
        if message.author == self.user or message.author.bot:
            return

        # Guarda el mensaje en la memoria
        mensaje = message.content.replace(settings.COMMAND, "").strip()
        self.memory.append(
            {
                "role": (
                    "user" if message.author.name in settings.USERS else "assistant"
                ),
                "content": mensaje,
                "author": str(message.author),
            }
        )

        # Si el mensaje contiene el comando, responde
        if message.content.startswith(settings.COMMAND):

            # Prepara el contexto incluyendo las últimas interacciones
            context = [{"role": "system", "content": settings.SYSTEM_PROMPT}] + [
                {
                    "role": msg["role"],
                    "content": f"{msg['author']} dijo: {msg['content']}",
                }
                for msg in self.memory
            ]
            print(context)

            try:
                response = client_openai.chat.completions.create(
                    model=settings.MODELO,
                    messages=context + [{"role": "user", "content": mensaje}],
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
            await message.channel.send(reply)


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    client_openai = OpenAI(api_key=get_openai_key())
    client = MyClient(intents=intents)
    client.run(get_discord_key())
