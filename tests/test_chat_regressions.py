import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from chat.legal_lookup import law_numbers, lookup_laws
from chat.skills.sql_skill import SQLSkill


class ChatRegressions(unittest.TestCase):
    def test_exact_law_lookup_ignores_unrelated_norms(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "laws.sqlite3"
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TABLE leyes (id INTEGER, tipo_norma TEXT, "
                             "numero_norma TEXT, texto_original TEXT, texto_actualizado TEXT)")
                conn.executemany("INSERT INTO leyes VALUES (?, ?, ?, ?, ?)", [
                    (1, "LEY", "25675", "Texto ambiental completo", None),
                    (2, "DECRETO", "25675", "Otro documento", None),
                    (3, "LEY", "25390", "Otra ley", None),
                ])
            conn.close()
            chunks = lookup_laws("Qué dice la Ley 25.675", path)
            self.assertEqual([c["numero_norma"] for c in chunks], ["25675"])
            self.assertIn("Texto ambiental completo", chunks[0]["text"])
            self.assertEqual(lookup_laws("Ley 99999", path), [])

    def test_number_formats_and_missing_database(self):
        self.assertEqual(law_numbers("Ley 25.675 y ley 27733"), ["25675", "27733"])
        self.assertEqual(law_numbers("leyes de 2002"), [])
        self.assertEqual(lookup_laws("Ley 25675", Path("missing.sqlite3")), [])

    def test_sql_formatter_receives_all_seventeen_rows_as_tool_data(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Listado"))])
        skill = SQLSkill()
        rows = [{"numero_norma": str(25000 + i)} for i in range(17)]
        with patch.object(skill, "_get_openai_client", return_value=client):
            skill._format_results(rows, "Listá las leyes", "SELECT * FROM leyes LIMIT 20")
        messages = client.chat.completions.create.call_args.kwargs["messages"]
        self.assertEqual([m["content"] for m in messages if m["role"] == "user"],
                         ["Listá las leyes"])
        self.assertEqual(json.loads(messages[-1]["content"]), rows)
        self.assertEqual(messages[-1]["role"], "tool")

    def test_tenth_law_survives_history_rewriting(self):
        from chat.skills import rag_skill
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Qué dice la Ley 25.675"))])
        history = [{"role": "assistant", "content": "Ley 25.390. " * 60 + "10. Ley 25.675"}]
        with patch.object(rag_skill, "_get_openai_client", return_value=client):
            result = rag_skill.rewrite_query_with_history("La décima", history)
        self.assertIn("25.675", result)
        self.assertIn("10. Ley 25.675", client.chat.completions.create.call_args.kwargs["messages"][-1]["content"])

    def test_followup_uses_exact_law_before_semantic_search(self):
        from chat.skills import rag_skill
        chunk = {"tipo_norma": "LEY", "numero_norma": "25675", "text": "Texto ambiental"}
        with patch.object(rag_skill, "rewrite_query_with_history", return_value="Ley 25.675"), \
             patch.object(rag_skill, "lookup_laws", return_value=[chunk]) as lookup, \
             patch.object(rag_skill, "search") as search, \
             patch.object(rag_skill, "generate_response", return_value="Respuesta"):
            response, sources = rag_skill.query("La décima", [{"role": "assistant", "content": "Listado"}])
        lookup.assert_called_once_with("Ley 25.675", rag_skill.DB_PATH)
        search.assert_not_called()
        self.assertEqual(sources[0]["numero"], "25675")

    def test_rag_separates_user_from_retrieved_documents(self):
        from chat.skills import rag_skill
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Respuesta"))])
        with patch.object(rag_skill, "_get_openai_client", return_value=client), \
             patch.object(rag_skill, "count_tokens", return_value=10), \
             patch.object(rag_skill, "estimate_chunks_tokens", return_value=10):
            rag_skill.generate_response("Qué dice esa ley", [
                {"tipo_norma": "LEY", "numero_norma": "25675", "text": "Texto documental"}])
        messages = client.chat.completions.create.call_args.kwargs["messages"]
        self.assertEqual(messages[-3], {"role": "user", "content": "Qué dice esa ley"})
        self.assertEqual(messages[-1]["role"], "tool")
        self.assertIn("Texto documental", messages[-1]["content"])


if __name__ == "__main__":
    unittest.main()
