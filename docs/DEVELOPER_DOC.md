# Developer Guide

Guía rápida para desarrollo y deploy.

## Setup local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tu OPENAI_API_KEY
```

## Flujo de trabajo

1. **Agregar documentos**: colocar PDFs/TXTs en `data/raw/`
2. **Construir índice**: `python -m etl.run`
3. **Verificar registro**: revisar `data/stories/registry.yaml`
4. **Ejecutar UI**: `streamlit run streamlit_app.py`

## Versionado de índices

- El ETL lee `INDEX_VERSION` de `.env` o genera `YYYY-MM-DD`
- Cada versión crea carpeta en `data/stories/<version>/`
- Metadata se registra en `data/stories/registry.yaml`

## Deploy Streamlit Cloud

1. Push repo a GitHub
2. Conectar en share.streamlit.io
3. Configurar secrets (OPENAI_API_KEY, INDEX_VERSION)
4. El índice debe estar pre-construido y commiteado (o usar storage externo)

## Notas

- Chat lee `INDEX_VERSION` desde `chat/config.py`
- ETL y Chat son independientes; UI no construye índices

## Limitación conocida: datos de firmantes/bloques vs. cobertura del corpus

El sistema maneja **dos clases de datos con cobertura distinta**:

| Dato | Lo usa | Cobertura actual | Base |
|---|---|---|---|
| Texto y ficha de las leyes (búsqueda temática) | `rag_skill` (índice FAISS) | **1997-2025** | `data/raw/leyes-1997-2025_unificada.sqlite3` |
| Firmantes, bloques, comisiones, trámites | `sql_skill` (text-to-SQL) | **solo 2023-2025** | `data/raw/leyes-leyes-2023-2025_12_20-2026_01_19.sqlite3` |

`sql_skill` usa `DB_PATH` (`chat/config.py`), que hoy apunta a `leyes-2015-2025_12_20.sqlite3`
— una base que **solo tiene la tabla `leyes`**, sin las tablas parlamentarias
(`leyes_data`, `firmantes`, `afiliaciones`, `bloques`, `comisiones_*`, `dictamenes`,
`tramites`). Por eso una consulta de firmantes disparaba `no such table: leyes_data`.
Ese error crudo **ya no se muestra al usuario**: `sql_skill.execute()` lo captura y
responde explicando el alcance real (ver el `except sqlite3.Error`).

Notas adicionales sobre alcance:
- El sistema **no tiene datos de votaciones** (quién votó a favor/en contra); solo
  *firmantes* (quién impulsó/suscribió la norma). El schema no modela votos.
- Los firmantes cargados son mayormente de la Cámara de Diputados.

### Cómo resolverlo (para que los firmantes acompañen la cobertura 1997+)

La decisión de producto fue **priorizar la cobertura temática (1997-2025)** por sobre
la funcionalidad de firmantes; por eso NO se cambió `DB_PATH` a la base parlamentaria
(hacerlo limitaría todo a 2023-2025). Para levantar la limitación en el futuro, sin
sacrificar cobertura, el camino es:

1. **Obtener los datos parlamentarios históricos** (firmantes, bloques, comisiones,
   trámites) para 1997-2022. No están en la descarga oficial de InfoLEG; residen en el
   sitio del H. Congreso (Diputados/Senado) y requieren consulta por norma (fuente y
   procesamiento distintos del pipeline actual — ver `RESUMEN_AVANCES.md`, sección 8).
2. **Cargar esas tablas en la base unificada** (`leyes-1997-2025_unificada.sqlite3`),
   respetando el schema documentado en `LEYES_SCHEMA` (`sql_skill.py`) y vinculando por
   `leyes_data.ley_id → leyes.id` (los `id` de fila se preservan al construir la base
   unificada con `ingest_historico.py build`).
3. **Apuntar `DB_PATH` a esa base unificada** una vez que tenga las tablas
   parlamentarias. Así `rag_skill` y `sql_skill` compartirían una única base con
   cobertura 1997-2025 completa, y el manejo de error de firmantes dejaría de dispararse.
