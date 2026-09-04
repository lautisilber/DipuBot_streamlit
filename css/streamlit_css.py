import streamlit as st

from pathlib import Path
import base64

# Paleta oficial (frames del diseñador, de claro a oscuro)
CREMA = "#FDF6EF"
AMARILLO = "#F9D24B"
CELESTE = "#A8D8F0"
AZUL_MEDIO = "#6390CE"
AZUL = "#3853A4"
TEXTO = "#1A1A2E"

def get_encoded_svg(filename: str) -> str:
    svg = Path(filename).read_text()
    svg_encoded = base64.b64encode(svg.encode()).decode()
    return svg_encoded

def get_encoded_png(filename: str) -> str:
    png = Path(filename).read_bytes()
    png_encoded = base64.b64encode(png).decode()
    return png_encoded

def add_css(main: bool=False) -> None:
    main_div = "section.stMain"
    chat_bubble_inner = 'div[data-testid="stChatMessage"]'
    chat_bubble = f'div[data-testid="stLayoutWrapper"]:has(> {chat_bubble_inner})'
    chat_bubble_user_inner = f'{chat_bubble_inner}:has(> div[data-testid="stChatMessageAvatarUser"])'
    chat_bubble_bot_inner = f'{chat_bubble_inner}:has(> div[data-testid="stChatMessageAvatarAssistant"])'
    chat_bubble_user = f'div[data-testid="stLayoutWrapper"]:has(> {chat_bubble_inner} > div[data-testid="stChatMessageAvatarUser"])'
    chat_bubble_bot = f'div[data-testid="stLayoutWrapper"]:has(> {chat_bubble_inner} > div[data-testid="stChatMessageAvatarAssistant"])'
    avatar_user = 'div[data-testid="stChatMessageAvatarUser"]'
    sidebar = 'div[data-testid="stSidebarContent"]'
    top_bg = 'div[data-testid="stMainBlockContainer"]'
    main_title = "h1#dipu-bot"
    subtitle = 'div[data-testid="stCaptionContainer"]'
    chat_input_bg = 'div[data-testid="stBottom"]'
    chat_input = "div.stChatInput"
    toolbar = "div.stAppToolbar"
    avatar_bot = 'div[data-testid="stChatMessageAvatarAssistant"]'
    avatar_bot_inside = f"{avatar_bot} span span"
    sidebar_logo = 'img[data-testid="stSidebarLogo"]'
    header_logo = 'img[data-testid="stHeaderLogo"]'
    expander = 'details[data-testid="stExpander"]'

    st.html(
f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap" rel="stylesheet">

<style>
:root {{
    --dipu-crema: {CREMA};
    --dipu-amarillo: {AMARILLO};
    --dipu-celeste: {CELESTE};
    --dipu-azul-medio: {AZUL_MEDIO};
    --dipu-azul: {AZUL};
    --dipu-texto: {TEXTO};
}}

html,
body,
[class*="st-"]:not([data-testid="stIconMaterial"]) {{
  font-family: "Space Grotesk", sans-serif !important;
}}

/* ---------- Fondo general: blanco limpio, como en los frames ---------- */
{main_div} {{
    background-color: #FFFFFF !important;
    color: var(--dipu-texto) !important;
}}

{main_div} p, {main_div} span, {main_div} li, {main_div} h2, {main_div} h3,
{main_div} strong, {main_div} em, {main_div} a {{
    color: var(--dipu-texto) !important;
}}

{chat_input_bg}, {top_bg},
{chat_input_bg} > div,
div[data-testid="stBottomBlockContainer"] {{
    background-color: transparent !important;
}}

/* ---------- Barra superior ---------- */
{toolbar} {{
    background-color: transparent !important;
    color: var(--dipu-azul) !important;
}}

/* ---------- Título y subtítulo ---------- */
{main_title} {{
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    width: 100%;
    max-width: 22rem;
    height: 4.5rem;
    margin: 0 auto 0.25rem auto;
    flex-shrink: 0;

    /* Hide the text. */
    text-indent: 100%;
    white-space: nowrap;
    overflow: hidden;
}}

{subtitle} {{
    color: var(--dipu-azul) !important;
    text-align: center !important;
    font-weight: 600 !important;
    text-shadow: none !important;
}}

{subtitle} p {{
    color: var(--dipu-azul) !important;
    font-size: 0.95rem !important;
}}

/* ---------- Burbujas de chat ---------- */
{chat_bubble} {{
    background-color: transparent !important;
}}

{chat_bubble_bot}, {chat_bubble_user} {{
    background-color: transparent !important;
}}

/* Bot: sin caja, texto suelto con el avatar del quirquincho al costado */
{chat_bubble_bot_inner} {{
    background-color: transparent !important;
    border: none !important;
    padding-left: 0 !important;
}}

{chat_bubble_bot_inner} p {{
    color: var(--dipu-texto) !important;
    line-height: 1.6 !important;
}}

/* Usuario: píldora celeste alineada a la derecha, sin avatar */
{chat_bubble_user_inner} {{
    background-color: var(--dipu-azul-medio) !important;
    color: #FFFFFF !important;
    border-radius: 22px !important;
    padding: 0.6rem 1.1rem !important;
    width: fit-content !important;
    max-width: 80% !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}}

{chat_bubble_user_inner} p,
{chat_bubble_user_inner} span,
{chat_bubble_user_inner} strong,
{chat_bubble_user_inner} li {{
    color: #FFFFFF !important;
}}

/* El avatar del usuario no aparece en el diseño */
{avatar_user} {{
    display: none !important;
}}

{avatar_bot} {{
    background-color: transparent !important;
}}

/* ---------- Botones: píldoras azules (prompts sugeridos) ---------- */
{main_div} div.stButton > button {{
    background-color: var(--dipu-azul) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 22px !important;
    padding: 0.5rem 1.15rem !important;
    font-weight: 500 !important;
    line-height: 1.3 !important;
    white-space: normal !important;
    height: auto !important;
    transition: background-color 0.15s ease, transform 0.15s ease !important;
}}

{main_div} div.stButton > button:hover {{
    background-color: var(--dipu-azul-medio) !important;
    transform: translateY(-1px) !important;
}}

{main_div} div.stButton > button p,
{main_div} div.stButton > button span,
{main_div} div.stButton > button div {{
    color: #FFFFFF !important;
}}

{main_div} div.stButton > button:focus:not(:active) {{
    color: #FFFFFF !important;
    box-shadow: 0 0 0 2px rgba(56, 83, 164, 0.25) !important;
}}

/* ---------- Input de chat: borde amarillo redondeado ---------- */
{chat_input} {{
    background-color: #FFFFFF !important;
    border: 2px solid var(--dipu-amarillo) !important;
    border-radius: 30px !important;
    padding: 0.15rem 0.4rem !important;
    box-shadow: none !important;
    overflow: hidden !important;
}}

{chat_input}:focus-within {{
    border-color: var(--dipu-amarillo) !important;
    box-shadow: 0 0 0 3px rgba(249, 210, 75, 0.3) !important;
}}

/* Todas las capas internas de Streamlit son grises y cuadradas.
   Las transparentamos por completo (menos el botón de enviar) para que
   se vea únicamente la píldora blanca del contenedor. */
{chat_input} *:not(button):not(button *) {{
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}

{chat_input} textarea {{
    background-color: transparent !important;
    color: var(--dipu-texto) !important;
    border: none !important;
    box-shadow: none !important;
    padding-left: 0.75rem !important;
}}

{chat_input} textarea::placeholder {{
    color: var(--dipu-amarillo) !important;
    opacity: 1 !important;
}}

{chat_input} button {{
    background-color: var(--dipu-amarillo) !important;
    border-radius: 50% !important;
    color: var(--dipu-azul) !important;
}}

{chat_input} button:hover {{
    background-color: var(--dipu-amarillo) !important;
    opacity: 0.85 !important;
}}

{chat_input} button svg,
{chat_input} button span {{
    color: var(--dipu-azul) !important;
    fill: var(--dipu-azul) !important;
}}

/* ---------- Sidebar: fondo azul pleno, píldoras claras ---------- */
{sidebar} {{
    background-color: var(--dipu-azul) !important;
}}

/* Todo el texto del sidebar va en AZUL: se lee sobre las píldoras claras */
{sidebar} p, {sidebar} span, {sidebar} li, {sidebar} h1, {sidebar} h2,
{sidebar} h3, {sidebar} strong, {sidebar} em, {sidebar} label,
{sidebar} a, {sidebar} a span {{
    color: var(--dipu-azul) !important;
}}

{sidebar} h1, {sidebar} h1 *,
{sidebar} h2, {sidebar} h2 *,
{sidebar} h3, {sidebar} h3 * {{
    color: var(--dipu-azul) !important;
}}

/* Botón de colapsar el sidebar («): BLANCO y SIEMPRE VISIBLE sobre el
   fondo azul. Streamlit lo oculta con opacity 0 hasta el hover, así que
   forzamos la opacidad en todos los estados. */
{sidebar} div[data-testid="stSidebarHeader"] button,
{sidebar} div[data-testid="stSidebarHeader"] button *,
{sidebar} div[data-testid="stSidebarHeader"] button:hover,
{sidebar} div[data-testid="stSidebarHeader"] button:hover *,
{sidebar} div[data-testid="stSidebarHeader"] button:focus,
{sidebar} div[data-testid="stSidebarHeader"] button:active,
{sidebar} button[data-testid="stSidebarCollapseButton"],
{sidebar} button[data-testid="stSidebarCollapseButton"] *,
{sidebar} button[data-testid="stSidebarCollapseButton"]:hover,
{sidebar} button[data-testid="stSidebarCollapseButton"]:hover *,
{sidebar} button[kind="header"],
{sidebar} button[kind="header"] * {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    background-color: transparent !important;
    opacity: 1 !important;
    visibility: visible !important;
}}

/* El ícono es una ligadura de Material Icons: lleva su propio color
   y su propia opacidad, así que también los fijamos. */
{sidebar} div[data-testid="stSidebarHeader"] span[data-testid="stIconMaterial"],
{sidebar} button span[data-testid="stIconMaterial"],
{sidebar} div[data-testid="stSidebarHeader"] svg,
{sidebar} div[data-testid="stSidebarHeader"] {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    opacity: 1 !important;
}}

