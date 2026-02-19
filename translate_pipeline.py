import asyncio
import os
import yaml
from lib.terminology import TerminologyManager
from lib.retriever import LegacyRetriever
from lib.llm_translator import LangChainLLMTranslator
from dotenv import load_dotenv

load_dotenv()

# Configuration Paths
CONFIG_PATH = "config/config.yaml"
TERMINOLOGY_CSV = "data/Angland Canonical Terminology - Terminology.csv"
LEGACY_DIR = "legacy_mapping"

class TranslationPipeline:
    def __init__(self):
        # 1. Load Configuration
        with open(CONFIG_PATH, 'r') as f:
            config_data = yaml.safe_load(f)
        self.lang_configs = config_data['Language']
        
        # 2. Initialize Managers
        self.term_manager = TerminologyManager(TERMINOLOGY_CSV, self.lang_configs)
        self.retriever = LegacyRetriever(LEGACY_DIR, self.lang_configs)
        self.translator = LangChainLLMTranslator()

    async def translate_single(self, ja_text, target_lang_code):
        """Translates a single JA sentence to a specific target language."""
        lang_config = self.lang_configs[target_lang_code]
        target_fullname = lang_config['fullname']
        
        # 1. Terminology Detection & Placeholder Injection
        placeholder_text, placeholder_map = self.term_manager.apply_placeholders(ja_text, target_lang_code)
        
        # 2. Legacy Context Retrieval
        examples = self.retriever.retrieve(ja_text, target_lang_code, top_k=3)
        
        # 3. Prompt Data Preparation
        glossary_info = self.term_manager.get_glossary_for_prompt(placeholder_map)
        examples_info = self.retriever.format_examples_for_prompt(examples, target_fullname)
        
        # 4. LLM Translation
        translated_text = await self.translator.translate(
            placeholder_text, 
            target_fullname, 
            glossary_info, 
            examples_info
        )
        
        # 5. Placeholder Restoration
        final_text = self.term_manager.restore_placeholders(translated_text, placeholder_map)
        
        return final_text

    async def translate_all(self, ja_text):
        """Translates a JA sentence to all target languages defined in config."""
        print(f"\n--- Translating JA: {ja_text} ---")
        
        results = {"JA": ja_text}
        
        # Define target languages (everything except JA)
        targets = [lang for lang in self.lang_configs if lang != 'JA']
        
        # We can run these in parallel for efficiency
        tasks = [self.translate_single(ja_text, lang) for lang in targets]
        translated_texts = await asyncio.gather(*tasks)
        
        for lang, text in zip(targets, translated_texts):
            results[lang] = text
            print(f"[{lang}] {text}")
            
        return results

async def main():
    # Verify GOOGLE_API_KEY
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in environment variables or .env file.")
        return

    pipeline = TranslationPipeline()
    
    # Test cases
    test_sentences = [
        # "ランドが定員オーバーのため、獲得FISHが減ります。",
        # "フィッシングを開始します。",
        # "新しいZONEを追加してください。",
        "マイドライブに Angland Backup/DO_NOT_DELETE_wallet_recovery_{0}を作成しました。\nこのフォルダーとファイルはウォレットの復元時に必要となるため、変更や削除、リネーム、移動したりしないようお願いします。"
    ]
    
    for sentence in test_sentences:
        await pipeline.translate_all(sentence)

if __name__ == "__main__":
    asyncio.run(main())
