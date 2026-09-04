"""
Ingesta histórica de leyes InfoLEG (ampliación del corpus hasta 1997)
======================================================================
Implementa el "Plan de ampliación del corpus" descrito en
`RESUMEN_AVANCES.md`. Descarga los datos oficiales de InfoLEG (datos
abiertos, CC-BY 4.0) y arma un SQLite compatible con `run_etl.py`.

El pipeline tiene tres etapas, ejecutables por separado (son reanudables):

    metadatos  ->  descarga el ZIP oficial y extrae las Leyes del rango
                   de años pedido a un CSV local (ficha de cada norma).
    textos     ->  descarga el .htm de cada ley (URL construible desde
                   id_norma), extrae el texto legal y lo cachea en disco.
    build      ->  arma un SQLite unificado (esquema idéntico al de la
                   tabla `leyes`) uniendo, si se indica, una base previa
                   (p. ej. las 665 leyes 2015-2025) con las históricas.

Uso típico (todo hasta 1997, base unificada con las 665 existentes):

    python ingest_historico.py metadatos --desde 1997 --hasta 2025
    python ingest_historico.py textos
    python ingest_historico.py build \
        --base-previa ../data/raw/leyes-2015-2025_12_20.sqlite3 \
        --salida ../data/raw/leyes-1997-2025_unificada.sqlite3

Luego reindexar reutilizando lo existente:

    DATABASE_PATH=../data/raw/leyes-1997-2025_unificada.sqlite3 python run_etl.py

Nota de codificación (hallazgo de la Fase 3): el CSV oficial viene en
UTF-8 y las páginas .htm en cp1252 (Windows-1252). Los datos NO están
corruptos; el "mojibake" que se ve en consola es solo de visualización.
Aquí decodificamos con el encoding correcto de cada fuente y guardamos
todo en UTF-8, aplicando la misma `normalize_text` del ETL.
"""

import argparse
import csv
import html as html_mod
import io
import re
import sqlite3
import ssl
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

from tqdm import tqdm

# La consola de Windows suele venir en cp1252 y no puede imprimir los
# símbolos Unicode del script (mismo tipo de problema que motivó la Fase 3:
# es la CONSOLA, no los datos). Forzamos UTF-8 en la salida para que los
# mensajes de progreso se vean bien en cualquier terminal.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

# Reutilizamos la normalización de texto de la Fase 3 (misma limpieza
# liviana y segura que aplica el ETL antes de indexar).
from run_etl import normalize_text, METADATA_COLUMNS, TEXT_COLUMN


# ============================================================================
# CONFIGURACIÓN Y RUTAS
# ============================================================================

SCRIPT_DIR = Path(__file__).parent

# Directorio de trabajo para artefactos intermedios de la ingesta.
WORK_DIR = (SCRIPT_DIR / "../data/ingest").resolve()
ZIP_PATH = WORK_DIR / "base-infoleg-normativa-nacional.zip"
META_CSV = WORK_DIR / "leyes_metadatos.csv"      # fichas filtradas (etapa metadatos)
TEXTS_DIR = WORK_DIR / "textos"                  # caché de .htm -> .txt (etapa textos)

# Fuente oficial (InfoLEG vía Portal de Datos de Justicia, CC-BY 4.0).
ZIP_URL = (
    "https://datos.jus.gob.ar/dataset/"
    "d9a963ea-8b1d-4ca3-9dd9-07a4773e8c23/resource/"
    "bf0ec116-ad4e-4572-a476-e57167a84403/download/"
    "base-infoleg-normativa-nacional.zip"
)

USER_AGENT = "Mozilla/5.0 (DipuBot ingest; +https://datos.jus.gob.ar)"

# InfoLEG sirve el .htm por http con certificado a veces incompleto; usamos
# un contexto SSL tolerante SOLO para estas descargas de datos públicos.
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

