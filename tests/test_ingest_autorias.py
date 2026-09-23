import csv
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from etl.ingest_autorias import integrate, parse_signers


HTML = """<p>Expediente: 0001-D-2008</p>
<table><tr><th>Firmante</th><th>Distrito</th><th>Bloque</th></tr>
<tr><td>PÉREZ, ANA</td><td>CÓRDOBA</td><td>BLOQUE HISTÓRICO</td></tr>
<tr><td>GOMEZ, JUAN</td><td></td><td></td></tr></table>"""


class IngestAutoriasTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "laws.sqlite3"
        self.cache = self.root / "cache"
        (self.cache / "fichas").mkdir(parents=True)
        conn = sqlite3.connect(self.db)
        conn.execute("CREATE TABLE leyes(id INTEGER PRIMARY KEY, numero_norma TEXT, "
                     "tipo_norma TEXT, year INTEGER, titulo_resumido TEXT, texto_original TEXT)")
        conn.executemany("INSERT INTO leyes VALUES(?,?,?,?,?,?)", [
            (97, "25000", "LEY", 1997, "Anterior", "Texto anterior"),
            (101, "26371", "LEY", 2008, "Prueba", "Texto que debe conservarse"),
            (108, "26485", "LEY", 2009, "Sin ficha", "Texto dos"),
            (120, "27000", "LEY", 2010, "Sin cruce", "Texto tres"),
        ])
        conn.commit()
        self.original = conn.execute("SELECT * FROM leyes ORDER BY id").fetchall()
        conn.close()
        laws = [dict(LEY="26371", PROYECTO_ID="A"), dict(LEY="26485", PROYECTO_ID="B")]
        projects = [dict(PROYECTO_ID=pid, EXP_DIPUTADOS="0001-D-2008", EXP_SENADO="",
                         CAMARA_ORIGEN="Diputados", PUBLICACION_FECHA="2008-04-01T00:00:00",
                         AUTOR=author) for pid, author in [("A", "PEREZ, ANA"), ("B", "OTRA, PERSONA")]]
        manifest = {"downloaded_at": "2026-09-20", "resources": {}, "pages": {}}
        for name, rows in [("leyes", laws), ("proyectos", projects)]:
            path = self.cache / f"{name}.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            manifest["resources"][name] = dict(url="https://datos.hcdn.gob.ar/test.csv",
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        raw = HTML.encode("utf-8")
        (self.cache / "fichas/A.html.gz").write_bytes(gzip.compress(raw))
        manifest["pages"] = {
            "A": dict(status="ok", url="https://www.hcdn.gob.ar/test", sha256=hashlib.sha256(raw).hexdigest()),
            "B": dict(status="error", url="https://www.hcdn.gob.ar/test-b"),
        }
        (self.cache / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_import_preserves_laws_historical_blocks_and_author_roles(self):
        report = integrate(self.db, self.cache)
        conn = sqlite3.connect(self.db)
        try:
            self.assertEqual(conn.execute("SELECT * FROM leyes ORDER BY id").fetchall(), self.original)
            rows = conn.execute("SELECT firmante,rol,bloque FROM autorias_leyes WHERE ley_id=101 ORDER BY orden").fetchall()
            self.assertEqual(rows, [("PÉREZ, ANA", "autor", "BLOQUE HISTÓRICO"), ("GOMEZ, JUAN", "firmante", None)])
            self.assertEqual(conn.execute("SELECT firmante,bloque,orden FROM autorias_leyes WHERE ley_id=108").fetchone(),
                             ("OTRA, PERSONA", None, None))
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(report["laws_with_signers"], 2)
            self.assertEqual(report["laws_with_block"], 1)
        finally:
            conn.close()

    def test_reimport_is_idempotent(self):
        integrate(self.db, self.cache)
        report = integrate(self.db, self.cache)
        self.assertEqual(report["signer_records"], 3)
        self.assertEqual(report["laws_total"], 4)

    def test_wrong_expediente_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_signers(HTML, "0002-D-2008")

    def test_modified_snapshot_does_not_write_database(self):
        (self.cache / "leyes.csv").write_text("corrupto", encoding="utf-8")
        with self.assertRaises(ValueError):
            integrate(self.db, self.cache)
        conn = sqlite3.connect(self.db)
        try:
            self.assertEqual(conn.execute("SELECT * FROM leyes ORDER BY id").fetchall(), self.original)
            self.assertEqual(conn.execute("SELECT name FROM sqlite_master WHERE name='hcdn_firmantes'").fetchall(), [])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
