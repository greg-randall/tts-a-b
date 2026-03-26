import shutil
import argparse
from pathlib import Path
from app import app
from models import db, Voice

AUDIO_DIR = Path(__file__).parent / "static" / "audio"


def bulk_add_voices(directory_path, engine, description, skip_normalize=False):
    """
    Scans a directory for audio files, copies them into static/audio/,
    and adds them as new voices to the database.
    """
    directory = Path(directory_path).resolve()
    if not directory.exists():
        print(f"Directory {directory_path} does not exist!")
        return

    # Supported formats
    extensions = [".mp3", ".wav", ".ogg", ".flac", ".m4a"]
    audio_files = [f for f in directory.iterdir() if f.suffix.lower() in extensions and not f.name.startswith('.')]

    if not audio_files:
        print(f"No audio files ({', '.join(extensions)}) found in the directory!")
        return

    print(f"Found {len(audio_files)} audio files. Copying and adding to database...")

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    with app.app_context():
        added_count = 0
        already_exists_count = 0

        for audio_file in audio_files:
            voice_name = audio_file.stem
            dest = AUDIO_DIR / audio_file.name

            # Copy file unless source and destination are the same path
            if audio_file.resolve() != dest.resolve():
                if dest.exists():
                    print(f"  ~ File already in static/audio/, skipping copy: {audio_file.name}")
                else:
                    shutil.copy2(audio_file, dest)
                    print(f"  > Copied: {audio_file.name}")

            existing = Voice.query.filter_by(name=voice_name).first()
            if not existing:
                new_voice = Voice(
                    name=voice_name,
                    engine=engine,
                    description=description
                )
                db.session.add(new_voice)
                added_count += 1
                print(f"  + Added to DB: {voice_name}")
            else:
                already_exists_count += 1

        db.session.commit()
        print(f"\nFinished! Added {added_count} new voices.")
        if already_exists_count > 0:
            print(f"Skipped {already_exists_count} voices that already exist in the database.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk add voices from a directory to the TTS database.")
    parser.add_argument("directory", help="Directory containing audio files")
    parser.add_argument("--engine", default="Unknown", help="Default engine name for these voices (e.g., 'Kokoro')")
    parser.add_argument("--description", default="", help="Default description for these voices")

    args = parser.parse_args()
    bulk_add_voices(args.directory, args.engine, args.description)
