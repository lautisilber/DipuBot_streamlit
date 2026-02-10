import streamlit as st

from css.streamlit_css import add_css, add_js

add_css()
add_js()

st.set_page_config(
    page_title="DipuBot | ¿Cómo funciona el poder legislativo?",
    page_icon="assets/svg/quirqui-01.svg",
    layout="centered"
)

st.title("¿Cómo funciona el poder legislativo?")
# st.caption("Consultá sobre legislación argentina")
st.logo("assets/svg/quirqui-01.svg")

st.markdown("""

## ¿Qué hace un legislador? ¿Cuáles son sus obligaciones?

La función principal de los legisladores es **debatir, elaborar y sancionar leyes que regulen distintos aspectos de la vida
del país.** También pueden modificar o derogar leyes ya existentes.

Además de dictar leyes, los legisladores tienen la **responsabilidad de representar a la ciudadanía**, participar en las
comisiones donde se analizan los proyectos y votar en el recinto.

Otra de sus funciones centrales es ejercer el **control sobre el Poder Ejecutivo**. Esto incluye, entre otras herramientas,
el pedido de informes, las interpelaciones a funcionarios, el trabajo de la Auditoría General de la Nación —que depende del
Congreso—, la posibilidad de impulsar juicios políticos, etc.

**Sus actuaciones están limitadas por la Constitución:** no pueden legislar sobre materias que no sean de competencia del
Congreso ni modificar lo que la propia Constitución establece.

## Diferencia entre diputado y senador

El Congreso Nacional está compuesto por dos cámaras: la de Diputados y la de Senadores. Si bien ambas cámaras se fundan a
partir de las votaciones, **los diputados representan directamente al pueblo argentino y los senadores a las provincias y a
la Ciudad de Buenos Aires.** La Cámara de Senadores tienese encuentra compuesta por 72 senadores, a razón de tres por cada
provincia y tres por la Ciudad de Buenos Aires. La Cámara de Diputados, por su parte, está compuesta por 257 diputados
elegidos directamente por el pueblo; el número de diputados por distrito es proporcional a su población.

Conforme a la Constitución, estos son los **deberes de cada cámara**:

#### Diputados:
- **Recibir los proyectos de Ley presentados por iniciativa popular** (CN Art.39)
- Iniciar el **proceso de consulta popular para un proyecto de ley** (CN Art. 40)
- **Iniciar las leyes** sobre contribuciones y reclutamiento de tropas (CN Art. 52)
- Acusar ante el Senado, en juicio político, al presidente y vicepresidente de la Nación, al jefe de Gabinete de ministros, a ministros del Poder Ejecutivo y a miembros de la Corte Suprema (CN Art. 53)

#### Senadores:
- Juzgar en juicio político a los acusados por la Cámara de Diputados (CN Art. 59)
- Autorizar al presidente de la Nación para que declare el estado de sitio en caso de ataque exterior (CN Art. 61)
- Ser cámara de origen en la Ley Convenio, sobre coparticipación federal de impuestos (CN Art. 75 Inc. 2)
- Ser cámara de origen de leyes que promuevan políticas tendientes al crecimiento armónico de la Nación y el poblamiento de su territorio (CN Art. 75 Inc. 19)
- Prestar acuerdo al Poder Ejecutivo para la designación de magistrados judiciales, embajadores, ministros plenipotenciarios, encargados de negocios y de oficiales superiores de las Fuerzas Armadas (CN Art. 99 Inc. 4, 7 y 13)

## Cómo se hace, se edita y se amplía una ley

La “iniciativa legislativa”, es decir la facultad de presentar proyectos de ley, corresponde a los diputados, senadores y al
presidente de la Nación. La última reforma constitucional de 1994 incorporó también el derecho de “iniciativa popular”, que
permite a los ciudadanos presentar proyectos de ley ante la Cámara de Diputados, siempre que cumplan con los requisitos que
determina la ley. Si un proyecto ingresa al Congreso por la Cámara de Diputados, esta se convierte en la cámara de origen del
proyecto y el Senado pasa a ser la cámara revisora. Cuando un proyecto se presenta en el Senado, este se convierte en cámara
de origen y la Cámara de Diputados, en cámara revisora.

Las etapas para elaborar una Ley en democracia son las siguientes:
1) **Presentación de un proyecto** en mesa de entradas de la Cámara de Diputados o del Senado.
2) **Tratamiento en comisiones.** El proyecto pasa a una o más comisiones de asesoramiento, que emiten un dictamen. En ocasiones, frente a temas de gran urgencia o relevancia, un proyecto puede ser tratado “sobre tablas” en el recinto sin que haya pasado previamente por las comisiones.
3) **Debate parlamentario en ambas cámaras.**
""")

