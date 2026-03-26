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
        # Sort by rating descending (CSV should already be sorted, but let's be safe)
        rows = sorted(list(reader), key=lambda x: float(x['rating']), reverse=True)

    with open(MD_PATH, "w") as f:
        f.write("# TTS Voice Rankings (Static Export)\n\n")
        f.write("This table is a snapshot of the current Elo rankings exported from the database. ")
        f.write("For the live, interactive rankings, visit [gregr.org/tts-a-b/results](https://gregr.org/tts-a-b/results).\n\n")
        
        # Table Header
        f.write("| Rank | Voice | Engine | Rating | Matches | Win Rate |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        
        for i, row in enumerate(rows, 1):
            name = row['name']
            engine = row['engine']
            rating = round(float(row.get('rating', 1000.0) or 1000.0))
            matches = row.get('matches', 0)
            
            try:
                wr_val = float(row.get('win_rate') or 0.0)
                win_rate = f"{wr_val:.1f}%"
            except ValueError:
                win_rate = "0.0%"
            
            f.write(f"| {i} | **{name}** | {engine} | {rating} | {matches} | {win_rate} |\n")

    print(f"Successfully generated {MD_PATH} from {len(rows)} voices.")

if __name__ == "__main__":
    generate_md()
