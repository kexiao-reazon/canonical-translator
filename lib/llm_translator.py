from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

class LangChainLLMTranslator:
    def __init__(self, model="gemini-2.5-flash"):
        # Google API Key should be in .env as GOOGLE_API_KEY
        self.llm = ChatGoogleGenerativeAI(model=model, temperature=0)
        self.output_parser = StrOutputParser()

    def _build_prompt(self, src_text, dest_lang, glossary_info, examples_info):
        system_template = (
            "You are a language localization expert in the gaming field. "
            "Your task is to translate Japanese text into natural {dest_lang}.\n\n"
            "CRITICAL RULES:\n"
            "1. The source text contains placeholders like ⟦TERM_IDX⟧. DO NOT translate or modify these placeholders. Keep them exactly as they are in the translated output.\n"
            "2. Use the provided Terminology Mapping Reference to understand the meaning of each placeholder. This should inform the context and tone of your translation.\n"
            "3. Use the Relevant Previous Translation Examples to ensure the style and tone match the existing game content.\n"
            "4. Ensure the final sentence is grammatically correct and fluent in {dest_lang}, while strictly preserving the placeholder positions.\n"
            "5. Output ONLY the translated text.\n\n"
            "{glossary_info}\n\n"
            "{examples_info}"
        )

        user_template = "Translate this Japanese text: {src_text}"
        
        return ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("user", user_template)
        ])

    async def translate(self, text, dest_lang, glossary_info, examples_info):
        prompt = self._build_prompt(text, dest_lang, glossary_info, examples_info)
        chain = prompt | self.llm | self.output_parser
        
        try:
            result = await chain.ainvoke({
                "dest_lang": dest_lang,
                "glossary_info": glossary_info,
                "examples_info": examples_info,
                "src_text": text
            })
            return result.strip()
        except Exception as e:
            print(f"Error during LLM translation: {e}")
            return f"[ERROR TRANSLATING: {text}]"
