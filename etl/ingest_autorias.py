"""Importación reproducible de autorías HCDN, sin modificar textos ni IDs de leyes.

python -m etl.ingest_autorias fetch
python -m etl.ingest_autorias import
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3
import time
import unicodedata
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/ingest/hcdn"
DB = ROOT / "data/raw/leyes-1997-2025_unificada.sqlite3"
API = "https://datos.hcdn.gob.ar/api/3/action/"
PROJECT_URL = "https://www.hcdn.gob.ar/comisiones/permanentes/clgeneral/proyecto.html"


def clean(value):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value or "")).split())


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFD", clean(value).upper())
                   if unicodedata.category(c) != "Mn")


def parse_signers(document, expediente):
    # Evitar importar un error HTTP disfrazado de página o una ficha distinta.
    if not re.search(r"Expediente\s*:\s*" + re.escape(expediente), clean(document), re.I):
        raise ValueError("La ficha no identifica el expediente solicitado")
    for table in re.findall(r"<table\b[^>]*>(.*?)</table>", document, re.S | re.I):
        headers = [clean(h).lower() for h in re.findall(r"<th\b[^>]*>(.*?)</th>", table, re.S | re.I)]
        if headers != ["firmante", "distrito", "bloque"]:
            continue
        result = []
        for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", table, re.S | re.I):
            cells = [clean(c) for c in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S | re.I)]
            if cells and (len(cells) != 3 or not cells[0]):
                raise ValueError("Fila de firmantes incompleta")
            if cells:
                result.append(dict(nombre=cells[0], distrito=cells[1] or None, bloque=cells[2] or None))
        return result
    return []


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def selected_projects(db, cache):
    conn = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        laws = {str(number).replace(".", ""): ident for ident, number in conn.execute(
            "SELECT id, numero_norma FROM leyes WHERE UPPER(tipo_norma)='LEY' AND year BETWEEN 2008 AND 2025")}
    finally:
        conn.close()
    projects = {r["PROYECTO_ID"]: r for r in csv_rows(cache / "proyectos.csv")}
    links = [(laws[r["LEY"]], r["PROYECTO_ID"]) for r in csv_rows(cache / "leyes.csv")
             if r["LEY"] in laws and r["PROYECTO_ID"] in projects]
    return {pid: projects[pid] for _, pid in links}, sorted(set(links))


def download(url):
    for attempt in range(3):
        try:
            with urlopen(url, timeout=35) as response:
                return response.read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)


def fetch(db, cache):
    cache.mkdir(parents=True, exist_ok=True)
    manifest = {"downloaded_at": datetime.now(timezone.utc).isoformat(), "resources": {}}
    for dataset, name in [("leyes-sancionadas", "leyes"), ("proyectos-parlamentarios", "proyectos")]:
        package = json.loads(download(API + "package_show?" + urlencode({"id": dataset})))["result"]
        resource = next(r for r in package["resources"] if r["url"].lower().endswith(".csv"))
        data = download(resource["url"])
        (cache / f"{name}.csv").write_bytes(data)
        manifest["resources"][name] = {"url": resource["url"], "sha256": hashlib.sha256(data).hexdigest()}
    projects, _ = selected_projects(db, cache)
    pages = cache / "fichas"
    pages.mkdir(exist_ok=True)

    def fetch_page(item):
        pid, project = item
        exp = project["EXP_DIPUTADOS"]
        url = PROJECT_URL + "?" + urlencode({"exp": exp})
        target = pages / f"{pid}.html.gz"
        try:
            if target.exists():
                data = gzip.decompress(target.read_bytes())
            else:
                data = download(url)
                parse_signers(data.decode("utf-8-sig"), exp)
                target.write_bytes(gzip.compress(data, mtime=0))
                time.sleep(0.15)
            signers = parse_signers(data.decode("utf-8-sig"), exp)
            return pid, {"url": url, "sha256": hashlib.sha256(data).hexdigest(),
                         "signers": len(signers), "status": "ok" if signers else "no_signers"}
        except Exception as error:
            return pid, {"url": url, "status": "error", "error": str(error)}

    manifest["pages"] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch_page, item) for item in projects.items()]
        for future in as_completed(futures):
            pid, status = future.result()
            manifest["pages"][pid] = status
            count = len(manifest["pages"])
            if count % 50 == 0:
                print(f"Fichas {count}/{len(projects)}", flush=True)
    (cache / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"projects": len(projects), "errors": sum(p["status"] == "error" for p in manifest["pages"].values())}))


SCHEMA = """
CREATE TABLE IF NOT EXISTS hcdn_proyectos (
 proyecto_id TEXT PRIMARY KEY, camara_origen TEXT, expediente_diputados TEXT,
 expediente_senado TEXT, fecha_publicacion TEXT, autor TEXT, fuente_url TEXT,
 estado_ficha TEXT, fuente_autor_url TEXT, importado_en TEXT);
CREATE TABLE IF NOT EXISTS hcdn_ley_proyectos (
 ley_id INTEGER REFERENCES leyes(id), proyecto_id TEXT REFERENCES hcdn_proyectos(proyecto_id),
 PRIMARY KEY (ley_id, proyecto_id));
CREATE TABLE IF NOT EXISTS hcdn_firmantes (
 proyecto_id TEXT REFERENCES hcdn_proyectos(proyecto_id), orden INTEGER,
 nombre TEXT NOT NULL, distrito TEXT, bloque TEXT, rol TEXT NOT NULL,
 fuente_url TEXT, UNIQUE(proyecto_id, nombre, bloque));
