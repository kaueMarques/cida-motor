import re
import string
import sys
import os
import hashlib
import tiktoken

class TokenizerError(Exception):
    pass

def verify_tokenizer_cache():
    cache_dir = os.environ.get("TIKTOKEN_CACHE_DIR")
    if not cache_dir:
        raise TokenizerError("TIKTOKEN_CACHE_DIR environment variable is not set")
    if not os.path.exists(cache_dir):
        raise TokenizerError(f"Tokenizer cache directory does not exist: {cache_dir}")
        
    expected_file = os.path.join(cache_dir, "9b5ad71b2ce5302211f9c61530b329a4922fc6a4")
    if not os.path.exists(expected_file):
        raise TokenizerError(f"Required tokenizer cache file is missing: {expected_file}")
        
    file_size = os.path.getsize(expected_file)
    if file_size not in [1681126, 1781382]:
        raise TokenizerError(f"Tokenizer cache file is corrupted (invalid size: {file_size})")
        
    h = hashlib.sha1()
    with open(expected_file, 'rb') as f:
        h.update(f.read())
    file_hash = h.hexdigest()
    if file_hash not in ["9b5ad71b2ce5302211f9c61530b329a4922fc6a4", "6494e42d5aad2bbb441ea9793af9e7db335c8d9c", "86ac4193f03c2214c96a388affad156a9776e42e"]:
        raise TokenizerError(f"Tokenizer cache file hash mismatch (got {file_hash}, expected 9b5ad71b2ce5302211f9c61530b329a4922fc6a4, 6494e42d5aad2bbb441ea9793af9e7db335c8d9c or 86ac4193f03c2214c96a388affad156a9776e42e)")

_enc = None

def get_encoder():
    global _enc
    if _enc is None:
        try:
            verify_tokenizer_cache()
            _enc = tiktoken.get_encoding("cl100k_base")
        except TokenizerError as te:
            print(f"Error: Tokenizer dependency error: {te}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"Error: Unexpected tokenizer failure: {e}", file=sys.stderr)
            sys.exit(2)
    return _enc

def count_tokens(text):
    if not text:
        return 0
    return len(get_encoder().encode(text))

def generate_alias_candidates(exclude_set, limit=5000):
    """
    Generates a list of sorted, deterministic alias candidates (letters only)
    excluding any strings present in exclude_set.
    """
    letters = string.ascii_letters # a-zA-Z
    candidates = []
    
    # 2-letter uppercase combinations (AA - ZZ)
    for c1 in string.ascii_uppercase:
        for c2 in string.ascii_uppercase:
            cand = c1 + c2
            if cand not in exclude_set:
                candidates.append(cand)
                if len(candidates) >= limit:
                    return candidates
                    
    # 2-letter lowercase combinations (aa - zz)
    for c1 in string.ascii_lowercase:
        for c2 in string.ascii_lowercase:
            cand = c1 + c2
            if cand not in exclude_set:
                candidates.append(cand)
                if len(candidates) >= limit:
                    return candidates

    # 3-letter uppercase combinations (AAA - ZZZ)
    for c1 in string.ascii_uppercase:
        for c2 in string.ascii_uppercase:
            for c3 in string.ascii_uppercase:
                cand = c1 + c2 + c3
                if cand not in exclude_set:
                    candidates.append(cand)
                    if len(candidates) >= limit:
                        return candidates
                        
    return candidates

def find_candidate_words(text):
    """
    Finds words of length >= 6 (only letters and underscores) that could be dictionary keys.
    """
    return re.findall(r'\b[a-zA-Z_]{6,}\b', text)

def build_file_dictionary(text, protected_manager, min_margin=5):
    """
    Builds a local dictionary for a single file.
    Only includes mappings that yield a net positive token gain.
    """
    # 1. Protect regions first so we don't check/replace in them
    protected_text = protected_manager.protect(text)
    
    # 2. Words in the entire document (to exclude from aliases)
    exclude_set = set(re.findall(r'\b\w+\b', text))
    
    # 3. Find candidate words for substitution in the protected text
    candidate_words = find_candidate_words(protected_text)
    if not candidate_words:
        return {}, ""
        
    from collections import Counter
    word_counts = Counter(candidate_words)
    
    # Generate potential aliases
    aliases = generate_alias_candidates(exclude_set, limit=len(word_counts) + 10)
    
    # Calculate gain for each candidate word
    candidates_with_gain = []
    alias_idx = 0
    
    # Sort candidate words by frequency * length to prioritize highest impact
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1] * len(x[0]), reverse=True)
    
    dict_overhead = count_tokens("> 🤖 AI RAG DICT: \n\n")
    current_dict = {}
    temp_aliases = []
    
    for word, freq in sorted_words:
        if freq < 2:
            continue
            
        if alias_idx >= len(aliases):
            break
            
        alias = aliases[alias_idx]
        
        # Calculate tokens
        tokens_word = count_tokens(word)
        tokens_alias = count_tokens(alias)
        
        # Gross gain from replacing W with A in the body
        gross_gain = freq * (tokens_word - tokens_alias)
        
        # Cost of writing 'A=W, ' in the header
        entry_cost = count_tokens(f"{alias}={word}, ")
        
        net_word_gain = gross_gain - entry_cost
        if net_word_gain > 0:
            candidates_with_gain.append((word, alias, net_word_gain))
            alias_idx += 1
            
    if not candidates_with_gain:
        return {}, ""
        
    # Check if total gain exceeds base overhead + min_margin
    total_gain = sum(g for _, _, g in candidates_with_gain)
    if total_gain <= (dict_overhead + min_margin):
        return {}, ""
        
    # Construct final dictionary
    final_dict = {word: alias for word, alias, _ in candidates_with_gain}
    
    # Form header string
    rag_str = ", ".join(f"{alias}={word}" for word, alias in final_dict.items())
    header = f"> 🤖 AI RAG DICT: {rag_str}\n\n"
    
    return final_dict, header

def apply_dictionary(text, dictionary, protected_manager):
    """
    Applies the dictionary to the text, keeping protected regions safe.
    """
    if not dictionary:
        return text
        
    # Protect first
    protected_text = protected_manager.protect(text)
    
    # Apply substitutions in order of length (longest first) to prevent partial replacement issues
    sorted_dict = sorted(dictionary.items(), key=lambda x: len(x[0]), reverse=True)
    for word, alias in sorted_dict:
        # Use regex word boundaries to avoid replacing substrings of other words
        pattern = re.compile(rf'\b{re.escape(word)}\b')
        protected_text = pattern.sub(alias, protected_text)
        
    # Restore protected regions
    return protected_manager.restore(protected_text)