# Columnas de la ficha oficial que nos interesan (el CSV trae 17; el resto
# —modificada_por / modifica_a— no forma parte del esquema de `leyes`).
# `texto_original` en el CSV oficial es el LINK al .htm, no el texto.
CSV_LINK_COLUMN = "texto_original"


# ============================================================================
# UTILIDADES DE RED
# ============================================================================

def _http_get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
        return resp.read()


def build_text_url(id_norma: str) -> str:
    """Construye la URL del .htm a partir del id_norma (rango de 5000)."""
    n = int(id_norma)
    lo = (n // 5000) * 5000
    hi = lo + 4999
    return (
        "http://servicios.infoleg.gob.ar/infolegInternet/anexos/"
        f"{lo}-{hi}/{n}/norma.htm"
    )


# ============================================================================
# ETAPA 1: METADATOS
# ============================================================================

def _descargar_zip(force: bool = False) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists() and not force:
        print(f"✔ ZIP ya presente: {ZIP_PATH} ({ZIP_PATH.stat().st_size/1e6:.1f} MB)")
        return
    print(f"⇩ Descargando base oficial de InfoLEG…\n  {ZIP_URL}")
    data = _http_get(ZIP_URL, timeout=300)
    ZIP_PATH.write_bytes(data)
    print(f"✔ Guardado {ZIP_PATH} ({len(data)/1e6:.1f} MB)")


def etapa_metadatos(desde: int, hasta: int, force_zip: bool = False) -> None:
    """Descarga el ZIP oficial y extrae las Leyes del rango de años a un CSV."""
    _descargar_zip(force=force_zip)

    print(f"⚙ Filtrando tipo=Ley, fecha_sancion en [{desde}, {hasta}]…")
    z = zipfile.ZipFile(ZIP_PATH)
    csv_name = z.namelist()[0]
    # El CSV oficial es UTF-8.
    raw = z.read(csv_name).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))

    seleccionadas: List[Dict[str, str]] = []
    for row in reader:
        if (row.get("tipo_norma") or "").strip().lower() != "ley":
            continue
        fecha = (row.get("fecha_sancion") or "").strip()
        year_str = fecha[:4]
        if not year_str.isdigit():
            continue
        year = int(year_str)
        if not (desde <= year <= hasta):
            continue
        row["_year"] = str(year)
        seleccionadas.append(row)

    # Orden estable por año y número para reproducibilidad.
    seleccionadas.sort(key=lambda r: (r["_year"], r.get("id_norma", "")))

    META_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(seleccionadas[0].keys()) if seleccionadas else []
    with open(META_CSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(seleccionadas)

    # Resumen por año.
    por_year: Dict[str, int] = {}
    for r in seleccionadas:
        por_year[r["_year"]] = por_year.get(r["_year"], 0) + 1
    print(f"✔ {len(seleccionadas)} leyes seleccionadas -> {META_CSV}")
    for y in sorted(por_year):
        print(f"    {y}: {por_year[y]}")


# ============================================================================
# ETAPA 2: TEXTOS
# ============================================================================

_RE_SCRIPT = re.compile(r"(?is)<script.*?</script>")
_RE_STYLE = re.compile(r"(?is)<style.*?</style>")
_RE_BODY = re.compile(r"(?is)<body[^>]*>(.*)</body>")
_RE_TAG = re.compile(r"(?is)<[^>]+>")
_RE_WS_INLINE = re.compile(r"[ \t]+")
_RE_WS_BLANK = re.compile(r"\n\s*\n+")

# Artefactos de navegación de InfoLEG que se cuelan como texto (enlaces del
# encabezado de la página). No son parte de la ley: se remueven para no
# contaminar el embedding.
_RE_NAV_ARTIFACTS = re.compile(
    r"(?im)^\s*(?:"
    r"Ir a texto actualizado(?: y otros datos)?"
    r"|Ver texto actualizado"
    r"|Antecedentes Normativos"
    r"|Actualizado al.*"
    r")\s*$"
)


def _extraer_texto_legal(html: str) -> str:
    """Extrae el texto legal plano de una página norma.htm de InfoLEG."""
    body = _RE_SCRIPT.sub("", html)
    body = _RE_STYLE.sub("", body)
    m = _RE_BODY.search(body)
    inner = m.group(1) if m else body
    text = _RE_TAG.sub(" ", inner)
    text = html_mod.unescape(text)
    text = _RE_WS_INLINE.sub(" ", text)
    text = _RE_WS_BLANK.sub("\n\n", text)
    # Quitar enlaces de navegación de InfoLEG (línea por línea, ya sin tags).
    text = "\n".join(
        ln for ln in text.split("\n") if not _RE_NAV_ARTIFACTS.match(ln)
    )
    text = _RE_WS_BLANK.sub("\n\n", text)
    return text.strip()


def _text_path(id_norma: str) -> Path:
    return TEXTS_DIR / f"{id_norma}.txt"


def _descargar_un_texto(id_norma: str) -> tuple[str, str, Optional[str]]:
    """Descarga y extrae el texto de una ley. Devuelve (id, estado, error)."""
    dest = _text_path(id_norma)
    if dest.exists() and dest.stat().st_size > 0:
        return (id_norma, "cache", None)
    try:
        url = build_text_url(id_norma)
        raw = _http_get(url, timeout=45)
        # Las páginas .htm de InfoLEG están en cp1252 (Windows-1252).
        html = raw.decode("cp1252", errors="replace")
        texto = _extraer_texto_legal(html)
        if not texto:
            return (id_norma, "vacio", "sin texto legal extraíble")
        dest.write_text(texto, encoding="utf-8")
        return (id_norma, "ok", None)
    except Exception as exc:  # noqa: BLE001 - registramos y seguimos
        return (id_norma, "error", f"{type(exc).__name__}: {exc}")


def etapa_textos(workers: int = 8, limite: Optional[int] = None) -> None:
    """Descarga en paralelo el texto de cada ley listada en el CSV."""
    if not META_CSV.exists():
        sys.exit(f"✖ Falta {META_CSV}. Corré primero la etapa 'metadatos'.")
    TEXTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(META_CSV, encoding="utf-8") as fh:
        ids = [row["id_norma"] for row in csv.DictReader(fh) if row.get("id_norma")]
    if limite:
        ids = ids[:limite]

    print(f"⇩ Descargando textos de {len(ids)} leyes ({workers} hilos)…")
    stats = {"ok": 0, "cache": 0, "vacio": 0, "error": 0}
    fallos: List[tuple[str, str]] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_descargar_un_texto, i): i for i in ids}
        for fut in tqdm(as_completed(futs), total=len(futs), desc="Textos"):
            _id, estado, err = fut.result()
            stats[estado] = stats.get(estado, 0) + 1
            if estado in ("error", "vacio"):
                fallos.append((_id, err or ""))

    print(f"✔ Descarga terminada: {stats}")
    if fallos:
        log = WORK_DIR / "textos_fallidos.log"
        with open(log, "w", encoding="utf-8") as fh:
            for _id, err in fallos:
                fh.write(f"{_id}\t{err}\n")
        print(f"⚠ {len(fallos)} fallos registrados en {log} "
              f"(reanudable: volvé a correr 'textos').")


