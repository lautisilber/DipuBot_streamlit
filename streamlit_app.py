"""
streamlit_app.py
================
UI Streamlit para chat con documentos legales argentinos.
Conecta con el módulo RAG que usa FAISS + OpenAI.
"""

import streamlit as st
from dotenv import load_dotenv

from chat.rag import initialize_rag, query
from chat.config import validate_index_exists

load_dotenv()


def init_session_state():
    """Inicializa el estado de la sesión."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
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
    
    with st.expander("📚 Fuentes consultadas", expanded=False):
        for source in sources:
            tipo = source.get("tipo", "")
            numero = source.get("numero", "")
            titulo = source.get("titulo", "")
            year = source.get("year", "")
            
            source_text = f"**{tipo} {numero}**"
            if year:
                source_text += f" ({year})"
            if titulo:
                source_text += f" - {titulo}"
            
            st.markdown(f"- {source_text}")


def main():
    st.set_page_config(
        page_title="Legal RAG Argentina",
        page_icon="⚖️",
        layout="centered"
    )
    
    st.title("⚖️ Legal RAG Argentina")
    st.caption("Consultá sobre legislación argentina")
    
    init_session_state()
    
    # Verificar que existe el índice
    if not validate_index_exists():
        st.error(
            "❌ No se encontró el índice de búsqueda. "
            "Ejecutá primero el ETL: `cd etl && python3 run_etl.py`"
        )
        st.stop()
    
    # Inicializar RAG (solo una vez)
    if not st.session_state.rag_initialized:
        with st.spinner("Cargando índice de leyes..."):
            try:
                initialize_rag()
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
                    response, sources = query(prompt)
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
    
    # Sidebar con info
    with st.sidebar:
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
            st.rerun()


if __name__ == "__main__":
    main()
