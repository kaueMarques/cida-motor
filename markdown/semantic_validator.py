import re
from markdown.block_parser import parse_markdown

def parse_yaml_frontmatter(content):
    """
    Parses a YAML frontmatter string line-by-line.
    """
    data = {}
    lines = content.strip().splitlines()
    start = 1 if lines and lines[0].strip() == '---' else 0
    end = len(lines) - 1 if lines and lines[-1].strip() == '---' else len(lines)
    
    for i in range(start, end):
        line = lines[i]
        if not line.strip() or line.strip().startswith('#'):
            continue
        parts = line.split(':', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            val = parts[1].strip()
            # Remove enclosing quotes if any
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            data[key] = val
    return data

def extract_inline_elements(text):
    """
    Extracts inline code blocks, links, placeholders, and XML/HTML tags.
    """
    inline_codes = re.findall(r'`([^`\n]+)`', text)
    links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', text)
    placeholders = re.findall(r'(\{\{[\w.-]+\}\}|\{[\w.-]+\}|\$\{[\w_]+\})', text)
    tags = re.findall(r'(<[^>]+>)', text)
    return {
        "inline_codes": inline_codes,
        "links": links,
        "placeholders": placeholders,
        "tags": tags,
    }

def validate_semantics(original_text, minified_text, dictionary=None):
    """
    Validates that the minified Markdown is semantically equivalent to the original.
    Dereferences dictionary aliases and compares headers, code blocks, lists, links,
    and frontmatter properties.
    """
    # Strip non-operational comments from both original and minified text
    # so that their removal does not trigger tag count mismatches.
    def clean_comments(t):
        comments = re.findall(r'<!--(.*?)-->', t, flags=re.DOTALL)
        res = t
        for c in comments:
            if any(w in c for w in ["stepsCompleted", "workflowType", "inputDocuments", "nextStepFile", "outputFile"]):
                continue
            res = res.replace(f"<!--{c}-->", "")
        return res

    original_text = clean_comments(original_text)
    minified_text = clean_comments(minified_text)

    decompiled_text = minified_text
    
    # 1. Parse dictionary from header if present
    extracted_dict = {}
    header_match = re.match(r'^>\s*🤖\s*AI RAG DICT:\s*(.*?)\n\n', minified_text, flags=re.DOTALL)
    if header_match:
        dict_content = header_match.group(1)
        minified_body = minified_text[header_match.end():]
        decompiled_text = minified_body
        for item in dict_content.split(','):
            parts = item.strip().split('=')
            if len(parts) == 2:
                # Key in header is alias, value is original word
                extracted_dict[parts[1].strip()] = parts[0].strip()
    else:
        minified_body = minified_text

    # Merge with provided dictionary if any
    active_dict = {}
    if dictionary:
        active_dict.update(dictionary)
    # Header format is alias=original_word (e.g. AA=someWord), so key is original_word, value is alias
    active_dict.update(extracted_dict)

    # Decompile (dereference aliases back to original words)
    if active_dict:
        # Sort by length of original word to replace longest first
        sorted_dict = sorted(active_dict.items(), key=lambda x: len(x[0]), reverse=True)
        for original_word, alias in sorted_dict:
            pattern = re.compile(rf'\b{re.escape(alias)}\b')
            decompiled_text = pattern.sub(original_word, decompiled_text)

    # 2. Parse original and decompiled into blocks
    orig_blocks = parse_markdown(original_text)
    decomp_blocks = parse_markdown(decompiled_text)

    # 3. Compare Headers
    orig_headers = [b.content.strip() for b in orig_blocks if b.type == "header"]
    decomp_headers = [b.content.strip() for b in decomp_blocks if b.type == "header"]
    if len(orig_headers) != len(decomp_headers):
        return False, f"Header count mismatch: original {len(orig_headers)} vs minified {len(decomp_headers)}"
    for i, (oh, dh) in enumerate(zip(orig_headers, decomp_headers)):
        oh_norm = re.sub(r'\s+', ' ', oh)
        dh_norm = re.sub(r'\s+', ' ', dh)
        if oh_norm != dh_norm:
            return False, f"Header content mismatch at index {i}: '{oh_norm}' vs '{dh_norm}'"

    # 4. Compare Fenced Code Blocks
    orig_code = [(b.metadata.get("lang"), b.content.strip()) for b in orig_blocks if b.type == "code_block"]
    decomp_code = [(b.metadata.get("lang"), b.content.strip()) for b in decomp_blocks if b.type == "code_block"]
    if len(orig_code) != len(decomp_code):
        return False, f"Code block count mismatch: original {len(orig_code)} vs minified {len(decomp_code)}"
    for i, (oc, dc) in enumerate(zip(orig_code, decomp_code)):
        if oc[0] != dc[0]:
            return False, f"Code block language mismatch at index {i}: '{oc[0]}' vs '{dc[0]}'"
        oc_content = re.sub(r'\s+', ' ', oc[1])
        dc_content = re.sub(r'\s+', ' ', dc[1])
        if oc_content != dc_content:
            return False, f"Code block content mismatch at index {i}"

    # 5. Compare List items
    orig_lists = [b.content.strip() for b in orig_blocks if b.type == "list"]
    decomp_lists = [b.content.strip() for b in decomp_blocks if b.type == "list"]
    orig_list_items = []
    for l in orig_lists:
        orig_list_items.extend([line.strip() for line in l.splitlines() if line.strip()])
    decomp_list_items = []
    for l in decomp_lists:
        decomp_list_items.extend([line.strip() for line in l.splitlines() if line.strip()])

    if len(orig_list_items) != len(decomp_list_items):
        return False, f"List items count mismatch: original {len(orig_list_items)} vs minified {len(decomp_list_items)}"

    # 6. Compare Inline Elements (inline code, links, placeholders, tags)
    orig_inline = extract_inline_elements(original_text)
    decomp_inline = extract_inline_elements(decompiled_text)

    for key in ["inline_codes", "links", "placeholders", "tags"]:
        orig_items = orig_inline[key]
        decomp_items = decomp_inline[key]
        if len(orig_items) != len(decomp_items):
            return False, f"Inline element '{key}' count mismatch: original {len(orig_items)} vs minified {len(decomp_items)}"
        for i, (oi, di) in enumerate(zip(orig_items, decomp_items)):
            if oi != di:
                return False, f"Inline element '{key}' mismatch at index {i}: '{oi}' vs '{di}'"

    # 7. Compare Frontmatter
    orig_fm_blocks = [b.content for b in orig_blocks if b.type == "frontmatter"]
    decomp_fm_blocks = [b.content for b in decomp_blocks if b.type == "frontmatter"]
    
    if len(orig_fm_blocks) != len(decomp_fm_blocks):
        return False, f"Frontmatter block count mismatch: original {len(orig_fm_blocks)} vs minified {len(decomp_fm_blocks)}"
        
    if orig_fm_blocks:
        orig_fm = parse_yaml_frontmatter(orig_fm_blocks[0])
        decomp_fm = parse_yaml_frontmatter(decomp_fm_blocks[0])
        
        if set(orig_fm.keys()) != set(decomp_fm.keys()):
            return False, f"Frontmatter keys mismatch: original {orig_fm.keys()} vs minified {decomp_fm.keys()}"
            
        for k, v in orig_fm.items():
            if v != decomp_fm[k]:
                return False, f"Frontmatter value mismatch for key '{k}': '{v}' vs '{decomp_fm[k]}'"

    return True, "Success"
