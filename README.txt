# Canonical Terminology Translator

This project provides an automated, terminology-consistent translation pipeline specifically designed for gaming localization. It uses a hybrid approach that combines strict rule-based terminology management with context-aware Large Language Model (LLM) translations, enriched by historical style references.

## Key Features

- **Strict Terminology Enforcement:** Uses a curated CSV-based glossary to ensure canonical terms are translated consistently across all target languages.
- **Contextual Retrieval (RAG-like):** Automatically searches legacy translation mappings to provide the LLM with relevant historical examples for style and tone consistency.
- **Hybrid Placeholder System:** Injects non-translatable placeholders into the source text to protect terminology, then restores them after LLM translation.
- **Multi-Language Support:** Simultaneously translates Japanese into English, Simplified Chinese, and Traditional Chinese.
- **Config-Driven Architecture:** All language settings and column mappings are managed via a central YAML configuration.

## Project Structure

- `translate_pipeline.py`: The main entry point that orchestrates the translation flow.
- `lib/terminology.py`: Manages the curated terminology glossary and placeholder logic.
- `lib/retriever.py`: Indexes legacy CSVs and retrieves relevant style examples.
- `lib/llm_translator.py`: Handles interaction with the Google Gemini LLM using LangChain.
- `config/config.yaml`: Central configuration for languages and data mappings.
- `data/`: Contains the curated terminology glossary CSV.
- `legacy_mapping/`: Contains historical translation files used for style reference.

## Setup Instructions

1. **Prerequisites:** Python 3.10+
2. **Create a Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirement.txt
   ```
4. **Environment Variables:**
   Create a `.env` file in the root directory and add your Google API key:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

## Usage

### Running the Translation Pipeline

To translate Japanese sentences into all configured target languages (English, Simplified Chinese, Traditional Chinese), run:

```bash
python3 translate_pipeline.py
```

The pipeline will:
1. Detect canonical terms in the Japanese input.
2. Retrieve the top-3 most relevant style examples for each target language from the `legacy_mapping/` directory.
3. Call the Gemini 1.5 Flash model with a terminology-aware prompt.
4. Output the final, consistent translations.

## Configuration

You can customize the languages and column mappings in `config/config.yaml`. The current setup supports:
- **JA:** Japanese (Source)
- **EN:** English (Target)
- **SC:** Simplified Chinese (Target)
- **TC:** Traditional Chinese (Target)

Terminology mappings are pulled from `data/Angland Canonical Terminology - Terminology.csv`. Only terms marked with `keep: Y` are used.