# ============================================================================
# ETAPA 3: BUILD (SQLite unificado)
# ============================================================================

# Esquema idéntico al de la tabla `leyes` existente (21 columnas).
_SCHEMA = """
CREATE TABLE IF NOT EXISTS leyes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_norma INTEGER,
    tipo_norma TEXT,
    numero_norma TEXT,
    clase_norma TEXT,
    organismo_origen TEXT,
    fecha_sancion TEXT,
    numero_boletin INTEGER,
    fecha_boletin TEXT,
    pagina_boletin INTEGER,
    titulo_resumido TEXT,
    titulo_sumario TEXT,
    texto_resumido TEXT,
    observaciones TEXT,
    texto_original TEXT,
    texto_actualizado TEXT,
    texto_original_link TEXT,
    texto_actualizado_link TEXT,
    numero_ley_original INTEGER,
    numero_ley_actualizado INTEGER,
    year INTEGER
);
"""

# Todas las columnas menos el id autoincremental.
_INSERT_COLS = [c for c in (METADATA_COLUMNS + [TEXT_COLUMN]) if c != "id"]


def _to_int(v) -> Optional[int]:
    try:
        s = str(v).strip()
        return int(s) if s else None
    except (TypeError, ValueError):
        return None


def _fila_desde_meta(meta: Dict[str, str]) -> Optional[Dict[str, object]]:
    """Arma una fila del esquema `leyes` desde una ficha del CSV + su texto."""
    id_norma = (meta.get("id_norma") or "").strip()
    if not id_norma:
        return None
    tp = _text_path(id_norma)
    if not (tp.exists() and tp.stat().st_size > 0):
        return None  # sin texto -> se omite (coherente con el WHERE del ETL)
    texto = normalize_text(tp.read_text(encoding="utf-8"))
    if not texto.strip():
        return None

    year = _to_int((meta.get("fecha_sancion") or "")[:4])
    numero = (meta.get("numero_norma") or "").strip()
    link = (meta.get(CSV_LINK_COLUMN) or "").strip() or build_text_url(id_norma)

    return {
        "id_norma": _to_int(id_norma),
        "tipo_norma": normalize_text(meta.get("tipo_norma") or ""),
        "numero_norma": numero,
        "clase_norma": normalize_text(meta.get("clase_norma") or "") or None,
        "organismo_origen": normalize_text(meta.get("organismo_origen") or ""),
        "fecha_sancion": (meta.get("fecha_sancion") or "").strip(),
        "numero_boletin": _to_int(meta.get("numero_boletin")),
        "fecha_boletin": (meta.get("fecha_boletin") or "").strip(),
        "pagina_boletin": _to_int(meta.get("pagina_boletin")),
        "titulo_resumido": normalize_text(meta.get("titulo_resumido") or ""),
        "titulo_sumario": normalize_text(meta.get("titulo_sumario") or ""),
        "texto_resumido": normalize_text(meta.get("texto_resumido") or ""),
        "observaciones": normalize_text(meta.get("observaciones") or "") or None,
        "texto_original": texto,
        "texto_actualizado": None,
        "texto_original_link": link,
        "texto_actualizado_link": None,
        "numero_ley_original": _to_int(numero),
        "numero_ley_actualizado": None,
        "year": year,
    }


