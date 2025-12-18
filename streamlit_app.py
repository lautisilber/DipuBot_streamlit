"""
streamlit_app.py
================
UI Streamlit para chat con documentos legales.
Solo provee interfaz; delega lógica RAG a chat/rag.py.
NO toca ETL ni construcción de índices.
"""

import streamlit as st
from dotenv import load_dotenv

# TODO: importar query_engine o función de chat desde chat.rag
# from chat.rag import get_query_engine, query

load_dotenv()


def main():
    st.set_page_config(page_title="Legal RAG Argentina", page_icon="⚖️")
    st.title("⚖️ Legal RAG Argentina")
    st.caption("Consulta documentos legales argentinos")

    # TODO: inicializar query engine (carga índice según INDEX_VERSION)
    # engine = get_query_engine()

    # Chat input
    if prompt := st.chat_input("Hacé tu consulta legal..."):
        st.chat_message("user").write(prompt)

        # TODO: ejecutar query contra el RAG
        # response = query(engine, prompt)
        response = "TODO: implementar RAG query"

        st.chat_message("assistant").write(response)


if __name__ == "__main__":
    main()
