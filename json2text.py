import json
import argparse
import sys
from pathlib import Path


# This output was created by 
# https://replicate.com/thomasmol/whisper-diarization?prediction=q67rrcg4n1rgg0ck8prvm0gnfc&output=json
# My prompt

# Create a python script that take a file as a command line argument  using the "segmemts" section and the "text', "speaker" and "start" fields to create a transcript sequenced by "start" which is time in seconds. 

# -- sample input --

# { "output": { "segments":[
# { "text": "hi there",
# "start: "1",
# "speaker": "SPEAKER_01",
# },
# { "text": "how are you doing?",
# "start: "2",
# "speaker": "SPEAKER_01"
# },
# { "text": "I'm great thanks! How are you?",
# "start: "3",
# "speaker": "SPEAKER_00"
# },
# { "text": "Bonza!",
# "start: "4",
# "speaker": "SPEAKER_01"
# },
# ]}}

# -- expected output --

# SPEAKER_01: hi there how are you doing?

# SPEAKER_00: I'm great thanks!

# SPEAKER_01: Bonza!




def create_transcript(json_file_path, speaker_labels=None):
    """
    Creates a transcript from a JSON file containing speech segments.

    Args:
        json_file_path: Path to the JSON file.
        speaker_labels: Optional dictionary to replace speaker labels.

    Returns:
        A string containing the formatted transcript, or None if an error occurs.
    """
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not load JSON file '{json_file_path}': {e}", file=sys.stderr)
        return None

    try:
        segments = data['output']['segments']
    except KeyError as e:
        print(f"Error: JSON file does not contain the expected 'output.segments' key: {e}", file=sys.stderr)
        return None

    # Sort segments by start time
    segments.sort(key=lambda x: float(x['start']))

    transcript = ""
    current_speaker = None
    for segment in segments:
        speaker = segment['speaker']
        if speaker_labels and speaker in speaker_labels:
            speaker = speaker_labels[speaker]
        text = segment['text']
        if speaker != current_speaker:
            if current_speaker:
                transcript += "\n"
            transcript += f"{speaker}: {text} "
            current_speaker = speaker
        else:
            transcript += text + " "

    return transcript.strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a transcript from a JSON file.")
    parser.add_argument("json_file", help="Path to the JSON file.")
    parser.add_argument("--output", help="Path to the output file.")
    parser.add_argument("--speakers", nargs='+', help="List of speaker labels to replace the default ones.")
    args = parser.parse_args()

    # Determine output file path
    input_path = Path(args.json_file)
    output_path = Path(args.output) if args.output else input_path.with_suffix('.txt')

    # Create speaker label mapping if provided
    speaker_labels = None
    if args.speakers:
        speaker_labels = {f"SPEAKER_{str(i).zfill(2)}": label for i, label in enumerate(args.speakers)}

    transcript = create_transcript(args.json_file, speaker_labels)
    if transcript:
        with open(output_path, 'w') as f:
            f.write(transcript)
        print(f"Transcript written to {output_path}")
