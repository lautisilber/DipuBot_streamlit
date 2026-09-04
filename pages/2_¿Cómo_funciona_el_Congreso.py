import streamlit as st

from css.streamlit_css import add_css, add_js

add_css()
add_js()

st.set_page_config(
    page_title="DipuBot | ┬┐C├│mo funciona el poder legislativo?",
    page_icon="assets/svg/quirqui-01.svg",
    layout="centered"
)

st.title("┬┐C├│mo funciona el poder legislativo?")
# st.caption("Consult├í sobre legislaci├│n argentina")
st.logo("assets/svg/quirqui-02.svg")

st.markdown("""

## ┬┐Qu├® hace un legislador? ┬┐Cu├íles son sus obligaciones?

La funci├│n principal de los legisladores es **debatir, elaborar y sancionar leyes que regulen distintos aspectos de la vida
del pa├¡s.** Tambi├®n pueden modificar o derogar leyes ya existentes.

Adem├ís de dictar leyes, los legisladores tienen la **responsabilidad de representar a la ciudadan├¡a**, participar en las
comisiones donde se analizan los proyectos y votar en el recinto.

Otra de sus funciones centrales es ejercer el **control sobre el Poder Ejecutivo**. Esto incluye, entre otras herramientas,
el pedido de informes, las interpelaciones a funcionarios, el trabajo de la Auditor├¡a General de la Naci├│n ÔÇöque depende del
CongresoÔÇö, la posibilidad de impulsar juicios pol├¡ticos, etc.

**Sus actuaciones est├ín limitadas por la Constituci├│n:** no pueden legislar sobre materias que no sean de competencia del
Congreso ni modificar lo que la propia Constituci├│n establece.

## Diferencia entre diputado y senador

El Congreso Nacional est├í compuesto por dos c├ímaras: la de Diputados y la de Senadores. Si bien ambas c├ímaras se fundan a
partir de las votaciones, **los diputados representan directamente al pueblo argentino y los senadores a las provincias y a
la Ciudad de Buenos Aires.** La C├ímara de Senadores tienese encuentra compuesta por 72 senadores, a raz├│n de tres por cada
provincia y tres por la Ciudad de Buenos Aires. La C├ímara de Diputados, por su parte, est├í compuesta por 257 diputados
elegidos directamente por el pueblo; el n├║mero de diputados por distrito es proporcional a su poblaci├│n.

Conforme a la Constituci├│n, estos son los **deberes de cada c├ímara**:

#### Diputados:
- **Recibir los proyectos de Ley presentados por iniciativa popular** (CN Art.39)
- Iniciar el **proceso de consulta popular para un proyecto de ley** (CN Art. 40)
- **Iniciar las leyes** sobre contribuciones y reclutamiento de tropas (CN Art. 52)
- Acusar ante el Senado, en juicio pol├¡tico, al presidente y vicepresidente de la Naci├│n, al jefe de Gabinete de ministros, a ministros del Poder Ejecutivo y a miembros de la Corte Suprema (CN Art. 53)

#### Senadores:
- Juzgar en juicio pol├¡tico a los acusados por la C├ímara de Diputados (CN Art. 59)
- Autorizar al presidente de la Naci├│n para que declare el estado de sitio en caso de ataque exterior (CN Art. 61)
- Ser c├ímara de origen en la Ley Convenio, sobre coparticipaci├│n federal de impuestos (CN Art. 75 Inc. 2)
- Ser c├ímara de origen de leyes que promuevan pol├¡ticas tendientes al crecimiento arm├│nico de la Naci├│n y el poblamiento de su territorio (CN Art. 75 Inc. 19)
- Prestar acuerdo al Poder Ejecutivo para la designaci├│n de magistrados judiciales, embajadores, ministros plenipotenciarios, encargados de negocios y de oficiales superiores de las Fuerzas Armadas (CN Art. 99 Inc. 4, 7 y 13)

## C├│mo se hace, se edita y se ampl├¡a una ley

La ÔÇ£iniciativa legislativaÔÇØ, es decir la facultad de presentar proyectos de ley, corresponde a los diputados, senadores y al
presidente de la Naci├│n. La ├║ltima reforma constitucional de 1994 incorpor├│ tambi├®n el derecho de ÔÇ£iniciativa popularÔÇØ, que
permite a los ciudadanos presentar proyectos de ley ante la C├ímara de Diputados, siempre que cumplan con los requisitos que
determina la ley. Si un proyecto ingresa al Congreso por la C├ímara de Diputados, esta se convierte en la c├ímara de origen del
proyecto y el Senado pasa a ser la c├ímara revisora. Cuando un proyecto se presenta en el Senado, este se convierte en c├ímara
de origen y la C├ímara de Diputados, en c├ímara revisora.

Las etapas para elaborar una Ley en democracia son las siguientes:
1) **Presentaci├│n de un proyecto** en mesa de entradas de la C├ímara de Diputados o del Senado.
2) **Tratamiento en comisiones.** El proyecto pasa a una o m├ís comisiones de asesoramiento, que emiten un dictamen. En ocasiones, frente a temas de gran urgencia o relevancia, un proyecto puede ser tratado ÔÇ£sobre tablasÔÇØ en el recinto sin que haya pasado previamente por las comisiones.
3) **Debate parlamentario en ambas c├ímaras.**
""")

