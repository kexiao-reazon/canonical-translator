import os
import glob
import pandas as pd
from difflib import SequenceMatcher

class LegacyRetriever:
    def __init__(self, legacy_dir, lang_configs):
        self.legacy_dir = legacy_dir
        self.lang_configs = lang_configs
        self.ja_col = lang_configs['JA']['source_col_name']
        # We'll store a list of all raw sentences for each target language
        self.corpora = self._load_corpora()

    def _load_corpora(self):
        corpora = {}
        pattern = os.path.join(self.legacy_dir, "MessageData*.csv")
        files = glob.glob(pattern)
        
        # Initialize lists for each target language
        for lang_code in self.lang_configs:
            if lang_code != 'JA':
                corpora[lang_code] = []

        for f in files:
            try:
                df = pd.read_csv(f)
                if self.ja_col in df.columns:
                    for lang_code, config in self.lang_configs.items():
                        if lang_code == 'JA':
                            continue
                        
                        target_col = config['source_col_name']
                        if target_col in df.columns:
                            valid_rows = df[[self.ja_col, target_col]].dropna()
                            for _, row in valid_rows.iterrows():
                                corpora[lang_code].append({
                                    "ja": str(row[self.ja_col]).strip(),
                                    "target": str(row[target_col]).strip()
                                })
            except Exception as e:
                print(f"Warning: Could not load {f}: {e}")
        
        # Deduplicate
        for lang_code in corpora:
            df_temp = pd.DataFrame(corpora[lang_code]).drop_duplicates()
            corpora[lang_code] = df_temp.to_dict('records')
            
        return corpora

    def _calculate_similarity(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def retrieve(self, ja_text, target_lang_code, top_k=3):
        """Retrieves top_k most similar (ja, target) pairs for a specific language."""
        corpus = self.corpora.get(target_lang_code, [])
        if not corpus:
            return []

        scored_corpus = []
        for entry in corpus:
            score = self._calculate_similarity(ja_text, entry['ja'])
            scored_corpus.append((score, entry))

        scored_corpus.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_corpus[:top_k]]

    def format_examples_for_prompt(self, examples, target_fullname):
        if not examples:
            return f"No previous translation examples found for {target_fullname} style reference."
        
        lines = [f"Relevant Previous Translation Examples for {target_fullname} Style Reference:"]
        for i, ex in enumerate(examples):
            lines.append(f"Example {i+1}:")
            lines.append(f"  Source (Japanese): {ex['ja']}")
            lines.append(f"  Target ({target_fullname}): {ex['target']}")
        return "\n".join(lines)
