"""
generate_samples.py — Generate sample audio files for MomFlow AI.

Run this ONCE from the project root after setting up your .env:
    python generate_samples.py

Generates 5 .mp3 files in data/sample_audio/:
  - 2 English voices
  - 2 Arabic voices
  - 1 off-topic (triggers refusal — important for Loom demo)

Uses OpenAI TTS (tts-1 model, ~$0.001 per file — essentially free).
Requires OPENAI_API_KEY in .env
"""

from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# (filename, text, voice, description)
# nova  = clear female English voice
# shimmer = softer, works well for Arabic
SAMPLES = [
    (
        "en_01_diapers_lotion.mp3",
        "I need Pampers diapers size 4 and baby lotion, I want to get them next week.",
        "nova",
        "English — multi-item with schedule",
    ),
    (
        "en_02_urgent_formula.mp3",
        "I urgently need newborn formula and a baby thermometer today.",
        "nova",
        "English — urgency + schedule",
    ),
    (
        "ar_01_diapers.mp3",
        "أحتاج حفاضات مقاس 3 وكريم الأطفال",
        "shimmer",
        "Arabic — simple request with size",
    ),
    (
        "ar_02_multi.mp3",
        "أحتاج علبتين من حليب نستلي وكريم جونسون للأطفال",
        "shimmer",
        "Arabic — multi-item with brand and quantity",
    ),
    (
        "en_03_offtopic_refusal.mp3",
        "What is the weather like in Dubai today?",
        "nova",
        "Off-topic — should trigger refusal (confidence < 0.5)",
    ),
]

out_dir = Path("data/sample_audio")
out_dir.mkdir(parents=True, exist_ok=True)

print("Generating sample audio files...\n")

for filename, text, voice, description in SAMPLES:
    out_path = out_dir / filename
    print(f"  🎙️  {filename}")
    print(f"      {description}")
    print(f"      Text: \"{text[:60]}{'...' if len(text) > 60 else ''}\"")

    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="mp3",
    )
    response.stream_to_file(out_path)
    print(f"      ✅ Saved to {out_path}\n")

print("Done! All 2 audio files are in data/sample_audio/")
print()
print("Test them with:")
print('  python -m app.main --audio data/sample_audio/ar_test_diapers.mp3')
print('  python -m app.main --audio data/sample_audio/en_test_diapers.mp3')

