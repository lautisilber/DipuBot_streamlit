"""
streamlit_app.py
================
UI Streamlit para chat con documentos legales argentinos.
Conecta con el módulo RAG que usa FAISS + OpenAI.
"""

import os
import sys

# En Windows la consola usa cp1252, que no soporta los emojis de los logs.
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

from chat.chat import initialize_chat, query
from chat.config import validate_index_exists

from css.streamlit_css import add_css, add_js

load_dotenv()



def init_session_state():
    """Inicializa el estado de la sesión."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
"""
**¡Hola! Soy DipuBot**, puedo ayudarte a buscar y comprender la legislación de nuestro país ¡Sé todas las leyes que fueron aprobadas entre 1997 y 2025! Si querés conocer mejor cómo funciono, te invito a revisar mi manual de uso en la sección "¿Qué es DipuBot?" en el menu lateral.
"""
            ),
            "sources": []
        })
    if "rag_initialized" not in st.session_state:
        st.session_state.rag_initialized = False


def display_chat_history():
    """Muestra el historial de mensajes. Devuelve una pregunta si el usuario
    hizo clic en una sugerencia de seguimiento del último mensaje."""
    clicked_question = None
    last_assistant_idx = max(
        (i for i, m in enumerate(st.session_state.messages) if m["role"] == "assistant"),
        default=-1
    )
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant" and message.get("sources"):
                display_sources(message["sources"])
                # Solo se pueden clickear las sugerencias del último mensaje
                if i == last_assistant_idx:
                    clicked_question = display_related_questions(message["sources"], key_prefix=f"related_{i}")
    return clicked_question


def get_related_questions(sources):
    """Extrae las preguntas relacionadas embebidas en las fuentes, si las hay."""
    for s in sources or []:
        if s.get("type") == "related_questions":
            return s.get("questions", [])
    return []


def display_related_questions(sources, key_prefix):
    """Muestra botones con preguntas de seguimiento sobre leyes relacionadas."""
    questions = get_related_questions(sources)
    if not questions:
        return None

    st.caption("¿Querés saber más?")
    cols = st.columns(len(questions))
    for i, question in enumerate(questions):
        with cols[i]:
            if st.button(question, key=f"{key_prefix}_{i}"):
                return question
    return None


def display_sources(sources):
    """Muestra las fuentes usadas en la respuesta."""
    if not sources:
        return

    # No mostramos "fuentes consultadas" para consultas SQL ni para el
    # marcador interno de preguntas relacionadas
    filtered_sources = [
        s for s in sources
        if s.get("type") not in ("sql_query", "related_questions")
    ]

    if not filtered_sources:
        return
    
    with st.expander("Fuentes consultadas", expanded=False):
        for source in filtered_sources:
            tipo = source.get("tipo", "")
            numero = source.get("numero", "")
            # Preferimos titulo_sumario sobre titulo_resumido
            titulo = source.get("titulo_sumario") or source.get("titulo_resumido") or source.get("titulo", "")
            organismo = source.get("organismo_origen", "")
            fecha_sancion = source.get("fecha_sancion", "")
            year = source.get("year", "")

            source_text = f"**{tipo} {numero}**"

            if year:
                source_text += f" ({year})"
            
            if fecha_sancion:
                try:
                    fecha_obj = datetime.strptime(fecha_sancion, "%Y-%m-%d")
                    fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
                    source_text += f" - Sancionada: {fecha_formateada}"
                except:
                    source_text += f" - Sancionada: {fecha_sancion}"
            
            if organismo:
                source_text += f" - {organismo}"
            
            if titulo:
                source_text += f" -  _{titulo}_"
            
            st.markdown(f"- {source_text}")


def render_sidebar():
    """Renderiza el sidebar con configuración e información."""
    with st.sidebar:

        if st.button("Limpiar conversación"):
            st.session_state.messages = []
            # Agregar mensaje de bienvenida después de limpiar
            st.session_state.messages.append({
                "role": "assistant",
                "content": (
"""
**¡Hola! Soy DipuBot**, puedo ayudarte a buscar y comprender la legislación de nuestro país ¡Sé todas las leyes que fueron aprobadas entre 1997 y 2025! Si querés conocer mejor cómo funciono, te invito a revisar mi manual de uso en la sección "¿Qué es DipuBot?" en el menu lateral.
"""
                ),
                "sources": []
            })
            st.rerun()


def main():
    st.set_page_config(
        page_title="DipuBot",
        page_icon="assets/svg/quirqui-01.svg",
        layout="centered"
    )

    add_css(main=True)
    add_js()

    st.title("DipuBot")
    st.caption("Consultá sobre legislación argentina")
    st.logo("assets/svg/quirqui-02.svg")

    init_session_state()

    # Renderizar sidebar primero (para que aparezca el input de API key)
    render_sidebar()

    # Verificar que existe el índice
    if not validate_index_exists():
        st.error(
            "No se encontró el índice de búsqueda. "
            "Ejecutá primero el ETL: `cd etl && python3 run_etl.py`"
        )
        st.stop()



    # Inicializar Chat (solo una vez)
    if not st.session_state.rag_initialized:
        with st.spinner("Cargando índice de leyes..."):
            try:
                initialize_chat()
                st.session_state.rag_initialized = True
            except Exception as e:
                st.error(f"Error al inicializar: {e}")
                st.stop()

    # Mostrar historial (y capturar clic en una pregunta relacionada, si lo hubo)
    clicked_question = display_chat_history()

    # Si en el turno anterior se clickeó una sugerencia justo después de
    # generarse la respuesta, se guardó en pending_question para procesarla ahora.
    pending_question = st.session_state.pop("pending_question", None)

    # Input del usuario (texto libre, clic en sugerencia del historial, o
    # sugerencia pendiente de la respuesta recién generada)
    prompt = st.chat_input("Hacé tu pregunta...") or clicked_question or pending_question
    if prompt:
        # Agregar mensaje del usuario
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.write(prompt)

        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Buscando en la legislación..."):
                try:
                    # Pasar historial previo (excluyendo el mensaje actual)
                    conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []
                    response, sources = query(prompt, conversation_history)
                    st.write(response)
                    display_sources(sources)
                    new_msg_index = len(st.session_state.messages) + 1
                    followup = display_related_questions(sources, key_prefix=f"related_{new_msg_index}")

                    # Guardar en historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources
                    })

                    if followup:
                        st.session_state.pending_question = followup
                        st.rerun()
                except Exception as e:
                    error_msg = f"Error al procesar la consulta: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": []
                    })


if __name__ == "__main__":
    main()
