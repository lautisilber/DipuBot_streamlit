"""UI real con conversación fija, sin usar API ni cargar el índice.

Ejecutar desde DipuBot: python -m streamlit run tests/ui_fixture.py
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st
import streamlit_app as app


def chat():
    app.initialize_chat = lambda: None
    app.validate_index_exists = lambda: True
    app.query = lambda *args: ("Respuesta de prueba.", [])
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": (
            "**Ley 25.675**\n\n" + "Información sobre la política ambiental nacional.\n\n" * 35
        ), "sources": []}]
    app.main()


def information():
    runpy.run_path(str(next((ROOT / "pages").glob("1_*.py"))))


def congress():
    runpy.run_path(str(next((ROOT / "pages").glob("2_*.py"))))


st.navigation([
    st.Page(chat, title="DipuBot", default=True),
    st.Page(information, title="¿Qué es DipuBot?"),
    st.Page(congress, title="¿Cómo funciona el Congreso?"),
]).run()
