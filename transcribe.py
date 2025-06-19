# transcribe.py

import sys
import whisper

# Get the file path from command line argument
audio_path = sys.argv[1]

model = whisper.load_model("base")  # or "small", "medium"
result = model.transcribe(audio_path)

# Print transcription to stdout so Node.js can read it
print(result["text"])
