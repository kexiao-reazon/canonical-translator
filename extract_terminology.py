import os
import glob
import pandas as pd
from collections import Counter, defaultdict
from sudachipy import dictionary

# ----------------------------
# Configuration
# ----------------------------
INPUT_PATTERN = "legacy_mapping/MessageData*.csv"
OUTPUT_CSV = "data/terminology_candidates.csv"
MIN_LENGTH = 2        # ignore 1-char noise
EXCLUDE_WORDS = {"こと", "もの", "場合"}  # common junk nouns
JA_COLUME_NAME = "Japanese(ja)"
EN_COLUME_NAME = "English (United States)(en-US)"
CN_COLUME_NAME = "Chinese (Simplified)(zh-CN)"


class Terminology():

  def __init__(self):
    self._tokenizer = dictionary.Dictionary().create()
    self._term_min_len = 1
    self._term_exclude_list = []


  def _filter_phrase(self, p):
    if len(p) >= MIN_LENGTH and p not in EXCLUDE_WORDS:
      return True


  # ----------------------------
  # Helper: extract noun phrases from a list of 
  # ----------------------------
  def extract_noun_phrases(self, text):
    tokens = self._tokenizer.tokenize(text)
    phrases = []
    buffer = []
  
    # Loop each tokens and get the nouns
    # Greedy get longest nouns whenever possible: ex. 取引履歴 rather than 取引
    for t in tokens:
      pos = t.part_of_speech()[0]
      surface = t.surface()
  
      if pos == "名詞":
        buffer.append(surface)
      else:
        if buffer:
          phrase = "".join(buffer)
          if self._filter_phrase(phrase):
            phrases.append(phrase)
          buffer = []
  
    if buffer and self._filter_phrase("".join(buffer)):
      phrases.append("".join(buffer))
  
    return phrases


  def find_translation_variants(self, term, df, target_col="zh_text"):
    variants = Counter()

    for _, row in df.iterrows():
        if term in row[JA_COLUME_NAME] and isinstance(row[target_col], str):
            variants[row[target_col]] += 1

    return variants

  
  def format_variants(self, variants_counter):
    return ";\n".join(
        f"{text}({count})"
        for text, count in variants_counter.most_common()
    )


def main():
  # ----------------------------
  # Initialize tokenizer
  # ----------------------------
  terminology = Terminology()
  terminology._term_min_len = MIN_LENGTH
  terminology._term_exclude_list = EXCLUDE_WORDS
  
  # ----------------------------
  # Main logic: Extract terminology
  # ----------------------------
  term_freq_counter = Counter()
  en_term_variant_map = defaultdict(Counter)
  cn_term_variant_map = defaultdict(Counter)

  path = os.getcwd()
  input_files = glob.glob(os.path.join(path, INPUT_PATTERN))
  for f in input_files:
    print(f"Processing file {f}")
    df = pd.read_csv(f)
  
    term_set = set()
    for text in df[JA_COLUME_NAME].dropna():
      phrases = terminology.extract_noun_phrases(text)
      for p in phrases:
        term_set.add(p)
        term_freq_counter[p] += 1
  
  
        # process English match
        variants_counter_en = terminology.find_translation_variants(p, df, target_col=EN_COLUME_NAME)
        en_term_variant_map[p] += variants_counter_en

        # process Chinese(Simplified) match
        variants_counter_cn = terminology.find_translation_variants(p, df, target_col=CN_COLUME_NAME)
        cn_term_variant_map[p] += variants_counter_cn

    # # ----------------------------
    # # Output ranked candidates
    # # ----------------------------
    # result = pd.DataFrame(counter.most_common(), columns=["ja_term", "frequency"])
    # result.to_csv(OUTPUT_CSV, index=False)
    #  
    # print(f"Extracted {len(result)} terminology candidates")

    # ----------------------------
    # Check logic: Verify terminology
    # ----------------------------

  all_terminology_rows = []
  for term, freq in term_freq_counter.most_common():

    # format variant
    en_variant = en_term_variant_map[term].most_common(3);
    en_variant_str = '\n'.join(e for e, _ in en_variant)

    cn_variant = cn_term_variant_map[term].most_common(3);
    cn_variant_str = '\n'.join(e for e, _ in cn_variant)

    all_terminology_rows.append({
      "keep?": "",
      "ja_term": term,
      "frequentcy": freq,
      "en_term": "",
      "en_variants": en_variant_str,
      "cn_term": "",
      "cn_variants": cn_variant_str,
    })

  # ----------------------------
  # Output Result
  # ----------------------------
  result = pd.DataFrame(all_terminology_rows)
  result.to_csv(OUTPUT_CSV, index=False)

  print(f"Processing Completed with {len(result)} rows")

if __name__ == '__main__':
  main()
    