CREATE INDEX IF NOT EXISTS hcdn_firmantes_proyecto ON hcdn_firmantes(proyecto_id);
CREATE TABLE IF NOT EXISTS hcdn_importaciones (
 id INTEGER PRIMARY KEY, fecha TEXT NOT NULL, manifest_json TEXT NOT NULL);
CREATE VIEW IF NOT EXISTS autorias_leyes AS
 SELECT l.id AS ley_id, l.numero_norma, l.titulo_resumido, l.year,
 p.proyecto_id, p.camara_origen, p.expediente_diputados, p.expediente_senado,
 p.fecha_publicacion, f.nombre AS firmante, f.rol, f.orden, f.bloque, f.distrito,
 f.fuente_url, p.fuente_autor_url, p.estado_ficha
 FROM leyes l JOIN hcdn_ley_proyectos lp ON lp.ley_id=l.id
 JOIN hcdn_proyectos p ON p.proyecto_id=lp.proyecto_id
 JOIN hcdn_firmantes f ON f.proyecto_id=p.proyecto_id;
"""


def integrate(db, cache):
    manifest = json.loads((cache / "manifest.json").read_text(encoding="utf-8"))
    for name, resource in manifest["resources"].items():
        if hashlib.sha256((cache / f"{name}.csv").read_bytes()).hexdigest() != resource["sha256"]:
            raise ValueError(f"Archivo alterado: {name}")
    projects, links = selected_projects(db, cache)
    prepared = []
    for pid, project in projects.items():
        page = manifest["pages"][pid]
        signers = []
        if page["status"] != "error":
            data = gzip.decompress((cache / "fichas" / f"{pid}.html.gz").read_bytes())
            if hashlib.sha256(data).hexdigest() != page["sha256"]:
                raise ValueError(f"Ficha alterada: {pid}")
            signers = parse_signers(data.decode("utf-8-sig"), project["EXP_DIPUTADOS"])
        author = clean(project["AUTOR"])
        records = []
        for order, signer in enumerate(signers, 1):
            # La posición en HTML se conserva, pero el rol autor se confirma
            # contra AUTOR del CSV, no se infiere del orden de la tabla.
            role = "autor" if author and normalized(signer["nombre"]) == normalized(author) else "firmante"
            records.append((pid, order, signer["nombre"], signer["distrito"], signer["bloque"], role, page["url"]))
        if author and not any(record[5] == "autor" for record in records):
            records.append((pid, None, author, None, None, "autor", manifest["resources"]["proyectos"]["url"]))
        prepared.append((pid, project, page, records))
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys=ON")
    backup = db.with_name(db.stem + ".before-autorias-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".sqlite3")
    target = sqlite3.connect(backup)
    conn.backup(target)
    target.close()
    try:
        conn.executescript(SCHEMA)
        before = conn.execute("SELECT count(*) FROM leyes").fetchone()[0]
        with conn:
            # Tablas propias de esta importación; ninguna tabla de leyes se altera.
            conn.execute("DELETE FROM hcdn_firmantes")
            conn.execute("DELETE FROM hcdn_ley_proyectos")
            conn.execute("DELETE FROM hcdn_proyectos")
            for pid, p, page, records in prepared:
                conn.execute("INSERT INTO hcdn_proyectos VALUES (?,?,?,?,?,?,?,?,?,?)", (
                    pid, p["CAMARA_ORIGEN"], p["EXP_DIPUTADOS"], p["EXP_SENADO"],
                    p["PUBLICACION_FECHA"][:10], clean(p["AUTOR"]), page["url"], page["status"],
                    manifest["resources"]["proyectos"]["url"], manifest["downloaded_at"]))
                conn.executemany("INSERT OR IGNORE INTO hcdn_firmantes VALUES (?,?,?,?,?,?,?)", records)
            conn.executemany("INSERT INTO hcdn_ley_proyectos VALUES (?,?)", links)
            conn.execute("INSERT INTO hcdn_importaciones(fecha,manifest_json) VALUES (?,?)", (
                manifest["downloaded_at"], json.dumps(manifest, ensure_ascii=False)))
            assert conn.execute("SELECT count(*) FROM leyes").fetchone()[0] == before
            if conn.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Relaciones inválidas")
        report = {
            "laws_total": before,
            "laws_with_signers": conn.execute("SELECT count(DISTINCT ley_id) FROM autorias_leyes").fetchone()[0],
            "laws_with_author": conn.execute("SELECT count(DISTINCT ley_id) FROM autorias_leyes WHERE rol='autor'").fetchone()[0],
            "laws_with_block": conn.execute("SELECT count(DISTINCT ley_id) FROM autorias_leyes WHERE bloque IS NOT NULL").fetchone()[0],
            "signer_records": conn.execute("SELECT count(*) FROM hcdn_firmantes").fetchone()[0],
            "coverage_by_year": conn.execute("SELECT l.year,count(DISTINCT l.id),count(DISTINCT a.ley_id) FROM leyes l LEFT JOIN autorias_leyes a ON a.ley_id=l.id WHERE l.year BETWEEN 2008 AND 2025 GROUP BY l.year").fetchall(),
            "unmatched_laws": conn.execute("SELECT numero_norma,year FROM leyes WHERE year BETWEEN 2008 AND 2025 AND id NOT IN (SELECT ley_id FROM hcdn_ley_proyectos) ORDER BY year,numero_norma").fetchall(),
            "backup": str(backup), "downloaded_at": manifest["downloaded_at"],
        }
        (cache / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in report.items() if k != "unmatched_laws"}, ensure_ascii=True), flush=True)
        return report
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["fetch", "import"])
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--cache", type=Path, default=CACHE)
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error("No existe la base de leyes")
    (fetch if args.action == "fetch" else integrate)(args.db, args.cache)
