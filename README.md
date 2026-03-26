# TTS Blind A/B Testing System

A modern, web-based tool for performing blind A/B testing on Text-to-Speech (TTS) voices and ranking them using the Elo rating system.

## Features

- **Blind A/B Testing:** Randomized, unlabeled voice comparisons to eliminate brand bias.
- **Elo Ranking System:** Calculates relative quality scores for each voice based on win/loss history.
- **Targeted Selection:** Intelligent algorithm that pairs voices with similar ratings to refine their relative positions.
- **Ranking Confidence:** Visual indicators and statistical certainty scores (based on match counts).
- **Voice Directory:** Comprehensive list of all voices with descriptions and integrated audio samples.
- **Column Customization:** Persistent "Show/Hide Columns" drawer on the rankings page for a clean, focused view.
- **Audio Normalization:** Built-in tools to ensure consistent loudness across all samples for fair testing.

## Technology Stack

- **Backend:** Python 3 with Flask
- **Database:** SQLite with SQLAlchemy ORM
- **Frontend:** Jinja2 Templates, Vanilla CSS, and JavaScript
- **Audio Processing:** Pydub, Pyloudnorm, and static-ffmpeg (for automatic codec handling)

## Getting Started

### 1. Installation

Clone the repository and install the required Python dependencies:

```bash
pip install -r requirements.txt
```

*Note: All necessary audio codecs (FFmpeg) are automatically managed via the `static-ffmpeg` Python library.*

### 2. Environment Setup

Create a `.env` file in the project root to store your configuration:

```bash
SECRET_KEY=your-secure-random-key
# Optional: Set FLASK_DEBUG=true for development
```

### 3. Running the App

Start the Flask development server:

```bash
python3 app.py
```

Navigate to `http://localhost:8000` in your web browser.

**Production (Gunicorn):** `run.sh` is gitignored as it may contain server-specific paths. A template is provided as `blank.run.sh` — copy it to `run.sh` and fill in your paths before use.

The database (`instance/tts_testing.db`) is automatically created on the first run. Sanitized exports of the voice rankings and vote history (without IP addresses) are available in `instance/voices.csv` and `instance/results.csv`. To regenerate these from a live database:

```bash
python3 instance/export_data.py
```

## Managing TTS Voices

### Adding New Voice Recordings

To add voices to the system, follow these steps:

1. **Prepare Audio:**
   - Place your new audio files (e.g., `.wav`, `.mp3`, `.ogg`, `.flac`, `.m4a`) in the `static/audio/` directory.
   - **Important:** The filename (excluding extension) will be used as the internal `voice_name` in the database.

2. **Normalize Loudness (Crucial for Fair Testing):**
   - Run the normalization script to ensure the new samples match the loudness of existing ones and are converted to `.mp3`:
     ```bash
     python3 normalize.py static/audio/ --overwrite
     ```
   - This script targets -14 LUFS, preventing users from being biased toward louder samples. It uses `static-ffmpeg` to ensure all formats are supported without manual system setup.

3. **Register in Database:**
   ```bash
   python3 bulk_add_voices.py /path/to/audio/ --engine "Kokoro" --description "American Female | Soft, Calm"
   ```
   This copies any new audio files into `static/audio/` and registers them in the database, skipping any that already exist. Point it at `static/audio/` directly if your files are already there.

Once these steps are complete, the new voices will automatically appear in A/B tests and the rankings table.

## Project Structure

- `app.py`: Main application logic and routing.
- `models.py`: Database schema for Voices and Test Results.
- `elo_rankings.py`: The Elo math and targeted pairing logic.
- `static/`:
    - `audio/`: MP3 voice samples (named exactly as registered in the DB).
    - `css/style.css`: Modern, responsive styling.
    - `js/main.js`: Custom audio player and table management.
- `templates/`: HTML layouts for testing, rankings, and the directory.
- `normalize.py`: Audio preprocessing utility with automatic dependency management.
- `instance/export_data.py`: Exports sanitized CSVs from the database (no IP addresses).
- `instance/voices.csv`: Voice rankings and Elo stats (exported, no PII).
- `instance/results.csv`: Raw vote history (exported, no PII).
