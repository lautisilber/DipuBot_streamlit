# Legal RAG Argentina

RAG minimalista para consulta de documentos legales argentinos.  
Stack: Python + LlamaIndex + Streamlit.

## Estructura

```
data/raw/          → documentos fuente (.pdf, .txt, .docx)
data/stories/      → índices persistidos por versión
data/stories/registry.yaml → registro de versiones
```

## Versionado de índices

Cada índice se guarda en `data/stories/<INDEX_VERSION>/`.  
La versión se define vía `INDEX_VERSION` env var o se genera como `YYYY-MM-DD`.

## Comandos

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env (copiar de .env.example)
cp .env.example .env

# 3. Colocar documentos en data/raw/

# 4. Ejecutar ETL (construye índice)
python -m etl.run

# 5. Abrir UI
streamlit run streamlit_app.py
```

## Docs

Ver `docs/DEVELOPER_DOC.md` para más detalles.
