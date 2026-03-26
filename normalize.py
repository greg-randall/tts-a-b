import os
from pydub import AudioSegment
from pathlib import Path
import pyloudnorm as pyln
import numpy as np
from static_ffmpeg import add_paths

# Automatically find/download and add ffmpeg to PATH for pydub
add_paths()

def process_audio(input_path, target_lufs=-14, threshold_db=-0.1, overwrite=False):
    """
    Process audio file by:
    1. Loading from any supported format
    2. Normalizing to target LUFS
    3. Applying hard limiter
    4. Exporting back to MP3
    
    Args:
        input_path (str): Path to the input audio file
        target_lufs (float): Target loudness in LUFS
        threshold_db (float): Maximum allowed amplitude in dB
        overwrite (bool): If True, replace original file
    """
    input_path = Path(input_path)
    if overwrite:
        output_path = input_path
        temp_path = input_path.parent / f".temp_{input_path.name}"
    else:
        output_path = input_path.parent / f"processed_{input_path.stem}.mp3"
        temp_path = output_path

    try:
        # Load the audio file (supports various formats)
        audio = AudioSegment.from_file(input_path)
        
        # Get the audio data as numpy array for LUFS processing
        samples = np.array(audio.get_array_of_samples())
        normalized_samples = samples.astype(np.float32) / (1 << (8 * audio.sample_width - 1))
        
        if audio.channels > 1:
            normalized_samples = normalized_samples.reshape(-1, audio.channels)
        
        # Measure LUFS
        meter = pyln.Meter(audio.frame_rate)
        current_loudness = meter.integrated_loudness(normalized_samples)
        
        # Calculate and apply loudness adjustment
        loudness_gain = target_lufs - current_loudness

        # Optimization: Skip if already at target loudness and already an MP3
        # This prevents generation loss from re-encoding and saves time.
        if abs(loudness_gain) < 0.1 and input_path.suffix.lower() == '.mp3':
            print(f"Skipped {input_path.name} (already normalized at {current_loudness:.1f} LUFS)")
            return
        
        audio = audio.apply_gain(loudness_gain)
        
        # Apply limiter
        if audio.dBFS > threshold_db:
            reduction_db = threshold_db - audio.dBFS
            audio = audio.apply_gain(reduction_db)
        
        # Export to temporary file first (always exporting as MP3 for consistency in this project)
        audio.export(str(temp_path), format="mp3", parameters=["-q:a", "0"])
        
        if overwrite and temp_path != output_path:
            # Atomic replace of original file if formats match, or just remove original
            if input_path.suffix.lower() == '.mp3':
                temp_path.replace(output_path)
            else:
                # If we are overwriting a non-mp3 with an mp3, we should probably delete the original
                # but overwrite logic usually implies "replace this entry". 
                # For safety in this script, we'll replace the content.
                output_path = input_path.with_suffix('.mp3')
                temp_path.replace(output_path)
                if input_path != output_path:
                    input_path.unlink()
        
        print(f"Processed {input_path.name}:")
        print(f"  - Original loudness: {current_loudness:.1f} LUFS")
        print(f"  - Applied gain: {loudness_gain:.1f} dB")
        if audio.dBFS > threshold_db:
            print(f"  - Limited peaks to {threshold_db} dB")
        
    except Exception as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        print(f"Error processing {input_path}: {str(e)}")

def process_directory(directory_path, target_lufs=-14, threshold_db=-0.1, overwrite=False):
    """
    Process all supported audio files in a directory.
    
    Args:
        directory_path (str): Path to the directory containing audio files
        target_lufs (float): Target loudness in LUFS
        threshold_db (float): Maximum allowed amplitude in dB
        overwrite (bool): If True, replace original files
    """
    directory = Path(directory_path)
    if not directory.exists():
        print(f"Directory {directory_path} does not exist!")
        return
    
    extensions = [".mp3", ".wav", ".ogg", ".flac", ".m4a"]
    audio_files = [f for f in directory.iterdir() if f.suffix.lower() in extensions and not f.name.startswith('.')]
    
    if not audio_files:
        print(f"No audio files ({', '.join(extensions)}) found in the directory!")
        return
    
    print(f"Found {len(audio_files)} audio files to process...")
    print(f"Target loudness: {target_lufs} LUFS")
    print(f"Peak limit: {threshold_db} dB")
    print(f"Overwrite mode: {'enabled' if overwrite else 'disabled'}")
    print()
    
    for audio_file in audio_files:
        process_audio(str(audio_file), target_lufs, threshold_db, overwrite)
    
    print("\nProcessing complete!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process audio files with minimal quality loss")
    parser.add_argument("directory", help="Directory containing MP3 files")
    parser.add_argument("--target-lufs", type=float, default=-14,
                      help="Target loudness in LUFS (default: -14)")
    parser.add_argument("--threshold-db", type=float, default=-0.1,
                      help="Maximum allowed amplitude in dB (default: -0.1)")
    parser.add_argument("--overwrite", action="store_true",
                      help="Replace original files instead of creating new ones")
    
    args = parser.parse_args()
    process_directory(args.directory, args.target_lufs, args.threshold_db, args.overwrite)