def _copiar_base_previa(dst: sqlite3.Connection, base_previa: Path) -> tuple[int, set]:
    """Copia las filas de una base previa al destino. Devuelve (n, ids_vistos)."""
    src = sqlite3.connect(str(base_previa))
    src.row_factory = sqlite3.Row
    cols = ", ".join(_INSERT_COLS)
    placeholders = ", ".join(["?"] * len(_INSERT_COLS))
    rows = src.execute(f"SELECT {cols} FROM leyes").fetchall()
    ids_vistos: set = set()
    n = 0
    for r in rows:
        d = dict(r)
        ids_vistos.add(d.get("id_norma"))
        dst.execute(
            f"INSERT INTO leyes ({cols}) VALUES ({placeholders})",
            [d.get(c) for c in _INSERT_COLS],
        )
        n += 1
    src.close()
    return n, ids_vistos


def etapa_build(salida: Path, base_previa: Optional[Path]) -> None:
    """Arma el SQLite unificado: base previa (opcional) + leyes históricas."""
    if not META_CSV.exists():
        sys.exit(f"✖ Falta {META_CSV}. Corré primero la etapa 'metadatos'.")

    salida = salida.resolve()
    salida.parent.mkdir(parents=True, exist_ok=True)
    if salida.exists():
        sys.exit(f"✖ El destino ya existe: {salida}. Borralo o elegí otro nombre.")

    dst = sqlite3.connect(str(salida))
    dst.execute(_SCHEMA)

    ids_previos: set = set()
    n_previas = 0
    if base_previa:
        base_previa = base_previa.resolve()
        if not base_previa.exists():
            sys.exit(f"✖ Base previa no encontrada: {base_previa}")
        print(f"⇒ Copiando base previa: {base_previa}")
        n_previas, ids_previos = _copiar_base_previa(dst, base_previa)
        print(f"  ✔ {n_previas} leyes copiadas de la base previa")

    print("⇒ Agregando leyes históricas (con texto descargado)…")
    cols = ", ".join(_INSERT_COLS)
    placeholders = ", ".join(["?"] * len(_INSERT_COLS))

    n_nuevas = 0
    sin_texto = 0
    duplicadas = 0
    with open(META_CSV, encoding="utf-8") as fh:
        metas = list(csv.DictReader(fh))
    for meta in tqdm(metas, desc="Ensamblando"):
        id_norma = _to_int((meta.get("id_norma") or "").strip())
        if id_norma is not None and id_norma in ids_previos:
            duplicadas += 1
            continue  # ya está en la base previa; no duplicar
        fila = _fila_desde_meta(meta)
        if fila is None:
            sin_texto += 1
            continue
        dst.execute(
            f"INSERT INTO leyes ({cols}) VALUES ({placeholders})",
            [fila.get(c) for c in _INSERT_COLS],
        )
        ids_previos.add(id_norma)
        n_nuevas += 1

    dst.commit()
    total = dst.execute("SELECT COUNT(*) FROM leyes").fetchone()[0]
    rango = dst.execute("SELECT MIN(year), MAX(year) FROM leyes").fetchone()
    dst.close()

    print("\n" + "=" * 60)
    print("✅ Base unificada creada")
    print("=" * 60)
    print(f"  Archivo:            {salida}")
    print(f"  Copiadas (previa):  {n_previas}")
    print(f"  Nuevas históricas:  {n_nuevas}")
    print(f"  Omitidas sin texto: {sin_texto}")
    print(f"  Ya en base previa:  {duplicadas}")
    print(f"  TOTAL en la base:   {total}  (years {rango[0]}–{rango[1]})")
    print(f"\n▶ Reindexar con:  DATABASE_PATH={salida} python run_etl.py")


