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

from collections import defaultdict
from typing import Union

from discord import Message

from dogimobot import settings


class BotStats:
    """Clase para llevar registros de las estadísticas
    relacionadas con el bot
    """

    def __init__(self) -> None:
        """Inicializa las estadísticas"""
        self.total_queries: int = 0
        self.total_cost = 0.0
        self.max_cost: float = 0.0
        self.total_tokens: int = 0
        # Estadísticas de usuario
        self.user_stats: defaultdict[str, dict[str, Union[int, float]]] = defaultdict(
            lambda: {"tokens": 0, "cost": 0.0, "queries": 0}
        )

    def add_total_tokens(self, total_tokens: int) -> None:
        """Suma a total_tokens los tokens de la query
        para llevar un registro

        Parameters
        ----------
        total_tokens : int
            _description_
        """
        self.total_tokens += total_tokens

    def add_total_queries(self) -> None:
        """Suma 1 al numero de queries totales
        a chatgpt
        """
        self.total_queries += 1

    def calculate_total_cost(self, in_tokens: int, out_tokens: int) -> float:
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
        in_cost: float = (in_tokens / 1e6) * settings.OPENAI_PRICING[settings.MODELO][
            "in"
        ]
        out_cost: float = (out_tokens / 1e6) * settings.OPENAI_PRICING[settings.MODELO][
            "out"
        ]

        return in_cost + out_cost

    def add_total_and_max_cost(self, total_cost: float) -> None:
        """Suma a la sesión el coste de la query
        y el máximo

        Parameters
        ----------
        total_cost : float
            _description_
        """

        self.total_cost += total_cost
        self.max_cost = max(self.max_cost, total_cost)

    def add_user_stats(
        self, message: Message, total_tokens: int, total_cost: float
    ) -> None:
        """Alimenta las estadísticas de los usuarios
        para llevar registro del gasto de cada uno en la sesión
        y el número de queries de cada uno"""

        self.user_stats[message.author.name]["tokens"] += total_tokens
        self.user_stats[message.author.name]["cost"] += total_cost
        self.user_stats[message.author.name]["queries"] += 1
