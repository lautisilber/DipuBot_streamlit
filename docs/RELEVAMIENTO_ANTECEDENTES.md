# Relevamiento de antecedentes — DipuBot

> Documento de antecedentes del prototipo: proyectos, apps, plataformas, experiencias e iniciativas
> similares a DipuBot que sirven como referencia para **comparar, validar y mejorar** el producto.
>
> Última actualización: junio 2026 · Información verificada mediante búsqueda web.

---

## 0. Definición del prototipo (criterio de comparación)

**DipuBot** es un chatbot de IA (arquitectura RAG sobre LlamaIndex + Streamlit) alimentado *únicamente*
con la base de datos oficial del Congreso de la Nación Argentina (leyes 2023–2025, con expansión proyectada
hasta 1984). Traduce la actividad legislativa a lenguaje claro, con énfasis en **neutralidad, transparencia,
información verificada y acceso ciudadano**. Es un proyecto de sociedad civil financiado por el Fondo
DemocráTICa (DDI / Wingu / Civic House / Kubadili / CIVICUS).

Los antecedentes se ordenan por **cercanía funcional** a esa definición, en cuatro capas:

1. **Capa A — IA aplicada a datos legislativos** (lo más cercano: misma tecnología + propósito).
2. **Capa B — Plataformas de transparencia/monitoreo legislativo** (mismo propósito, sin IA generativa).
3. **Capa C — Participación y deliberación ciudadana** (propósito cívico complementario).
4. **Capa D — Marcos de referencia y RAG legal** (estándares y arquitectura comparable).

---

## Capa A · IA aplicada a datos legislativos (antecedentes directos)

### A.1 — Ulysses · Câmara dos Deputados (Brasil) ⭐ *referente regional clave*
- **Qué es:** robô digital de IA del parlamento brasileño que articula datos legislativos del portal y
  clasifica automáticamente comentarios ciudadanos sobre proyectos (hasta ~30.000 comentarios por proyecto)
  con NLP. Nueva fase con políticas de gobernanza de IA y un "Ulysses Chat" interno sobre normas y procedimientos.
- **Por qué importa para DipuBot:** es el caso más maduro de IA legislativa orientada a ciudadanía en la región;
  modelo de gobernanza, escala y código abierto (repos en GitHub `ulysses-camara`).
- **Qué tomar:** estructura de gobernanza de IA pública; clasificación de feedback ciudadano; arquitectura por capas.
- 🔗 https://www.camara.leg.br/noticias/548730-camara-lanca-ulysses-robo-digital-que-articula-dados-legislativos/
- 🔗 https://github.com/ulysses-camara

### A.2 — GOV.UK Chat (Reino Unido)
- **Qué es:** chatbot oficial del gobierno británico con **arquitectura RAG sobre el contenido de GOV.UK**,
  con datos personales removidos, para que la ciudadanía consulte obligaciones y trámites en lenguaje natural.
- **Por qué importa:** validación de que el patrón *RAG sobre corpus oficial → respuesta en lenguaje claro*
  es exactamente el de DipuBot, hecho por un gobierno a escala nacional.
- **Qué tomar:** manejo de privacidad/anonimización; gestión de alucinaciones; disclaimers de "no es asesoría".
- 🔗 https://www.theregister.com/2025/12/19/govuk_chatbot/

### A.3 — DiputadosAR · DipLab (Argentina) ⭐ *misma jurisdicción*
- **Qué es:** laboratorio de innovación de la Cámara de Diputados que expone proyectos y datos legislativos
  con herramientas digitales. Fuente **oficial primaria** y posible origen/complemento de datos de DipuBot.
- **Por qué importa:** comparte la fuente de datos; es el "competidor/colaborador" institucional directo.
- **Qué tomar:** trazabilidad al documento original; estándares de datos abiertos del HCDN.
- 🔗 https://diplab.hcdn.gob.ar/proyectos

