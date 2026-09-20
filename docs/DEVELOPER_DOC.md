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

## Datos de autores y bloques

La base unificada conserva las leyes de 1997 a 2025 y agrega las tablas
`hcdn_proyectos`, `hcdn_ley_proyectos`, `hcdn_firmantes` y la vista
`autorias_leyes`. Las consultas usan esta vista y conservan las fuentes oficiales.

La cobertura de proyectos vinculados a leyes desde 2008 es parcial.
No incluye todos los proyectos presentados ni datos de votaciones.

Ver [Autores y bloques](AUTORES_Y_BLOQUES.md) para importar, actualizar y desplegar
los datos, y [Cobertura](COBERTURA_AUTORES.md) para los resultados de la carga.
