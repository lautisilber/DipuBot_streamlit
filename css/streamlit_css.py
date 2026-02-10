import streamlit as st

from pathlib import Path
import base64

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

    bg_svg_encoded = get_encoded_svg("assets/svg/fondo-06.svg")

    st.html(
f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap" rel="stylesheet">

<style>
html,
body,
[class*="st-"]:not([data-testid="stIconMaterial"]) {{
  font-family: "Space Grotesk", sans-serif !important;
}}

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

{main_div} {{
    background-image: url("data:image/svg+xml;base64,{bg_svg_encoded}") !important;
    background-size: cover !important;
    background-repeat: no-repeat !important;
    background-attachment: fixed !important;
    color: #1A1A2E !important;
}}

{main_div} p, {main_div} span, {main_div} li, {main_div} h1, {main_div} h2, {main_div} h3, {main_div} strong, {main_div} em, {main_div} a {{
    color: #1A1A2E !important;
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

{chat_bubble_bot} {{
    background-color: #FFFFFF !important;
    /* background-color: #FFFFFF !important; */
}}

{chat_bubble} {{
    /* background-color: #F8F9FA !important; */
    background-color: #00000000 !important;
}}

{chat_bubble_user_inner} {{
    background-color: #FEFCF1 !important;
}}

{chat_bubble_bot_inner} {{
    background-color: #F4F7FA !important;
}}
</style>
""")

    if main:
        avatar_assistant_svg_encoded = get_encoded_svg("assets/svg/quirqui-02.svg")
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
    margin-right: 10px;
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