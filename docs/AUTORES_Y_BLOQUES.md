# Autores, firmantes y bloques desde 2008

La base `data/raw/leyes-1997-2025_unificada.sqlite3` conserva las leyes 1997–2025 y se enriquece con autorías de proyectos vinculados a leyes desde 2008. La importación no modifica textos ni IDs y no requiere reconstruir el índice vectorial: estas consultas usan SQL.

## Fuentes y alcance

- [Leyes sancionadas](https://datos.hcdn.gob.ar/dataset/leyes-sancionadas): vínculo entre ley y proyecto.
- [Proyectos parlamentarios](https://datos.hcdn.gob.ar/dataset/proyectos-parlamentarios): autor, cámara, expedientes y fecha de publicación.
- Fichas oficiales de HCDN: tabla de firmantes, distrito y bloque de cada proyecto.

Los CSV se localizan mediante la API pública CKAN `package_show`. Se conservan HTML comprimidos, URLs, sumas SHA-256 y manifiesto de descarga.

El antiguo [diccionario de firmantes](https://www4.hcdn.gob.ar/Datos_doc/Doc_Firmantes%20leyes%20sancionadas.pdf) describe un recurso específico que no apareció en el catálogo público al verificarlo el 20/09/2026. Por eso se usan los CSV actuales y las fichas, sin depender de una URL de descarga supuesta.

La cobertura es **parcial** y centrada en proyectos cabecera. Proyectos iniciados desde 2008 no equivale a todas las leyes sancionadas desde ese año: algunas provienen de proyectos anteriores. No incluye todos los proyectos no sancionados ni todas las iniciativas acumuladas en una ley.

El informe `data/ingest/hcdn/report.json` incluye cobertura por año y leyes sin cruce. Ver también [COBERTURA_AUTORES.md](COBERTURA_AUTORES.md).

## Interpretación

- `rol='autor'` se verifica con `AUTOR` del CSV oficial. Los restantes conservan `rol='firmante'`; no se infiere autoría de la posición en HTML.
- `orden` conserva la posición en la ficha, cuando está disponible.
- El bloque es el histórico publicado en la ficha, no la afiliación actual. No equivale necesariamente al partido.
- `PODER EJECUTIVO` es procedencia institucional, no un partido.
- Los faltantes se guardan como `NULL`. La ausencia de una firma no prueba que alguien no haya presentado proyectos. No hay datos de votaciones.
- Si una ficha falla, se conserva el autor documentado en el CSV, sin inventar bloque ni distrito. Se registra el estado de la ficha.

## Consulta

`chat/parliamentary.py` documenta la vista `autorias_leyes`. Esta une `hcdn_proyectos`, `hcdn_ley_proyectos` y `hcdn_firmantes` con `leyes`.

```sql
SELECT numero_norma, firmante, rol, bloque, distrito,
       expediente_diputados, expediente_senado, fuente_url, fuente_autor_url
FROM autorias_leyes
WHERE numero_norma = '26618'
ORDER BY orden;
```

Para contar leyes usar `COUNT(DISTINCT ley_id)`; para el autor del proyecto cabecera, filtrar `rol='autor'`.

## Actualización y publicación

Desde `DipuBot/`:

```powershell
python -m etl.ingest_autorias fetch
python -m etl.ingest_autorias import
python -m unittest discover -s tests -v
```

`fetch` usa cuatro conexiones, reintentos limitados y caché reanudable. Para actualizar también las fichas ya descargadas, usar un directorio nuevo con `--cache data/ingest/hcdn-AAAA-MM-DD` en ambos comandos.

`import` verifica las sumas SHA-256 antes de escribir y crea una copia `*.before-autorias-*.sqlite3`. Reemplaza únicamente sus tablas propias dentro de una transacción; verifica relaciones y conservación del total de leyes. Repetir la importación no duplica firmas.

La base unificada ya está versionada en este repositorio, aunque `.gitignore` excluye nuevas bases y descargas. Para publicar la ampliación hay que incluir también el cambio del archivo SQLite, o ejecutar la importación en destino. Las copias de respaldo y la caché no se agregan a Git.

La base parlamentaria anterior de 2023–2025 permanece intacta. Esta importación usa fuentes actuales, sin fusionar IDs ni atribuir roles que el esquema antiguo no distinguía.