st.markdown("""
    | 1┬░ C├ímara de origen | 2┬░ C├ímara revisora | 3┬░ Resultado |
    |----------|----------|----------|
    | Aprueba el proyecto | Aprueba el proyecto | Se sanciona el proyecto aprobado por la c├ímara de origen |
    | Aprueba el proyecto | Rechaza (desecha) el proyecto | El proyecto no puede volver a tratarse en las sesiones de ese a├▒o |
    | Rechaza (desecha) el proyecto |  | El proyecto no puede volver a tratarse en las sesiones de ese a├▒o |
    | Aprueba el proyecto | Adiciona o corrige (por mayor├¡a absoluta  o por 2/3 de los votos) | Vuelve a la c├ímara de origen. <br> &rarr; Si la c├ímara de origen acepta las modificaciones, se sanciona el texto aprobado en la c├ímara revisora. <br> &rarr; Si la c├ímara de origen insiste en la redacci├│n originaria, se necesita alcanzar la misma mayor├¡a o una superior que la de la c├ímara revisora para que se sancione como ley el texto originalmente aprobado. En el caso de no lograrlo queda sancionado el texto aprobado en la c├ímara revisora. <br> <small>(En ning├║n caso podr├í la c├ímara de origen desechar totalmente los proyectos modificados por la c├ímara revisora ni introducir nuevas adiciones o correcciones)</small> |
""", unsafe_allow_html=True)

st.markdown("""
Un proyecto de ley aprobado en la c├ímara de origen pasa luego a ser discutido en la c├ímara revisora, que lo puede aprobar,
rechazar o devolver con sus correcciones.

Una vez que la C├ímara de Senadores y la C├ímara de Diputados sancionan un proyecto
de ley, esta pasa al Poder Ejecutivo.

El presidente de la Naci├│n puede:
- **Aprobar y promulgar la ley.** Se completa as├¡ el proceso legislativo. Esto lo puede hacer por medio de un decreto o bien
ÔÇ£promulgaci├│n de hechoÔÇØ, ya que si el presidente no se pronuncia pasados diez d├¡as h├íbiles desde que se le comunic├│ la norma
se promulga autom├íticamente. En ambos casos, la ley se publica luego en el Bolet├¡n Oficial y entra en vigencia de acuerdo con
los plazos legales.
- **Vetar la ley**, de forma total o parcial. En caso de veto parcial, puede promulgar parcialmente la parte no vetada cuando
no desvirt├║e el esp├¡ritu del proyecto sancionado por el Congreso.

En caso de que el presidente vete la ley, el proyecto vuelve al Poder Legislativo, que puede aceptar el veto o insistir en su
sanci├│n. Si ambas c├ímaras cuentan con dos tercios de los votos para imponer su criterio inicial, la ley se promulga, aunque el
presidente no est├® de acuerdo. Si no lo consiguen, se mantiene el veto del presidente y el proyecto no puede volver a tratarse
en las sesiones de ese a├▒o.

#### Insistencia del poder Legislativo

""")

st.markdown("""
| Poder Ejecutivo | C├ímara Legislativa Iniciadora | C├ímara Legislativa Revisora | Promulgaci├│n |
|----------|----------|----------|----------|
| Veta | **Confirma la ley** <br> Cuenta con 2/3 de los votos para insistir en la sanci├│n de las c├ímaras | **Confirma la ley** <br> Cuenta con 2/3 de los votos para insistir en la sanci├│n de las c├ímaras | S├¡ |
| Veta | **No confirma la ley** <br> No cuenta con los 2/3 de los votos | No puede tratarse en las sesiones de este a├▒o | Se mantiene el veto |
| Veta | **Confirma la ley** <br> Cuenta con 2/3 de los votos para insistir en la sanci├│n de las c├ímaras | **No confirma la ley** <br> No cuenta con 2/3 de los votos para insistir en la sanci├│n de las c├ímaras | Se mantiene el veto |

""", unsafe_allow_html=True)

