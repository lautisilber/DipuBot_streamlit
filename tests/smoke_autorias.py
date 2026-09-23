"""Prueba explícita con API real (consume tokens).

Ejecutar con: python tests/smoke_autorias.py desde DipuBot.
Requiere haber importado las autorías y configurar OPENAI_API_KEY.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chat.chat import get_chat
from chat.skills.sql_skill import SQLSkill


def main():
    chat = get_chat()
    skill = SQLSkill()
    for question, person, block in [
        ("¿Quién propuso el proyecto que se convirtió en la Ley 26.618 y cuál era su bloque?",
         "AUGSBURGER", "SOCIALISTA"),
        ("¿Quién fue la autora del proyecto de la Ley 26.485 y a qué bloque pertenecía?",
         "PERCEVAL", "VICTORIA"),
        ("¿Quién presentó el proyecto que dio origen a la Ley 27.610? Indicá su bloque o procedencia institucional.",
         "FERNANDEZ", "PODER EJECUTIVO"),
    ]:
        route = chat._determine_skill(question)
        assert route == "sql_query", (question, route)
        result = skill.execute(question)
        assert not result.metadata.get("error"), result.metadata
        evidence = json.dumps(result.metadata["raw_results"], ensure_ascii=False).upper()
        assert person in evidence and block in evidence, (question, result.metadata)
        print(json.dumps({"question": question, "sql": result.metadata["sql"],
                          "answer": result.response}, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