### A.4 — Senado / Italia (casos IPU)
- **Qué es:** el Senado italiano emplea IA para consultas en lenguaje natural sobre proyectos de ley;
  caso documentado entre los 40+ "use cases" recopilados por la IPU.
- **Qué tomar:** patrón de "query en lenguaje natural sobre proyectos" en un parlamento europeo.
- 🔗 https://www.ipu.org/ai-guidelines/role-ai-in-parliaments

### A.5 — Avatares/IA de legisladores individuales (Argentina, 2025)
- **Qué es:** un diputado argentino lanzó una IA propia (basada en ChatGPT) como "representante digital".
- **Por qué importa:** **contra-ejemplo**. Es el polo opuesto a DipuBot: personalista, no neutral, sin corpus
  verificado. Útil para argumentar el diferencial de DipuBot (neutralidad, fuente oficial única, sin opinión).
- 🔗 https://www.infobae.com/politica/2025/07/07/un-diputado-creo-su-version-de-inteligencia-artificial-para-trabajar-24-horas-y-no-perder-tiempo-en-la-campana-electoral/

---

## Capa B · Transparencia y monitoreo legislativo (mismo propósito, sin IA generativa)

### B.1 — TheyWorkForYou · mySociety (Reino Unido) ⭐ *gold standard de UX cívica*
- **Qué es:** desde 2004, el primer sitio que convirtió datos parlamentarios en una herramienta para que la
  ciudadanía entienda **qué dice y cómo vota su representante**, en lenguaje simple, con alertas por email
  y por frase/tema. Hermano de **WriteToThem** (escribile a tu representante con solo el código postal).
- **Por qué importa:** referencia mundial de cómo presentar actividad legislativa de forma accesible y accionable.
- **Qué tomar:** alertas por tema; ficha por legislador; el modelo "esto es lo que hizo tu representante".
- 🔗 https://www.theyworkforyou.com/  ·  🔗 https://www.mysociety.org/category/democracy/writetothem/

### B.2 — GovTrack.us (EE.UU.)
- **Qué es:** desde 2004, seguimiento de todo el ciclo de un proyecto (de la introducción a la sanción),
  texto de las leyes, votaciones y alertas por tema/legislador. Pionero del movimiento de datos abiertos.
- **Qué tomar:** visualización del *estado/trámite* de un proyecto; seguimiento por palabra clave.
- 🔗 https://www.govtrack.us/

### B.3 — Directorio Legislativo (Argentina / regional) ⭐ *referente local de la temática*
- **Qué es:** ONG (desde 2000) que provee información sobre legisladores y funcionamiento de los congresos de
  Argentina, México y Colombia (trayectoria, gestión, comisiones, género, contacto). Publica además una
  **Guía global sobre monitoreo parlamentario con tecnología**.
- **Por qué importa:** es el actor de referencia de transparencia legislativa en Argentina; aliado o benchmark natural.
- **Qué tomar:** taxonomía de datos por legislador; la guía de monitoreo como marco metodológico.
- 🔗 https://legisladores.directoriolegislativo.org/  ·  🔗 https://directoriolegislativo.org/es/guia-global-sobre-monitoreo-parlamentario-con-tecnologia/

### B.4 — Plataforma de Información Legislativa (PIL) — Argentina (oficial)
- **Qué es:** herramienta oficial (Jefatura de Gabinete) para seguir en tiempo real las novedades y la agenda
  del Congreso Nacional, en web y móvil.
- **Qué tomar:** fuente complementaria de datos en tiempo real; comparación de "agenda" vs. "leyes sancionadas".
- 🔗 https://www.argentina.gob.ar/jefatura/secretaria-de-gabinete/asuntos-parlamentarios/plataforma-de-informacion-legislativa

### B.5 — Congreso Abierto · Fundación Ciudadanía Inteligente (Chile)
- **Qué es:** monitor del Congreso chileno donde se ven proyectos, su estado, alertas por materia de interés y
  contacto directo con el/la congresista. Misma fundación de **Vota Inteligente** (proposiciones a candidatos).
