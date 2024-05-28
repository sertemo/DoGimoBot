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

from icecream import ic
from pathlib import Path
from string import Template
from typing import Any

from dogimobot.exceptions import FormatterException
from dogimobot.settings import USERS


def format_stats(
    template: Path,
    session_id: str,
    elapsed_hours: int,
    elapsed_minutes: int,
    elapsed_seconds: int,
    total_tokens: int,
    total_cost: float,
    user_stats: dict[str, dict[str, Any]],
    max_cost: float,
    session_start_time: str,
) -> str:
    """Formatea la plantilla de stats
    y la devuelve formateada

    Parameters
    ----------
    template : Path
        _description_
    session_id : str
        _description_
    elapsed_hours : int
        _description_
    elapsed_minutes : int
        _description_
    elapsed_seconds : int
        _description_
    total_tokens : int
        _description_
    total_cost : float
        _description_
    user_stats : dict[str, dict[str, Any]]
        _description_
    max_cost : float
        _description_
    session_start_time : str
        _description_

    Returns
    -------
    str
        _description_
    """

    # Cargamos la plantilla
    try:
        plantilla = Template(template.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Se ha producido un error al formatear: {exc}")
        raise FormatterException("Se ha producido un problema al formatear:", exc)

    user_stats_table = "```\n| Usuario   | Tokens Consumidos | Coste ($)  |\n"
    user_stats_table += "|-----------|-------------------|------------|\n"
    for user, stats in user_stats.items():
        user_stats_table += f"| {USERS[user]:<9} | {stats['tokens']:<17} | {stats['cost']:<10.4f} |\n"
    user_stats_table += "```"


    return plantilla.safe_substitute(
        session_id=session_id,
        elapsed_hours=str(elapsed_hours).zfill(2),
        elapsed_minutes=str(elapsed_minutes).zfill(2),
        elapsed_seconds=str(elapsed_seconds).zfill(2),
        total_tokens=total_tokens,
        total_cost=total_cost,
        user_stats=user_stats_table,
        max_cost=max_cost,
        session_start_time=session_start_time,
    )
