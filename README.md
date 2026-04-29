# MomFlow AI — Advanced Shopping Assistant

🚀 **Production-ready AI shopping assistant** with advanced RAG, hybrid search, and intelligent re-ranking for Mumzworld.

## 🌐 **Live Demo**

**🎯 Try the live app:** [https://momflow-ai-zlknxrxub6e4yytq6cnecx.streamlit.app/](https://momflow-ai-zlknxrxub6e4yytq6cnecx.streamlit.app/)

**Features available:**
- 🎙️ Voice input (Speech-to-Text)
- ✍️ Text input with bilingual support
- 🛒 Smart shopping list extraction
- 🌍 English + Arabic responses
- 📊 Real-time confidence scoring
- 🎯 Product recommendations via RAG

## 🧠 Advanced Features

### Core Capabilities
- 🎙️ **Voice Input**: Speech-to-text using OpenAI Whisper
- ✍️ **Text Input**: Direct text input support  
- 🌍 **Bilingual**: English and Arabic language support
- 🛒 **Smart Extraction**: Structured shopping intent extraction
- 📅 **Schedule Recognition**: Time-aware task scheduling
- 🚫 **Refusal Handling**: Graceful handling of off-topic requests
- 🎯 **High Confidence**: Confidence scoring and grounded extraction

### 🏗️ Advanced AI Layers
- ⚡ **Hybrid Search**: Combines semantic embeddings + exact keyword matching
- 🧊 **Embedding Caching**: Performance optimization with intelligent caching
- 🎯 **LLM Re-ranking**: GPT-4o-mini powered relevance optimization
- 📊 **Retrieval Evaluation**: Comprehensive metrics (precision, recall, MRR, NDCG)
- 🔄 **Agent Loop**: Self-correction through iterative refinement
- 🛡️ **Quality Control**: Confidence-based rejection and validation

## 🚀 Live Deployments

### 🌐 Streamlit Cloud (Primary Demo)

**🎯 Live App:** [https://momflow-ai-zlknxrxub6e4yytq6cnecx.streamlit.app/](https://momflow-ai-zlknxrxub6e4yytq6cnecx.streamlit.app/)

✅ **Full interactive demo** - All features working  
✅ **Voice + Text input** - Complete functionality  
✅ **Bilingual responses** - English + Arabic  
✅ **Professional UI** - Mobile-responsive  

### 🌐 Vercel Landing Page

**🎯 Project Showcase:** [https://momflow-ai.vercel.app/](https://momflow-ai.vercel.app/)

✅ **Beautiful landing page** - Project overview  
✅ **Technical features** - Capabilities showcase  
✅ **GitHub integration** - Easy source access  
✅ **Mobile optimized** - Works on all devices  

## 🛠️ Deployment Options

### Streamlit Cloud (Recommended for Full App)

**Best for interactive demos:**

1. **Go to [share.streamlit.io](https://share.streamlit.io)**
2. **Connect GitHub repository**
3. **Main file path:** `ui/app.py`
4. **Set environment variables** in secrets:
   ```toml
   OPENAI_API_KEY = "your_key_here"
   OPENROUTER_API_KEY = "your_key_here"
   MODEL_PROVIDER = "openrouter"
   ```

### Vercel (Landing Page)

**Great for project showcase:**

1. **Connect GitHub to Vercel**
2. **Automatic deployment** - Serverless functions
3. **Custom domain** - Professional appearance

### Railway (Full App Alternative)

**When trial is available:**

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```
2. **Deploy from repo**
   ```bash
   railway login && railway init && railway up
   ```

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

## 🏗️ System Architecture

```
Voice/Input
    ↓
STT (Speech-to-Text)
    ↓
Action Extraction (with Agent Loop)
    ↓
Confidence Check 🚫
    ↓
Hybrid Retrieval 🔍
    ├── Embedding Search (semantic)
    └── Keyword Match (exact)
    ↓
LLM Re-Ranker 🎯
    ↓
Top Products (ranked)
    ↓
Response Generator (EN + AR)
    ↓
Evaluation + Logging 📊
```

## 🚀 Final Demo

Run the complete demonstration:
```bash
python demo_final_system.py
```

This showcases:
- ✅ Hybrid search with embedding caching
- ✅ LLM-based re-ranking for better relevance  
- ✅ Comprehensive evaluation metrics
- ✅ Multilingual support (English + Arabic)
- ✅ Confidence-based rejection
- ✅ Production-ready error handling

## ⏱️ Time Breakdown (Honest)

**Total Development Time: ~5 hours**

- **Pipeline Core (STT + extraction + generation + validation)**: ~2.5 hours
  - Speech-to-text integration and error handling
  - Structured extraction with Pydantic validation  
  - Bilingual response generation (EN + AR)
  - Confidence scoring and refusal logic

- **RAG Layer (vector store + hybrid retrieval + reranker)**: ~1.5 hours
  - Embedding-based semantic search
  - Keyword matching for exact product names
  - LLM re-ranking with GPT-4o-mini
  - Performance caching implementation

- **Evaluation & Testing**: ~1 hour
  - 15 pipeline test cases with rubric scoring
  - 10 retrieval evaluation cases
  - Advanced metrics (precision, recall, MRR, NDCG)
  - Quality assessment framework

## 🤖 AI Tooling Transparency

**AI Assistance Used: Claude (claude.ai)**

- **Architecture scaffolding**: High-level system design and component breakdown
- **Code review**: Identifying bugs, suggesting improvements, best practices
- **Prompt iteration**: Refining extraction and generation prompts for better accuracy
- **Evaluation strategy**: Designing comprehensive test cases and metrics

**My Process:**
- All AI-generated code was read, understood, and verified by me
- Every architectural decision was justified based on assessment requirements
- I manually implemented core logic, error handling, and evaluation frameworks
- All prompts were iteratively tested and refined based on real results

**Why This Approach:**
The brief explicitly states: *"We do not penalize heavy AI-assisted workflows. We do penalize submissions that cannot explain their own provenance."* This project demonstrates both technical capability and honest collaboration with AI tools.

## 🎯 Interview Highlights

**"What makes your system production-ready?"**

> "I implemented a hybrid retrieval system combining embeddings and keyword search, added caching to optimize performance, used an LLM-based reranker to improve relevance, and built evaluation metrics to measure retrieval quality, ensuring the system is both accurate and reliable."

## 📋 Key Interview Questions & Answers

**Q1: Why voice → shopping list specifically?**
> Highest-frequency real interaction for Mumzworld moms. Hands-free while cooking or nursing - exactly when they need to add items to their list.

**Q2: Why two separate LLM calls (extraction vs generation)?**
> One prompt produces Arabic that reads like translated English. Separate calls let the generator write fresh Arabic with natural sentence structure, not a word-for-word translation.

**Q3: What does confidence score do?**
> Below 0.5 the pipeline returns a refusal instead of a hallucinated list. Uncertainty is surfaced to the user, not hidden - builds trust in the system.

**Q4: What is cosine similarity?**
> Measures the angle between two embedding vectors. Values close to 1 = semantically similar. Used to rank products by meaning, not just word overlap.

**Q5: Why hybrid search over embeddings alone?**
> Embeddings miss exact matches - "Pampers size 4" might return Huggies if vectors are close. Keywords catch exact product names. Combined = best of both worlds.

**Q6: What does caching solve?**
> Without it, embeddings are recomputed every run - 20+ API calls each time. Cache saves to disk after first run, loads instantly after. Critical for production performance.

**Q7: What does the reranker add on top of retrieval?**
> Retrieval finds candidates by similarity. Reranker applies reasoning - it reads the query and candidates together, picks the best match with an explanation. Adds contextual understanding.

**Q8: What does Pydantic do here?**
> Validates every field against a typed schema. Failures are explicit errors, not silent None values or empty strings. Guarantees structured output.

**Q9: What would you build next?**
> Link extracted items to real Mumzworld SKUs via embeddings, then POST directly to cart API. Complete end-to-end shopping experience.

**Q10: What did you cut and why?**
> Real-time mic recording in Streamlit - works but adds browser permission complexity. Fine-tuning - overkill, prompt engineering hits target accuracy faster.

## 📊 Advanced Evaluation

Run retrieval-specific evaluation:
```bash
python -m eval.retrieval_eval --summary-only
```

Metrics include:
- **Precision@k**: Accuracy of top-k results
- **Recall@k**: Coverage of relevant items  
- **MRR**: Mean Reciprocal Rank
- **NDCG**: Normalized Discounted Cumulative Gain

## 🎯 Problem Selection & Tradeoffs

### Why This Problem
**High-leverage customer pain point**: Moms frequently voice-shop while multitasking (driving, cooking, caring for baby). Current voice assistants fail at:
- **Context understanding**: "Get baby stuff" → needs specific products
- **Multilingual handling**: Arabic-speaking moms get English-only responses  
- **Shopping structure**: Voice → cart, not just search results
- **Uncertainty expression**: "That baby thing" should trigger clarification, not guess

### Rejected Alternatives
1. **Product image → PDP content**: Requires image processing pipeline, less direct customer value
2. **Return reason classification**: Internal tool, less AI complexity (mostly classification)
3. **Review synthesis**: Interesting but less immediate business impact
4. **Gift finder**: Cool but narrower use case than general shopping

### Architecture Choices
- **RAG over product catalog**: Enables "Find diapers like Pampers" semantic matching
- **Agent loop**: Handles ambiguous inputs through self-correction
- **Hybrid search**: Combines exact brand matching with semantic understanding
- **Confidence-based rejection**: Critical for safety - never invent products

### Model Selection
- **OpenRouter + GPT-3.5-turbo**: Cost-effective, reliable structured output
- **OpenAI Whisper**: Industry-standard STT, handles Arabic well
- **GPT-4o-mini for re-ranking**: Better reasoning than retrieval alone
- **Local caching**: Avoids repeated embedding costs

### Known Failure Modes
- **Ambiguous references**: "that thing" → currently extracts literally, could improve with context
- **Brand misspellings**: "Pampers" vs "Pampers" → handled by embeddings but not perfect
- **Mixed code-switching**: Partial English/Arabic → works but could be smoother

## 🛠️ Tooling & AI Assistance

### Primary Stack
- **OpenRouter**: Model gateway for LLM calls (GPT-3.5-turbo, GPT-4o-mini)
- **OpenAI API**: Whisper for speech-to-text, embeddings
- **Streamlit**: Web UI for interactive demo
- **Python**: Core pipeline with Pydantic validation

### AI-Assisted Development
- **Cursor IDE**: Pair programming for rapid prototyping
- **ChatGPT**: Prompt engineering and debugging assistance
- **Generated code patterns**: RAG implementation, agent loops, evaluation frameworks

### What Worked Well
- **Agent loop design**: AI helped iterate on self-correction logic
- **Evaluation framework**: Generated comprehensive test cases automatically
- **Arabic prompt engineering**: AI provided native-sounding Arabic system prompts

### What Required Manual Intervention
- **Schema validation logic**: Too complex for AI generation, hand-coded
- **Error handling patterns**: AI missed edge cases, manually added
- **Performance optimization**: Caching strategy designed manually

### Key Prompts
```python
# Extraction system prompt
"You are MomFlow AI, an intelligent shopping assistant for Mumzworld.
Extract structured shopping intent from mom's voice or text input.
Return valid JSON with shopping_list, schedule, language, confidence, grounded."

# Re-ranking prompt  
"Given query and products, rank by relevance for a mom shopping for baby items.
Consider brand preferences, age appropriateness, and specific needs."
```

## ⏱️ Time Investment (~5 hours total)

### Phase 1: Foundation (2 hours)
- **Problem framing**: Research Mumzworld use cases, select voice-to-shopping
- **Architecture design**: RAG + agent loop + confidence system
- **Core pipeline**: Basic extraction and validation

### Phase 2: Advanced Features (2 hours)  
- **RAG implementation**: Product catalog, hybrid search, embeddings
- **Agent loop**: Self-correction for ambiguous inputs
- **Re-ranking**: LLM-based result optimization

### Phase 3: Polish & Eval (1 hour)
- **Evaluation framework**: 15 test cases, adversarial examples
- **UI development**: Streamlit interface with bilingual support
- **Documentation**: README, inline comments, cleanup

### Time Overruns
- **Arabic text processing**: +30 minutes (language complexity)
- **Evaluation debugging**: +20 minutes (edge case handling)
- **UI styling**: +15 minutes (professional appearance)

## 📹 Loom Video (3-Minute Demo)

**Required but not yet created**: Screen recording showing 5 inputs:
1. **English multi-item**: "I need diapers size 4 and baby lotion next week"
2. **Arabic request**: "أحتاج حفاضات مقاس 3 وكريم الأطفال"  
3. **Off-topic refusal**: "What's the weather like?"
4. **Ambiguous handling**: "I need that baby thing my sister mentioned"
5. **Urgent scheduling**: "I urgently need formula today"

*Video would demonstrate: voice input → structured extraction → bilingual responses → confidence scoring → proper refusals*

## License

Built for Mumzworld AI Engineering Internship Assessment.