/* Todos los links iguales: píldora blanca, texto azul, activo o no.
   Streamlit tiñe el link activo, así que forzamos los tres estados. */
{sidebar} a[data-testid="stSidebarNavLink"],
{sidebar} a[data-testid="stSidebarNavLink"][aria-current],
{sidebar} a[data-testid="stSidebarNavLink"][aria-selected="true"],
{sidebar} li:has(> a[data-testid="stSidebarNavLink"]) {{
    background-color: #F2F5FA !important;
    border-radius: 22px !important;
    padding: 0.4rem 1rem !important;
    margin-bottom: 0.45rem !important;
}}

{sidebar} li:has(> a[data-testid="stSidebarNavLink"]) {{
    padding: 0 !important;
    background-color: transparent !important;
}}

/* El texto de los links de navegación va SIEMPRE en azul sobre la píldora
   clara. El `*` cubre cualquier span/p/div que Streamlit anide adentro. */
{sidebar} a[data-testid="stSidebarNavLink"],
{sidebar} a[data-testid="stSidebarNavLink"] *,
{sidebar} a[data-testid="stSidebarNavLink"]:hover *,
{sidebar} a[data-testid="stSidebarNavLink"]:visited * {{
    color: var(--dipu-azul) !important;
    font-weight: 600 !important;
}}

