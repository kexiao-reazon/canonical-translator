import pandas as pd
import re

class TerminologyManager:
    def __init__(self, csv_path, lang_configs):
        self.csv_path = csv_path
        self.lang_configs = lang_configs
        # Map of ja_term -> {lang_code: translated_term}
        self.glossary = self._load_glossary()
        # Sort terms by length descending to match longest terms first
        self.sorted_terms = sorted(self.glossary.keys(), key=len, reverse=True)

    def _load_glossary(self):
        df = pd.read_csv(self.csv_path)
        glossary = {}
        
        # Ensure we have the JA term column
        ja_col = self.lang_configs['JA']['terminology_col_name']
        
        # Filter for 'keep' == 'Y'
        valid_df = df[df['keep'] == 'Y'].dropna(subset=[ja_col])
        
        for _, row in valid_df.iterrows():
            ja_term = str(row[ja_col]).strip()
            mappings = {}
            for lang_code, config in self.lang_configs.items():
                if lang_code == 'JA':
                    continue
                
                term_col = config['terminology_col_name']
                # Get the translated term if it exists in the CSV
                val = row.get(term_col)
                if pd.notna(val):
                    mappings[lang_code] = str(val).strip()
                else:
                    # Fallback for Traditional Chinese if only Simplified is available
                    if lang_code == 'TC' and pd.notna(row.get('cn_term')):
                        mappings[lang_code] = str(row.get('cn_term')).strip()
                    else:
                        mappings[lang_code] = None
            
            glossary[ja_term] = mappings
            
        return glossary

    def apply_placeholders(self, text, target_lang_code):
        """
        Replaces JA terms with placeholders. 
        Stores the specific target language translation in the map.
        """
        placeholder_map = {}
        processed_text = text
        
        for idx, ja_term in enumerate(self.sorted_terms):
            if ja_term in processed_text:
                placeholder = f"⟦TERM_{idx}⟧"
                processed_text = processed_text.replace(ja_term, placeholder)
                
                target_term = self.glossary[ja_term].get(target_lang_code)
                
                placeholder_map[placeholder] = {
                    "ja": ja_term,
                    "target": target_term,
                    "target_lang": target_lang_code
                }
        
        return processed_text, placeholder_map

    def restore_placeholders(self, translated_text, placeholder_map):
        result = translated_text
        for placeholder, mapping in placeholder_map.items():
            # If we have a canonical translation, use it. 
            # Otherwise, the LLM should have translated it (if it followed instructions).
            if mapping['target']:
                result = result.replace(placeholder, mapping['target'])
        return result

    def get_glossary_for_prompt(self, placeholder_map):
        """Returns a string representation of the used terms for the LLM prompt."""
        if not placeholder_map:
            return "No specific terminology mappings for this sentence."
        
        lines = ["Terminology Mapping Reference:"]
        for ph, data in placeholder_map.items():
            target_val = data['target'] if data['target'] else "[LLM to provide context-appropriate translation]"
            lines.append(f"- {ph}: '{data['ja']}' -> '{target_val}'")
        return "\n".join(lines)
