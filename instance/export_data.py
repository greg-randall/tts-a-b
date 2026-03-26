"""Export sanitized CSVs from the database (no IP addresses)."""
import csv
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tts_testing.db")
OUT_DIR = os.path.dirname(__file__)


def export():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    with con:
        voices = con.execute("SELECT * FROM voices ORDER BY rating DESC").fetchall()
        results = con.execute(
            "SELECT id, timestamp, voice_a_name, voice_b_name, chosen_voice_name FROM test_results ORDER BY id"
        ).fetchall()

    voices_path = os.path.join(OUT_DIR, "voices.csv")
    with open(voices_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=voices[0].keys())
        w.writeheader()
        w.writerows(dict(r) for r in voices)
    print(f"Wrote {len(voices)} rows to {voices_path}")

    results_path = os.path.join(OUT_DIR, "results.csv")
    with open(results_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(dict(r) for r in results)
    print(f"Wrote {len(results)} rows to {results_path}")

    con.close()


if __name__ == "__main__":
    export()
