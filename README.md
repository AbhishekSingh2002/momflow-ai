# MomFlow AI — Mumzworld Shopping Assistant

An intelligent voice and text shopping assistant for Mumzworld, the Middle East's largest e-commerce platform for mothers and babies. Supports both English and Arabic inputs.

## Features

- 🎙️ **Voice Input**: Speech-to-text using OpenAI Whisper
- ✍️ **Text Input**: Direct text input support
- 🌍 **Bilingual**: English and Arabic language support
- 🛒 **Smart Extraction**: Structured shopping intent extraction
- 📅 **Schedule Recognition**: Time-aware task scheduling
- 🚫 **Refusal Handling**: Graceful handling of off-topic requests
- 🎯 **High Confidence**: Confidence scoring and grounded extraction

## Quick Start

1. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate sample audio files**
   ```bash
   python generate_samples.py
   ```

4. **Test the pipeline**
   ```bash
   # Audio input
   python -m app.main --audio data/sample_audio/en_01_diapers_lotion.mp3
   
   # Text input
   python -m app.main --text "I need diapers size 4 and baby lotion next week"
   ```

5. **Run the Streamlit UI**
   ```bash
   streamlit run ui/app.py
   ```

6. **Run evaluation**
   ```bash
   python -m eval.evaluator
   ```

## Project Structure

```
momflow-ai/
├── generate_samples.py        # Generate sample audio files
├── .env.example               # Environment variables template
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── app/                       # Core application modules
│   ├── __init__.py
│   ├── config.py              # Provider configuration
│   ├── main.py                # Pipeline orchestrator
│   ├── schema.py              # Pydantic models
│   ├── extractor.py           # LLM extraction
│   ├── generator.py           # Bilingual responses
│   ├── stt.py                 # Speech-to-text
│   └── validator.py           # Schema validation
├── prompts/
│   └── extraction_prompt.txt  # System prompt for extraction
├── data/
│   ├── test_cases.json        # Evaluation test cases
│   └── sample_audio/          # Generated audio samples
├── eval/
│   └── evaluator.py           # Evaluation harness
└── ui/
    └── app.py                 # Streamlit interface
```

## Usage Examples

### Command Line Interface

```bash
# Audio input with auto language detection
python -m app.main --audio path/to/audio.mp3

# Text input with language hint
python -m app.main --text "I need diapers size 4" --lang en

# Arabic text input
python -m app.main --text "اشتري حفاضات مقاس 3" --lang ar
```

### Streamlit UI

Run the web interface:
```bash
streamlit run ui/app.py
```

Features:
- Text input mode
- Audio file upload
- Real-time pipeline display
- Bilingual output display
- Confidence scoring

### Evaluation

Run the evaluation harness:
```bash
# Run all test cases
python -m eval.evaluator

# Run specific tag cases
python -m eval.evaluator --tag adversarial

# Save evaluation report
python -m eval.evaluator --save
```

## Output Format

The system returns structured JSON with the following fields:

```json
{
  "shopping_list": [
    {
      "item": "diapers",
      "details": "size 4",
      "quantity": 2
    }
  ],
  "schedule": [
    {
      "task": "Buy diapers size 4",
      "date": "next week"
    }
  ],
  "language": "en",
  "confidence": 0.85,
  "grounded": true,
  "response_en": "I've added diapers size 4 to your shopping list...",
  "response_ar": "لقد أضفت حفاضات مقاس 4 إلى قائمة تسوقك..."
}
```

## Configuration

The system supports multiple LLM providers:

- **OpenAI**: GPT-4o-mini for extraction, tts-1 for speech synthesis
- **OpenRouter**: Alternative provider with model selection

Configure in `.env`:
```bash
MODEL_PROVIDER=openai
EXTRACTION_MODEL=gpt-4o-mini
```

## Evaluation Rubric

Each test case is scored on 5 criteria (max 5 points):
1. **Item recall** - Expected items found in shopping_list
2. **No hallucination** - No items invented beyond user input
3. **Refusal correctness** - Refusal returned iff expected
4. **Confidence range** - Confidence within expected bounds
5. **Schema validity** - Output validates against schema

## Development

### Adding New Test Cases

Edit `data/test_cases.json` following the existing format:

```json
{
  "id": "test_001",
  "description": "Test description",
  "input": "User input text",
  "language_hint": "en",
  "expected_items": ["item1", "item2"],
  "expect_refusal": false,
  "min_confidence": 0.7,
  "tags": ["easy", "english"]
}
```

### Custom Prompts

Edit `prompts/extraction_prompt.txt` to modify the extraction behavior. The prompt is versioned separately from the code.

## License

Built for Mumzworld AI Engineering Internship Assessment.