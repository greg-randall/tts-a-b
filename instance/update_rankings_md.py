import csv
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "instance", "voices.csv")
MD_PATH = os.path.join(BASE_DIR, "RANKINGS.md")

def generate_md():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found. Run 'python3 instance/export_data.py' first.")
        return

    with open(CSV_PATH, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = sorted(list(reader), key=lambda x: float(x.get('rating', 0) or 0), reverse=True)

    with open(MD_PATH, "w") as f:
        f.write("# TTS Voice Rankings (Static Export)\n\n")
        f.write("This table is a snapshot of the current Elo rankings exported from the database. ")
        f.write("For the live, interactive rankings with audio samples, visit [gregr.org/tts-a-b/results](https://gregr.org/tts-a-b/results).\n\n")
        
        # Table Header
        f.write("| Rank | Voice | Engine | Rating | ± | Description | Matches | Record | Win % | Confidence |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        
        for i, row in enumerate(rows, 1):
            name = row.get('name', 'Unknown')
            engine = row.get('engine', 'Unknown')
            rating = round(float(row.get('rating', 1000.0) or 1000.0))
            
            try:
                conf = round(float(row.get('confidence_interval', 0) or 0))
                conf_str = f"±{conf}"
            except ValueError:
                conf_str = "-"

            desc = row.get('description', '')
            matches = row.get('matches', 0)
            wins = row.get('wins', 0)
            losses = row.get('losses', 0)
            record = f"{wins}-{losses}"
            
            try:
                wr_val = float(row.get('win_rate') or 0.0)
                win_rate = f"{wr_val:.1f}%"
            except ValueError:
                win_rate = "0.0%"

            try:
                rel_val = float(row.get('reliability') or 0.0)
                reliability = f"{rel_val:.0f}%"
            except ValueError:
                reliability = "0%"
            
            f.write(f"| {i} | **{name}** | {engine} | {rating} | {conf_str} | {desc} | {matches} | {record} | {win_rate} | {reliability} |\n")

    print(f"Successfully generated {MD_PATH} from {len(rows)} voices.")

if __name__ == "__main__":
    generate_md()