- **Qué tomar:** modelo de alertas + comunicación directa representante-ciudadano.
- 🔗 https://en.ciudadanointeligente.org/  ·  🔗 https://votainteligente.cl/

---

## Capa C · Participación y deliberación ciudadana (propósito cívico complementario)

### C.1 — DemocracyOS · Democracia en Red (Argentina) ⭐
- **Qué es:** software open-source (ONG argentina, 2014) para informar, debatir y votar propuestas o textos
  legislativos online. Usado por el Concejo de Bahía Blanca y como plataforma de consulta pública nacional.
  Evolucionó hacia **Consultas Digitales**.
- **Por qué importa:** muestra el paso de "consulta pasiva" (lo que hace DipuBot hoy) a "participación activa";
  posible dirección futura del producto.
- **Qué tomar:** módulos de deliberación/voto si DipuBot quisiera sumar participación; equipo afín (programadores + cientistas sociales).
- 🔗 https://democraciaos.org/  ·  🔗 https://github.com/DemocraciaEnRed/consultas-digitales

---

## Capa D · Marcos de referencia y RAG legal (estándares y arquitectura)

### D.1 — IPU · Guidelines for AI in Parliaments (2024) ⭐ *marco normativo de referencia*
- **Qué es:** guía de la Unión Interparlamentaria (dic. 2024) + 40+ casos de uso reales de parlamentos.
  Define principios de **transparencia, rendición de cuentas, equidad y mitigación de sesgos** para IA legislativa.
- **Por qué importa:** es el estándar internacional con el que DipuBot debería poder mostrarse alineado
  (clave para fondos, credibilidad institucional y mitigación de riesgos).
- **Qué tomar:** checklist de gobernanza/ética; lenguaje de "principios" para la documentación del proyecto.
- 🔗 https://www.ipu.org/resources/publications/reference/2024-12/guidelines-ai-in-parliaments
- 🔗 https://www.ipu.org/file/20632/download (PDF)

### D.2 — Biblioteca del Congreso (BCN) — Dossier Legislativo IA (Argentina)
- **Qué es:** material oficial argentino sobre IA y legislación; contexto regulatorio local.
- **Qué tomar:** encuadre regulatorio nacional; legitimidad de fuentes oficiales.
- 🔗 https://bcn.gob.ar/biblioteca-digital/dossier-legislativo-inteligencia-artificial---abril-2025

### D.3 — RAG legal/cívico comparable (arquitectura)
- **GOV.UK Chat** (ver A.2) como el RAG cívico-oficial de referencia.
- Herramientas de **RAG legal** comerciales (Harvey, CoCounsel/Casetext, Spellbook) como benchmark de
  **calidad de cita y anti-alucinación** — NO de propósito cívico, pero sí de rigor técnico en dominio legal.
- **Qué tomar:** prácticas de citación de la fuente exacta y evaluación de alucinaciones (relevante para
  la promesa de DipuBot de "información verificada").

---

## Síntesis comparativa

| # | Antecedente | País | IA gen. | Fuente oficial | Lenguaje claro | Ciudadanía | Cercanía |
|---|-------------|------|:------:|:--------------:|:--------------:|:----------:|:--------:|
| A.1 | Ulysses (Câmara) | BR | ✅ | ✅ | ◐ | ✅ | ★★★★★ |
| A.2 | GOV.UK Chat | UK | ✅ (RAG) | ✅ | ✅ | ✅ | ★★★★★ |
| A.3 | DiputadosAR / DipLab | AR | ◐ | ✅ | ◐ | ✅ | ★★★★☆ |
| A.4 | Senado Italia | IT | ✅ | ✅ | ◐ | ◐ | ★★★☆☆ |
| B.1 | TheyWorkForYou | UK | ❌ | ✅ | ✅ | ✅ | ★★★★☆ |
| B.2 | GovTrack | US | ❌ | ✅ | ◐ | ✅ | ★★★☆☆ |
| B.3 | Directorio Legislativo | AR | ❌ | ✅ | ◐ | ✅ | ★★★★☆ |
| B.5 | Congreso Abierto (CI) | CL | ❌ | ✅ | ✅ | ✅ | ★★★☆☆ |
| C.1 | DemocracyOS | AR | ❌ | ◐ | ✅ | ✅ | ★★★☆☆ |
| D.1 | IPU Guidelines | Intl | — | — | — | — | marco |