{sidebar} a[data-testid="stSidebarNavLink"]:hover {{
    background-color: #FFFFFF !important;
}}

{sidebar} div.stButton > button {{
    background-color: rgba(255, 255, 255, 0.92) !important;
    color: var(--dipu-azul) !important;
    border: none !important;
    border-radius: 22px !important;
    font-weight: 600 !important;
}}

{sidebar} div.stButton > button p {{
    color: var(--dipu-azul) !important;
}}

{sidebar} div.stButton > button:hover {{
    background-color: #FFFFFF !important;
}}

{sidebar_logo} {{
    height: 100% !important;
}}

div:has(> {sidebar_logo}), button:has(> {sidebar_logo}) {{
    padding-top: 4px !important;
    height: calc(100% - 4px) !important;
}}

div:has(> {header_logo}) {{
    display: none !important;
}}

/* ---------- Expander de fuentes ---------- */
{expander} {{
    background-color: var(--dipu-crema) !important;
    border: 1px solid rgba(56, 83, 164, 0.15) !important;
    border-radius: 14px !important;
}}

{expander} summary {{
    color: var(--dipu-azul) !important;
    font-weight: 600 !important;
}}

/* ==================================================================
   RESPONSIVE — CELULAR (hasta 640px)
   Todos los selectores van acotados a su contenedor: nunca globales.
   ================================================================== */
