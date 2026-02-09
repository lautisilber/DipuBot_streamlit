"""
streamlit_app.py
================
UI Streamlit para chat con documentos legales argentinos.
Conecta con el módulo RAG que usa FAISS + OpenAI.
"""

import os
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

from chat.chat import initialize_chat, query
from chat.config import validate_index_exists

load_dotenv()


def check_api_key():
    """Verifica si hay API key de OpenAI configurada (env o session)."""
    return bool(os.environ.get("OPENAI_API_KEY") or st.session_state.get("openai_api_key"))


def init_session_state():
    """Inicializa el estado de la sesión."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Mensaje de bienvenida automático
        st.session_state.messages.append({
            "role": "assistant",
            "content": "¡Hola! Soy DipuBot, puedo ayudarte a buscar y comprender la legislación de nuestro país ¡Sé todas las leyes que fueron aprobadas entre 2023 y 2025! Si querés conocer mejor cómo funciono, te invito a revisar mi manual de uso en la sección “¿Qué es DipuBot?”.",
            "sources": []
        })
    if "rag_initialized" not in st.session_state:
        st.session_state.rag_initialized = False


def display_chat_history():
    """Muestra el historial de mensajes."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant" and message.get("sources"):
                display_sources(message["sources"])


def display_sources(sources):
    """Muestra las fuentes usadas en la respuesta."""
    if not sources:
        return
    
    # No mostramos "fuentes consultadas" para consultas SQL
    filtered_sources = [s for s in sources if s.get("type") != "sql_query"]
    
    if not filtered_sources:
        return
    
    with st.expander("📚 Fuentes consultadas", expanded=False):
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
        # Configuración de API key (solo si no está en .env)
        if not os.environ.get("OPENAI_API_KEY"):
            st.header("🔑 Configuración")
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=st.session_state.get("openai_api_key", ""),
                placeholder="sk-...",
                help="Tu API key de OpenAI. Se guarda solo en esta sesión."
            )
            if api_key:
                st.session_state.openai_api_key = api_key
                os.environ["OPENAI_API_KEY"] = api_key
            st.divider()
        
        st.header("ℹ️ Información")
        st.markdown("""
        Este chatbot responde preguntas sobre **legislación argentina** 
        usando inteligencia artificial.
        
        **¿Cómo funciona?**
        1. Tu pregunta se busca en una base de leyes
        2. Se encuentran los fragmentos más relevantes
        3. La IA genera una respuesta basada en esos textos
        
        **Ejemplos de preguntas:**
        - ¿Se suspenden las PASO en 2025?
        - ¿Qué es el Parque Nacional Laguna El Palmar?
        - ¿Qué dice la ley sobre cardiopatías congénitas?
        """)
        
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.messages = []
            # Agregar mensaje de bienvenida después de limpiar
            st.session_state.messages.append({
                "role": "assistant",
                "content": "¡Hola! Soy DipuBot, puedo ayudarte a buscar y comprender la legislación de nuestro país ¡Sé todas las leyes que fueron aprobadas entre 2023 y 2025! Si querés conocer mejor cómo funciono, te invito a revisar mi manual de uso en la sección “¿Qué es DipuBot?”.",
                "sources": []
            })
            st.rerun()


def main():
    st.set_page_config(
        page_title="Legal RAG Argentina",
        page_icon="⚖️",
        layout="centered"
    )
    
    st.title("⚖️ Legal RAG Argentina")
    st.caption("Consultá sobre legislación argentina")
    
    init_session_state()
    
    # Renderizar sidebar primero (para que aparezca el input de API key)
    render_sidebar()
    
    # Verificar que existe el índice
    if not validate_index_exists():
        st.error(
            "❌ No se encontró el índice de búsqueda. "
            "Ejecutá primero el ETL: `cd etl && python3 run_etl.py`"
        )
        st.stop()
    
    # Verificar API key
    if not check_api_key():
        st.warning("⚠️ Configurá tu API key de OpenAI en el sidebar para continuar.")
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
    
    # Mostrar historial
    display_chat_history()
    
    # Input del usuario
    if prompt := st.chat_input("Hacé tu consulta legal..."):
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
                    
                    # Guardar en historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources
                    })
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
