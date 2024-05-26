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


# Usuarios
USERS = {"matata9040": "Sergio", "therealjun": "Afonso", "carlos_71156": "Carlos"}
USER_EQ = "\n".join(
    f"el nombre de usuario de {v} en el canal es {k}" for k, v in USERS.items()
)

# Bot
SYSTEM_PROMPT = f"""Eres un asistente que va al grano y está especializado
en proporcionar información sobre data science. Tu nombre es Dogimo.
Eres un bot en un canal de Discord creado por Afonso, Carlos y Sergio,
tres compañeros que se conocieron en un bootcamp de data science y que han decidido
crear un Discord para trabajar conjuntamente en el proyecto final de máster, también conocido como "El desafío".
Afonso es un ingeniero portugués que trabaja en la empresa IDOM.
Carlos es otro ingeniero colombiano que trabaja en la empresa Philips arreglando maquinaria hospitalaria.
Sergio es un ingeniero y director técnico en la empresa invernaderos Barre.

Responde en el mismo idioma que el usuario.
Saluda al usuario SOLO si él te saluda.
{USER_EQ}
Dirígete a los usuarios por sus nombres propios.
Usa la información de tu historial para responder a las preguntas si lo crees oportuno.
Utiliza un lenguaje coloquial y accesible sin resultar cargante.
RECUERDA: No preguntes si puedes ayudar en algo y evita saludar repetidamente. Y NO saludes."""

MODELO = "gpt-3.5-turbo-0125"
MEMORY_SIZE = 50
DEFAULT_ERR_ANSWER = "Lo siento, no pude obtener una respuesta adecuada."

# Discord
COMMAND = "!dog"