@media (max-width: 640px) {{

    /* Márgenes laterales más finos para ganar ancho de lectura */
    {top_bg} {{
        padding-left: 0.9rem !important;
        padding-right: 0.9rem !important;
        padding-top: 2.5rem !important;
    }}

    /* Logo del título: se achica y sigue centrado */
    {main_title} {{
        max-width: 14rem !important;
        height: 3.2rem !important;
    }}

    {subtitle} p {{
        font-size: 0.85rem !important;
    }}

    /* Burbuja del usuario: puede ocupar más ancho en pantalla angosta */
    {chat_bubble_user_inner} {{
        max-width: 88% !important;
        padding: 0.55rem 0.95rem !important;
    }}

    {chat_bubble_bot_inner} p {{
        font-size: 0.95rem !important;
        line-height: 1.55 !important;
    }}

    /* Botones de prompts: ancho completo y apilados, como en el frame.
       En celular las columnas de Streamlit quedan muy angostas. */
    {main_div} div.stButton > button {{
        width: 100% !important;
        text-align: left !important;
        padding: 0.6rem 1rem !important;
        font-size: 0.9rem !important;
    }}

    /* Las columnas de sugerencias se apilan una debajo de otra */
    {main_div} div[data-testid="stHorizontalBlock"] {{
        flex-direction: column !important;
        gap: 0.5rem !important;
    }}

    {main_div} div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }}

    /* Input: un poco más compacto y pegado a los bordes */
    {chat_input_bg} {{
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }}

    {chat_input} {{
        border-radius: 26px !important;
    }}

    {chat_input} textarea {{
        font-size: 16px !important; /* evita el zoom automático de iOS */
    }}

    /* Sidebar: ocupa casi toda la pantalla al abrirse */
    section[data-testid="stSidebar"] {{
        width: 85vw !important;
        min-width: 85vw !important;
    }}

    {sidebar} a[data-testid="stSidebarNavLink"] {{
        padding: 0.55rem 1rem !important;
    }}

    /* El expander de fuentes: texto más chico para que no desborde */
    {expander} summary {{
        font-size: 0.9rem !important;
    }}

    {expander} p, {expander} li {{
        font-size: 0.85rem !important;
        word-break: break-word !important;
    }}
}}

/* Pantallas muy angostas (hasta 400px) */
@media (max-width: 400px) {{
    {main_title} {{
        max-width: 11.5rem !important;
        height: 2.7rem !important;
    }}

    {chat_bubble_user_inner} {{
        max-width: 92% !important;
    }}

    {top_bg} {{
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }}
}}
</style>
""")

    if main:
        avatar_assistant_svg_encoded = get_encoded_svg("assets/svg/quirqui-01.svg")
        title_svg_encoded = get_encoded_svg("assets/svg/titulo-01.svg")
        st.html(f"""
<style>
{main_title} {{
    background-image: url("data:image/svg+xml;base64,{title_svg_encoded}");
}}

{avatar_bot_inside} {{
    background-image: url("data:image/svg+xml;base64,{avatar_assistant_svg_encoded}");
    background-size: contain;
    background-repeat: no-repeat;
    width: 21px;
    height: 21px;
    /* margin-right: 10px; */
    flex-shrink: 0;

    /* Hide the text. */
    text-indent: 100%;
    white-space: nowrap;
    overflow: hidden;
}}
</style>
""")

def add_js() -> None:
    st.html("""
<script>
    function change_app_name() {
        document.querySelectorAll('a[data-testid="stSidebarNavLink"] > span')
            .forEach(span => {
                if (span.textContent.trim() === 'streamlit_app' || span.textContent.trim() === 'streamlit app') {
                    span.innerHTML = 'DipuBot';
                }
            });
    }

    function on_dom_loader(cb) {
        console.log("Running that");
        if (document.readyState === "complete") {
            cb();
        } else {
            window.addEventListener("load", cb);
        }
    }

    on_dom_loader(change_app_name);
</script>
""", unsafe_allow_javascript=True)
