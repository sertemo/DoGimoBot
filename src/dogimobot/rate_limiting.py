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

"""Clase con métodos de rate limitter para decorar la función
de obtener respuesta de openAI.
El método limit de RateLimitter hace de decorador"""

from collections import defaultdict
from datetime import datetime
from functools import wraps
import random
from typing import Callable, Any

from discord import Message
from icecream import ic
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from dogimobot import settings


def default_response(user: str) -> ChatCompletion:
    """Respuesta por defecto cuando el usuario excede el rate limit"""
    return ChatCompletion(
        id=f"chatcmpl-{random.randint(111, 9999)}",
        object="chat.completion",
        created=1677652288,
        model=settings.MODELO,
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=(
                        f"\n\n🛑 No tan rápido, {settings.USERS[user]}. "
                        f"Has excedido el límite de mensajes por minuto. "
                        f"Por favor, espera {settings.RATE_LIMIT} segundos para enviar otro mensaje."
                    ),
                ),
                logprobs=None,
                finish_reason="stop",
            )
        ],
    )


class RateLimiter:
    track: defaultdict[str, dict[str, Any]] = defaultdict(
        lambda: {"num_peticiones": 0, "start": datetime.now()}
    )

    @staticmethod
    def limit(
        msg_per_minute: int = settings.MAX_MSG_PER_MINUTES,
        rate_time: int = settings.RATE_LIMIT,
    ):
        def func_wrapper(
            f: Callable[[Message, list[ChatCompletionMessage]], ChatCompletion]
        ) -> Callable[[Message, list[ChatCompletionMessage]], ChatCompletion]:
            @wraps(f)
            def wrapper(*args, **kwds) -> ChatCompletion:
                print("Dentro del decorador RateLimiter.limit")
                ic(kwds)
                # Trackear el usuario
                mensaje: Message = kwds["message"]
                ic(mensaje)
                user_key: str = mensaje.author.name
                user_data = RateLimiter.track[user_key]
                ic(user_key)
                ic(user_data)

                # Comprobar si el tiempo ha pasado un minuto
                now: datetime = datetime.now()
                inicio: datetime = user_data["start"]
                elapsed_time: float = (now - inicio).total_seconds()

                if elapsed_time > rate_time:
                    # Resetear el contador
                    user_data["num_peticiones"] = 0
                    user_data["start"] = now

                # Incrementar el contador de peticiones
                user_data["num_peticiones"] += 1

                # Verificar si el número de peticiones excede el límite
                if user_data["num_peticiones"] > msg_per_minute:
                    return default_response(user_key)

                return f(*args, **kwds)

            return wrapper

        return func_wrapper