st.markdown("""
    | 1° Cámara de origen | 2° Cámara revisora | 3° Resultado |
    |----------|----------|----------|
    | Aprueba el proyecto | Aprueba el proyecto | Se sanciona el proyecto aprobado por la cámara de origen |
    | Aprueba el proyecto | Rechaza (desecha) el proyecto | El proyecto no puede volver a tratarse en las sesiones de ese año |
    | Rechaza (desecha) el proyecto |  | El proyecto no puede volver a tratarse en las sesiones de ese año |
    | Aprueba el proyecto | Adiciona o corrige (por mayoría absoluta  o por 2/3 de los votos) | Vuelve a la cámara de origen. <br> &rarr; Si la cámara de origen acepta las modificaciones, se sanciona el texto aprobado en la cámara revisora. <br> &rarr; Si la cámara de origen insiste en la redacción originaria, se necesita alcanzar la misma mayoría o una superior que la de la cámara revisora para que se sancione como ley el texto originalmente aprobado. En el caso de no lograrlo queda sancionado el texto aprobado en la cámara revisora. <br> <small>(En ningún caso podrá la cámara de origen desechar totalmente los proyectos modificados por la cámara revisora ni introducir nuevas adiciones o correcciones)</small> |
""", unsafe_allow_html=True)

st.markdown("""
Un proyecto de ley aprobado en la cámara de origen pasa luego a ser discutido en la cámara revisora, que lo puede aprobar,
rechazar o devolver con sus correcciones.

Una vez que la Cámara de Senadores y la Cámara de Diputados sancionan un proyecto
de ley, esta pasa al Poder Ejecutivo.

El presidente de la Nación puede:
- **Aprobar y promulgar la ley.** Se completa así el proceso legislativo. Esto lo puede hacer por medio de un decreto o bien
“promulgación de hecho”, ya que si el presidente no se pronuncia pasados diez días hábiles desde que se le comunicó la norma
se promulga automáticamente. En ambos casos, la ley se publica luego en el Boletín Oficial y entra en vigencia de acuerdo con
los plazos legales.
- **Vetar la ley**, de forma total o parcial. En caso de veto parcial, puede promulgar parcialmente la parte no vetada cuando
no desvirtúe el espíritu del proyecto sancionado por el Congreso.

En caso de que el presidente vete la ley, el proyecto vuelve al Poder Legislativo, que puede aceptar el veto o insistir en su
sanción. Si ambas cámaras cuentan con dos tercios de los votos para imponer su criterio inicial, la ley se promulga, aunque el
presidente no esté de acuerdo. Si no lo consiguen, se mantiene el veto del presidente y el proyecto no puede volver a tratarse
en las sesiones de ese año.

#### Insistencia del poder Legislativo

""")

st.markdown("""
| Poder Ejecutivo | Cámara Legislativa Iniciadora | Cámara Legislativa Revisora | Promulgación |
|----------|----------|----------|----------|
| Veta | **Confirma la ley** <br> Cuenta con 2/3 de los votos para insistir en la sanción de las cámaras | **Confirma la ley** <br> Cuenta con 2/3 de los votos para insistir en la sanción de las cámaras | Sí |
| Veta | **No confirma la ley** <br> No cuenta con los 2/3 de los votos | No puede tratarse en las sesiones de este año | Se mantiene el veto |
| Veta | **Confirma la ley** <br> Cuenta con 2/3 de los votos para insistir en la sanción de las cámaras | **No confirma la ley** <br> No cuenta con 2/3 de los votos para insistir en la sanción de las cámaras | Se mantiene el veto |

""", unsafe_allow_html=True)

