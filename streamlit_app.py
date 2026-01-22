"""
streamlit_app.py
================
UI Streamlit para chat con documentos legales argentinos.
Conecta con el módulo RAG que usa FAISS + OpenAI.
"""

import base64
import os
import streamlit as st
from dotenv import load_dotenv

from chat.chat import initialize_chat, query
from chat.config import validate_index_exists
from pathlib import Path

load_dotenv()


def check_api_key():
    """Verifica si hay API key de OpenAI configurada (env o session)."""
    return bool(os.environ.get("OPENAI_API_KEY") or st.session_state.get("openai_api_key"))


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
            st.rerun()

def get_encoded_svg(filename: str) -> str:
    svg = Path(filename).read_text()
    svg_encoded = base64.b64encode(svg.encode()).decode()
    return svg_encoded


def add_css():
    main_div = "section.stMain"
    chat_bubble_user = "div.stLayoutWrapper div.stChatMessage.st-emotion-cache-1iitq1e"
    chat_bubble_bot = "div.stLayoutWrapper div.stChatMessage.st-emotion-cache-1fee4w7"
    sidebar = 'div[data-testid="stSidebarContent"]'
    top_bg = 'div[data-testid="stMainBlockContainer"]'
    main_title = "h1#dipu-bot"
    subtitle = 'div[data-testid="stCaptionContainer"]'
    chat_input_bg = 'div[data-testid="stBottom"]'
    chat_input = "div.stChatInput"
    toolbar = "div.stAppToolbar"
    avatar_bot = 'div[data-testid="stChatMessageAvatarAssistant"]'
    avatar_bot_inside = f"{avatar_bot} span span"

    bg_svg_encoded = get_encoded_svg("assets/svg/fondo-06.svg")
    avatar_assistant_svg_encoded = get_encoded_svg("assets/svg/quirqui-02.svg")
    title_svg_encoded = get_encoded_svg("assets/svg/titulo-01.svg")

    st.markdown(
        f"""
<style>
{toolbar} {{
    background-color: #6076B9 !important;
    color: #FFF !important;
}}

{chat_input_bg}, {top_bg} {{
    background-color: rgba(255, 255, 255, 0.7) !important;
}}

{subtitle} {{
    color: #6076B9 !important;
    text-shadow: 0 0 15px white !important;
}}

{main_title} {{
    background-image: url("data:image/svg+xml;base64,{title_svg_encoded}");
    background-size: contain;
    background-repeat: no-repeat;
    width: 35rem;
    height: 4rem;
    margin-right: 10px;
    flex-shrink: 0;

    /* Hide the text. */
    text-indent: 100%;
    white-space: nowrap;
    overflow: hidden;
}}

{avatar_bot} {{
    background-color: #3853A4 !important;
}}

{avatar_bot_inside} {{
    background-image: url("data:image/svg+xml;base64,{avatar_assistant_svg_encoded}");
    background-size: contain;
    background-repeat: no-repeat;
    width: 21px;
    height: 21px;
    margin-right: 10px;
    flex-shrink: 0;

    /* Hide the text. */
    text-indent: 100%;
    white-space: nowrap;
    overflow: hidden;
}}

{main_div} {{
    background-image: url("data:image/svg+xml;base64,{bg_svg_encoded}") !important;
    background-size: cover !important;
    background-repeat: no-repeat !important;
    background-attachment: fixed !important;
}}
</style>
""",
        unsafe_allow_html=True
    )


def main():
    st.set_page_config(
        page_title="DipuBot",
        page_icon="⚖️",
        layout="centered"
    )
    
    add_css()

    st.title("DipuBot")
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
    if prompt := st.chat_input("Hacé tu pregunta..."):
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