st.markdown("""
## ┬┐C├│mo se deroga una ley?

La derogaci├│n ocurre cuando una nueva ley elimina una parte o la totalidad de una disposici├│n normativa previgente.

## ┬┐C├│mo se hace un decreto?

El Jefe de Gabinete debe comunicar al Congreso de la Naci├│n los decretos delegados y los de necesidad y urgencia que se emiten
y este debe controlar si se cumplieron los requisitos que establece la Constituci├│n. La Comisi├│n Bicameral Permanente tiene que
expedirse y elevar el dictamen al plenario de cada una de las C├ímaras para su tratamiento.

Los decretos de necesidad y urgencia deben ser firmados por el Presidente, el Jefe de Gabinete y todos los ministros. Los
delegados no requieren la firma de los ministros. Adem├ís, cuando se emite un decreto de necesidad y urgencia debe decir que
se funda en el art. 99 inciso 3┬║ de la Constituci├│n Nacional. En el caso de los delegados, aclarar que se funda en la ley
que deleg├│ las facultades legislativas y en el art. 76 de la Constituci├│n Nacional.

## ┬┐C├│mo funcionan las elecciones?

En Argentina tenemos elecciones legislativas cada dos a├▒os y elecciones presidenciales, cada cuatro. **La C├ímara de Diputados
se renueva en mitades y la de Senadores en tercios**. Esto significa que despu├®s de cada elecci├│n legislativa cambian
solamente la mitad de los diputados y un tercio de los senadores. Una vez electos, los diputados tienen un mandato de
cuatro a├▒os y los senadores, de seis. Ambos tienen la posibilidad de ser reelegidos.

A diferencia de otros pa├¡ses, en Argentina se vota por lista o partido, en lugar de elegir directamente al candidato.
Esto significa que los ciudadanos votan por un partido que previamente decidi├│ qui├®nes ser├ín sus candidatos al Congreso y
en qu├® orden entrar├ín.

## ┬┐Cu├íl es la diferencia entre el Congreso Nacional y las legislaturas provinciales?

El Congreso Nacional representa a toda la Argentina y sanciona leyes que aplican a toda la naci├│n. Las legislaturas
provinciales representan a una ├║nica provincia y sancionan leyes que solo aplican a esa provincia. Cada provincia
tiene su propia legislatura, incluyendo la Ciudad de Buenos Aires, que tiene una legislatura separada a la de la
provincia. Las legislaturas provinciales no siempre se componen como la nacional. Hay algunas provincias, como C├│rdoba
o Chubut, que solo tienen una c├ímara en lugar de dos.

## ┬┐Qui├®nes son los diputados y senadores hoy?

La lista oficial de **diputados nacionales** se puede encontrar en
[https://www.diputados.gov.ar/diputados](https://www.diputados.gov.ar/diputados/) Y la lista oficial de **senadores nacionales** en
[https://www.senado.gob.ar/senadores/listados/listaSenadoRes](https://www.senado.gob.ar/senadores/listados/listaSenadoRes)

## ┬┐Cu├íles son los partidos y bloques actuales?

Cuando pensamos en pol├¡tica muchos pensamos solo en los partidos m├ís famosos, como el peronismo o los libertarios.
Pero en la pr├íctica estos no son los ├║nicos partidos en el Congreso y tampoco se llaman oficialmente ÔÇ£peronismoÔÇØ o
ÔÇ£libertariosÔÇØ. Para poder recibir las mejores respuesta de DipuBot, es importante saber c├│mo se llaman los partidos y
los bloques.

Estos son los partidos en la **C├ímara de Diputados**:

| Partido | Cantidad de integrantes |
|---------|-------------------------|
| La Libertad Avanza | 95 |
| Uni├│n por la Patria | 93 |
| Provincias Unidas | 18 |
| PRO | 12 |
| Innovaci├│n Federal | 7 |
| Uni├│n C├¡vica Radical | 6 |
| Frente de Izquierda y de Trabajadores Unidad | 4 |
| Elijo Catamarca | 3 |
| Independencia | 3 |
| Coalici├│n C├¡vica | 2 |
| Encuentro Federal | 2 |
| MID - Movimiento de Integraci├│n y Desarrollo | 2 |
| Pa├¡s Federal | 2 |
| Producci├│n y Trabajo | 2 |
| Adelante Buenos Aires | 1 |
| Coherencia | 1 |
| Defendamos C├│rdoba | 1 |
| La Neuquenidad | 1 |
| Por Santa Cruz | 1 |
| Primero San Luis | 1 |

Si quer├®s saber qu├® diputados est├ín en cada bloque, podes chequear la p├ígina oficial:
    [https://www.diputados.gov.ar/diputados/diputados-por-bloque.html](https://www.diputados.gov.ar/diputados/diputados-por-bloque.html)

Estos son los partidos en el **Senado**:

| Partido | Cantidad de senadores |
|---------|-----------------------|
| Justicialista | 21 |
| La Libertad Avanza | 20 |
| Uni├│n C├¡vica Radical | 10 |
| Convicci├│n Federal | 5 |
| Frente PRO | 3 |
| Frente C├¡vico por Santiago | 2 |
| Frente Renovador de la Concordia Social | 2 |
| Movere por Santa Cruz | 2 |
| Provincias Unidas | 2 |
| Despierta Chubut | 1 |
| Frente C├¡vico de C├│rdoba | 1 |
| Independencia | 1 |
| La Neuquenidad | 1 |
| Primero los Salte├▒os | 1 |

┬┐Quer├®s saber m├ís sobre qui├®nes forman parte de cada partido? Mir├í la p├ígina oficial:
[https://www.senado.gob.ar/senadores/listados/agrupados-por-bloques](https://www.senado.gob.ar/senadores/listados/agrupados-por-bloques)

## ┬┐Quer├®s saber m├ís?

**Cheque├í la p├ígina oficial del Congreso:**
[https://www.diputados.gob.ar/congreso_explicado](https://www.diputados.gob.ar/congreso_explicado/)

""")