*Leyenda: ✅ sí · ◐ parcial · ❌ no · — no aplica.*

---

## Lecturas para mejorar DipuBot (qué adoptar)

1. **Citación trazable al documento oficial** (de RAG legal + DipLab): cada respuesta debería linkear a la
   ley/proyecto exacto en la fuente oficial → refuerza "información verificada".
2. **Alertas por tema/legislador** (de TheyWorkForYou / GovTrack): pasar de Q&A puntual a seguimiento continuo.
3. **Ficha por legislador y estado del trámite** (de Directorio Legislativo / GovTrack): enriquecer el corpus
   más allá de "leyes sancionadas".
4. **Alineación explícita con las IPU Guidelines** (transparencia, sesgos, rendición de cuentas): convertirlo en
   sección de documentación y argumento ante fondos.
5. **Anonimización y disclaimers** (de GOV.UK Chat): política clara de privacidad y de "no es asesoría legal/política".
6. **Camino a participación** (de DemocracyOS): roadmap opcional de consulta → deliberación.
7. **Diferencial frente a IA personalista de legisladores**: comunicar neutralidad + corpus oficial único como ventaja.

---

## Fuentes

- Câmara dos Deputados — Ulysses: https://www.camara.leg.br/noticias/548730-camara-lanca-ulysses-robo-digital-que-articula-dados-legislativos/
- Ulysses (GitHub): https://github.com/ulysses-camara
- GOV.UK Chat (The Register): https://www.theregister.com/2025/12/19/govuk_chatbot/
- DiputadosAR — DipLab: https://diplab.hcdn.gob.ar/proyectos
- IPU — Role of AI in parliaments: https://www.ipu.org/ai-guidelines/role-ai-in-parliaments
- IPU — Guidelines for AI in parliaments (2024): https://www.ipu.org/resources/publications/reference/2024-12/guidelines-ai-in-parliaments
- IPU — Guidelines (PDF): https://www.ipu.org/file/20632/download
- TheyWorkForYou: https://www.theyworkforyou.com/
- WriteToThem / mySociety: https://www.mysociety.org/category/democracy/writetothem/
- GovTrack.us: https://www.govtrack.us/
- Directorio Legislativo (legisladores): https://legisladores.directoriolegislativo.org/
- Directorio Legislativo — Guía de monitoreo: https://directoriolegislativo.org/es/guia-global-sobre-monitoreo-parlamentario-con-tecnologia/
- Plataforma de Información Legislativa (PIL): https://www.argentina.gob.ar/jefatura/secretaria-de-gabinete/asuntos-parlamentarios/plataforma-de-informacion-legislativa
- Fundación Ciudadanía Inteligente: https://en.ciudadanointeligente.org/
- Vota Inteligente: https://votainteligente.cl/
- DemocracyOS / Democracia en Red: https://democraciaos.org/
- Consultas Digitales (GitHub): https://github.com/DemocraciaEnRed/consultas-digitales
- BCN — Dossier Legislativo IA (abril 2025): https://bcn.gob.ar/biblioteca-digital/dossier-legislativo-inteligencia-artificial---abril-2025
- Infobae — IA de legislador: https://www.infobae.com/politica/2025/07/07/un-diputado-creo-su-version-de-inteligencia-artificial-para-trabajar-24-horas-y-no-perder-tiempo-en-la-campana-electoral/