st.markdown("""
## ¿Cómo se deroga una ley?

La derogación ocurre cuando una nueva ley elimina una parte o la totalidad de una disposición normativa previgente.

## ¿Cómo se hace un decreto?

El Jefe de Gabinete debe comunicar al Congreso de la Nación los decretos delegados y los de necesidad y urgencia que se emiten
y este debe controlar si se cumplieron los requisitos que establece la Constitución. La Comisión Bicameral Permanente tiene que
expedirse y elevar el dictamen al plenario de cada una de las Cámaras para su tratamiento.

Los decretos de necesidad y urgencia deben ser firmados por el Presidente, el Jefe de Gabinete y todos los ministros. Los
delegados no requieren la firma de los ministros. Además, cuando se emite un decreto de necesidad y urgencia debe decir que
se funda en el art. 99 inciso 3º de la Constitución Nacional. En el caso de los delegados, aclarar que se funda en la ley
que delegó las facultades legislativas y en el art. 76 de la Constitución Nacional.

## ¿Cómo funcionan las elecciones?

En Argentina tenemos elecciones legislativas cada dos años y elecciones presidenciales, cada cuatro. **La Cámara de Diputados
se renueva en mitades y la de Senadores en tercios**. Esto significa que después de cada elección legislativa cambian
solamente la mitad de los diputados y un tercio de los senadores. Una vez electos, los diputados tienen un mandato de
cuatro años y los senadores, de seis. Ambos tienen la posibilidad de ser reelegidos.

A diferencia de otros países, en Argentina se vota por lista o partido, en lugar de elegir directamente al candidato.
Esto significa que los ciudadanos votan por un partido que previamente decidió quiénes serán sus candidatos al Congreso y
en qué orden entrarán.

## ¿Cuál es la diferencia entre el Congreso Nacional y las legislaturas provinciales?

El Congreso Nacional representa a toda la Argentina y sanciona leyes que aplican a toda la nación. Las legislaturas
provinciales representan a una única provincia y sancionan leyes que solo aplican a esa provincia. Cada provincia
tiene su propia legislatura, incluyendo la Ciudad de Buenos Aires, que tiene una legislatura separada a la de la
provincia. Las legislaturas provinciales no siempre se componen como la nacional. Hay algunas provincias, como Córdoba
o Chubut, que solo tienen una cámara en lugar de dos.

## ¿Quiénes son los diputados y senadores hoy?

La lista oficial de **diputados nacionales** se puede encontrar en
[https://www.diputados.gov.ar/diputados](https://www.diputados.gov.ar/diputados/) Y la lista oficial de **senadores nacionales** en
[https://www.senado.gob.ar/senadores/listados/listaSenadoRes](https://www.senado.gob.ar/senadores/listados/listaSenadoRes)

## ¿Cuáles son los partidos y bloques actuales?

Cuando pensamos en política muchos pensamos solo en los partidos más famosos, como el peronismo o los libertarios.
Pero en la práctica estos no son los únicos partidos en el Congreso y tampoco se llaman oficialmente “peronismo” o
“libertarios”. Para poder recibir las mejores respuesta de DipuBot, es importante saber cómo se llaman los partidos y
los bloques.

Estos son los partidos en la **Cámara de Diputados**:

| Partido | Cantidad de integrantes |
|---------|-------------------------|
| La Libertad Avanza | 95 |
| Unión por la Patria | 93 |
| Provincias Unidas | 18 |
| PRO | 12 |
| Innovación Federal | 7 |
| Unión Cívica Radical | 6 |
| Frente de Izquierda y de Trabajadores Unidad | 4 |
| Elijo Catamarca | 3 |
| Independencia | 3 |
| Coalición Cívica | 2 |
| Encuentro Federal | 2 |
| MID - Movimiento de Integración y Desarrollo | 2 |
| País Federal | 2 |
| Producción y Trabajo | 2 |
| Adelante Buenos Aires | 1 |
| Coherencia | 1 |
| Defendamos Córdoba | 1 |
| La Neuquenidad | 1 |
| Por Santa Cruz | 1 |
| Primero San Luis | 1 |

Si querés saber qué diputados están en cada bloque, podes chequear la página oficial:
    [https://www.diputados.gov.ar/diputados/diputados-por-bloque.html](https://www.diputados.gov.ar/diputados/diputados-por-bloque.html)

Estos son los partidos en el **Senado**:

| Partido | Cantidad de senadores |
|---------|-----------------------|
| Justicialista | 21 |
| La Libertad Avanza | 20 |
| Unión Cívica Radical | 10 |
| Convicción Federal | 5 |
| Frente PRO | 3 |
| Frente Cívico por Santiago | 2 |
| Frente Renovador de la Concordia Social | 2 |
| Movere por Santa Cruz | 2 |
| Provincias Unidas | 2 |
| Despierta Chubut | 1 |
| Frente Cívico de Córdoba | 1 |
| Independencia | 1 |
| La Neuquenidad | 1 |
| Primero los Salteños | 1 |

¿Querés saber más sobre quiénes forman parte de cada partido? Mirá la página oficial:
[https://www.senado.gob.ar/senadores/listados/agrupados-por-bloques](https://www.senado.gob.ar/senadores/listados/agrupados-por-bloques)

## ¿Querés saber más?

**Chequeá la página oficial del Congreso:**
[https://www.diputados.gob.ar/congreso_explicado](https://www.diputados.gob.ar/congreso_explicado/)

""")
