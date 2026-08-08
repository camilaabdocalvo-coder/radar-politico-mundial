import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collector import normalize, rank, similarity, tokens


class CollectorTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize("Política: eleição!"), "politica eleicao")

    def test_similarity(self):
        self.assertGreater(similarity(tokens("Presidente anuncia nova política"), tokens("Presidente anuncia política nova")), .7)

    def test_rank_prefers_cross_source_story(self):
        now = datetime.now(timezone.utc)
        base = {"id": "1", "title": "Governo anuncia política no Congresso", "url": "https://a", "feed": "A", "priority": 1.0, "published_at": now.isoformat(), "_published": now, "_tokens": tokens("Governo anuncia política no Congresso")}
        other = {**base, "id": "2", "url": "https://b", "source": "B"}
        base["source"] = "A"
        unrelated = {**base, "id": "3", "title": "Eleição internacional tem resultado", "url": "https://c", "source": "C", "_tokens": tokens("Eleição internacional tem resultado")}
        result = rank([base, other, unrelated], now)
        self.assertEqual(result[0]["signals"]["source_count"], 2)


if __name__ == "__main__":
    unittest.main()
