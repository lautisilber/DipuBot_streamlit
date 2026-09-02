import streamlit as st

from css.streamlit_css import add_css, add_js, get_encoded_svg, get_encoded_png

add_css()
add_js()

st.set_page_config(
    page_title="DipuBot | ┬┐Qu├® es DipuBot?",
    page_icon="assets/svg/quirqui-01.svg",
    layout="centered"
)

st.title("┬┐Qu├® es DipuBot?")
# st.caption("Consult├í sobre legislaci├│n argentina")
st.logo("assets/svg/quirqui-01.svg")

st.markdown("""
DipuBot es un chatbot impulsado por inteligencia artificial, **alimentado ├║nicamente con la base de datos
oficial del Congreso Nacional de Argentina.** Actualmente incluye ├║nicamente leyes aprobadas entre 1997 y 2025.
DipuBot te **brinda informaci├│n resumida, clara y f├ícil de entender sobre la actividad legislativa.**

La idea no es que DipuBot determine por vos qu├® representa cada una de estas corrientes, sino que puedas informarte
sobre lo que ocurre en la legislatura y saques tus propias conclusiones.

En este momento, DipuBot est├í en proceso de expansi├│n y, con el tiempo, llegar├í a cubrir toda la informaci├│n disponible
en la base de datos del Congreso, que se remonta a 1984.

## Manual de uso

DipuBot solo sabe lo que figura en esta base oficial: el **trabajo legislativo del Congreso Nacional**. **No** incluye
informaci├│n provincial ni de los poderes Ejecutivo o Judicial. **Tampoco tiene acceso a lo que los pol├¡ticos hacen o
dicen por fuera del Congreso**, no sabe qu├® pueden llegar a opinar en un medio de comunicaci├│n o qu├® dicen los medios
sobre ellos. **Conoce solamente los nombres oficiales de los partidos y las personas**. Si us├ís apodos no podr├í descifrar
de qui├®n est├ís hablando.

Al preguntarle sobre presidentes o ex-presidentes, contestar├í en base a sus acciones como legisladores. Si un ex presidente
nunca fue legislador, probablemente DipuBot no pueda decirte mucho sobre ├®l/ella.

T├®rminos como ÔÇ£peronismoÔÇØ, ÔÇ£radicalismoÔÇØ, ÔÇ£kirchnerismoÔÇØ o ÔÇ£liberalismoÔÇØ son complejos de definir y clasificar, por lo que
es probable que DipuBot tampoco pueda hacerlo con precisi├│n.

## ┬┐Qui├®nes somos?

Somos un equipo joven e interdisciplinario, integrado por personas de distintas regiones del pa├¡s comprometidas con el
fortalecimiento del sistema democr├ítico. Contamos con formaci├│n nacional e internacional, tanto en instituciones p├║blicas
como privadas, en el ├ímbito de las ciencias sociales y las ciencias exactas. Creemos en el valor de la diversidad y del
di├ílogo para construir una Argentina m├ís democr├ítica. A trav├®s de DipuBot, **extendemos el acceso a informaci├│n precisa y
verificada** a la ciudadan├¡a, base fundamental para aumentar el compromiso pol├¡tico y fomentar un debate p├║blico responsable
con los marcos democr├íticos.
""")

st.markdown("""
## Co-fundadores

**Juana Perdomenico**: Licenciada en Relaciones Internacionales por la Universidad Torcuato Di Tella, Maestranda en Pol├¡ticas P├║blicas en la Universidad Sciences Po, Francia. Ex pasante del Parlamento Alem├ín (Internationales Parlaments-Stipendium) y de la Deutsche Gesellschaft f├╝r Internationale Zusammenarbeit (GIZ), Alemania (2024-2025). Alumni del programa J├│venes L├¡deres Iberoamericanos 2025 por la Fundaci├│n Carolina.

[juanaperdomenico@hotmail.com](mailto:juanaperdomenico@hotmail.com)

[https://www.linkedin.com/in/juana-perdomenico](https://www.linkedin.com/in/juana-perdomenico/)
<br>
<br>

**Victoria Mi├▒o**: Licenciada en Ciencia Pol├¡tica por la Universidad Nacional de Rosario (UNR), becaria doctoral de CONICET en Ciencia Pol├¡tica (UNR), ex becaria  EVC-CIN. Alumni del programa J├│venes L├¡deres Iberoamericanos 2025 por la Fundaci├│n Carolina.

[victoria.smg01@gmail.com](mailto:victoria.smg01@gmail.com)

[https://www.linkedin.com/in/victoriaminio](https://www.linkedin.com/in/victoriaminio/)
<br>
<br>

**Miranda Gonzalez Wicky**: Tesista de la Licenciatura en Antropolog├¡a Social y Cultural en la Universidad Nacional de San Mart├¡n. Becaria EVC-CIN, ERASMUS+ y Delegada Joven en el Foro Mundial por la Democracia (Consejo de Europa, Francia 2024).

[mirandagonzalezwicky@gmail.com](mailto:mirandagonzalezwicky@gmail.com)

[https://www.linkedin.com/in/miranda-gonzalez-wicky-645147222](https://www.linkedin.com/in/miranda-gonzalez-wicky-645147222/)
<br>
<br>

**Lautaro Silbergleit**: Licenciado en F├¡sica por la Universidad de Buenos Aires, doctorando en F├¡sica por la Universidad de Chicago Illinois. Programador y ex-investigador estudiante en la Universidad de Humboldt (Alemania, 2025) en el ├írea de f├¡sica cu├íntica.

[lautisilbergleit@gmail.com](mailto:lautisilbergleit@gmail.com)

[https://www.linkedin.com/in/lautaro-silbergleit-182b31225](https://www.linkedin.com/in/lautaro-silbergleit-182b31225/)

<hr>
""", unsafe_allow_html=True)

st.markdown(f"""
Este proyecto es financiado por el Fondo Democr├íTICa, un programa de Digital Democracy Initiative (DDI) implementado por Wingu, Civic House y Kubadili, con el apoyo de CIVICUS.

<style>
.logo-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    padding: 1rem;
}}

.logo-item {{
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 1rem;
    aspect-ratio: 1 / 1;
}}

.logo-item img, .logo-item svg {{
    max-width: 100%;
    max-height: 100%;
    height: auto;
    object-fit: contain;
}}

</style>
<div class="logo-grid">
    <div class="logo-item">
        <a href="https://www.democratica.digital">
        <img src="data:image/svg+xml;base64,{get_encoded_svg("assets/extra/DemocraTICa_logo.svg")}" alt="Democr├íTICa" width="500.68" height="56.29">
        </a>
    </div>
    <div class="logo-item">
        <a href="https://www.civicus.org">
        <img src="data:image/svg+xml;base64,{get_encoded_svg("assets/extra/CIVICUS_logo.svg")}" alt="CIVICUS" width="595.28" height="539.131">
        </a>
    </div>
    <div class="logo-item">
        <a href="https://digitaldemocracyinitiative.net">
            <img src="data:image/png;base64,{get_encoded_png("assets/extra/DDI_logo.png")}" alt="Company Three Logo">
        </a>
    </div>
</div>


""", unsafe_allow_html=True)