# ============================================================================
# CLI
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingesta histórica de leyes InfoLEG (ampliación del corpus).",
    )
    sub = parser.add_subparsers(dest="etapa", required=True)

    p_meta = sub.add_parser("metadatos", help="Descargar ZIP oficial y filtrar Leyes.")
    p_meta.add_argument("--desde", type=int, default=1997)
    p_meta.add_argument("--hasta", type=int, default=2025)
    p_meta.add_argument("--force-zip", action="store_true",
                        help="Re-descargar el ZIP aunque exista en caché.")

    p_txt = sub.add_parser("textos", help="Descargar el texto .htm de cada ley.")
    p_txt.add_argument("--workers", type=int, default=8)
    p_txt.add_argument("--limite", type=int, default=None,
                       help="Descargar solo las primeras N (para pruebas).")

    p_build = sub.add_parser("build", help="Armar el SQLite unificado.")
    p_build.add_argument("--salida", type=Path, required=True)
    p_build.add_argument("--base-previa", type=Path, default=None,
                         help="SQLite existente a incluir (p. ej. las 665 leyes).")

    args = parser.parse_args()

    if args.etapa == "metadatos":
        etapa_metadatos(args.desde, args.hasta, force_zip=args.force_zip)
    elif args.etapa == "textos":
        etapa_textos(workers=args.workers, limite=args.limite)
    elif args.etapa == "build":
        etapa_build(args.salida, args.base_previa)


if __name__ == "__main__":
    main()
