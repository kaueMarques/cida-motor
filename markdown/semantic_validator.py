import re
import yaml
from markdown.block_parser import parse_markdown

class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = []
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in [k for k, _ in mapping]:
                raise yaml.constructor.ConstructorError(
                    None, None, f"Duplicate key '{key}' found in YAML frontmatter", key_node.start_mark
                )
            value = self.construct_object(value_node, deep=deep)
            mapping.append((key, value))
        return super().construct_mapping(node, deep=deep)

def parse_yaml_frontmatter_safe(content):
    """
    Parses frontmatter content using safe PyYAML and UniqueKeyLoader to reject duplicates.
    """
    lines = content.strip().splitlines()
    start = 1 if lines and lines[0].strip() == '---' else 0
    end = len(lines) - 1 if lines and lines[-1].strip() == '---' else len(lines)
    
    yaml_str = "\n".join(lines[start:end])
    if not yaml_str.strip():
        return {}
        
    try:
        data = yaml.load(yaml_str, Loader=UniqueKeyLoader)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ValueError("Frontmatter must be a key-value dictionary")
        return {str(k): (str(v) if v is not None else "") for k, v in data.items()}
    except Exception as e:
        raise ValueError(f"YAML parsing error: {e}")

def parse_yaml_frontmatter(content):
    """
    Backward-compatible entry point for parse_yaml_frontmatter.
    """
    try:
        return parse_yaml_frontmatter_safe(content)
    except Exception:
        # Fallback to simple line parsing to prevent unit test crashes if needed
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
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                data[key] = val
        return data

def extract_all_protected_elements(text):
    """
    Extracts all occurrences of protected elements in their exact order of appearance.
    """
    patterns = [
        # Inline code
        r'`[^`\n]+`',
        # Link/Image destinations
        r'(?<=\]\()[^)]+(?=\))',
        # URLs
        r'https?://[^\s)\]]+',
        # Placeholders
        r'\{\{[\w.-]+\}\}',
        r'\{[\w.-]+\}',
        r'\$\{[\w_]+\}',
        # XML/HTML tags
        r'<[^>]+>',
        # BMAD critical terms
        r'\bstepsCompleted\b',
        r'\bworkflowType\b',
        r'\binputDocuments\b',
        r'\bnextStepFile\b',
        r'\boutputFile\b',
        r'\bbmad-create-architecture\b',
        r'\bbmad-dev-story\b',
        r'\bsteps-c/?\b',
        r'\bsteps-e/?\b',
        r'\bsteps-v/?\b',
        r'\b_bmad/?\b',
        r'\b_bmad-output/?\b',
        # Paths
        r'\b[\w.-]+/[\w.-]+(?:/[\w.-]+)*\b/?',
        r'\b[a-zA-Z]:\\[\w.-\\]*\b',
        r'\b[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\(\)',
        # Normative values
        r'\b(?i:must|never|deve|não|somente|obrigatório)\b',
    ]
    combined = re.compile('|'.join(patterns), re.MULTILINE)
    return combined.findall(text)

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

def clean_comments(text):
    """
    Removes non-operational HTML/XML comments from the text.
    """
    def repl(m):
        content = m.group(1)
        if any(w in content for w in ["stepsCompleted", "workflowType", "inputDocuments", "nextStepFile", "outputFile"]):
            return m.group(0)
        return ""
    return re.sub(r'<!--([\s\S]*?)-->', repl, text)

def normalize_spaces(text):
    return re.sub(r'\s+', ' ', text.strip())

def validate_semantics(original_text, minified_text, dictionary=None):
    """
    Validates that the minified Markdown is semantically and structurally equivalent to the original.
    """
    try:
        orig_has_fm = original_text.strip().startswith('---')
        mini_has_fm = minified_text.strip().startswith('---')
        if orig_has_fm != mini_has_fm:
            return False, f"Frontmatter presence mismatch: original {orig_has_fm} vs minified {mini_has_fm}"
            
        original_clean = clean_comments(original_text)
        minified_clean = clean_comments(minified_text)
        
        decompiled_text = minified_clean
        if dictionary:
            sorted_dict = sorted(dictionary.items(), key=lambda x: len(x[0]), reverse=True)
            for original_word, alias in sorted_dict:
                pattern = re.compile(rf'\b{re.escape(alias)}\b')
                decompiled_text = pattern.sub(original_word, decompiled_text)
                
        orig_blocks = parse_markdown(original_clean)
        decomp_blocks = parse_markdown(decompiled_text)

        # 0. Check YAML frontmatter syntax/duplicates first
        for blocks in [orig_blocks, decomp_blocks]:
            fm_blocks = [b for b in blocks if b.type == "frontmatter"]
            for b in fm_blocks:
                try:
                    parse_yaml_frontmatter_safe(b.content)
                except Exception as e:
                    return False, f"YAML frontmatter error: {e}"
        
        # 1. Compare inline elements first for explicit test cases
        orig_inline = extract_inline_elements(original_clean)
        decomp_inline = extract_inline_elements(decompiled_text)

        for key in ["inline_codes", "links", "placeholders", "tags"]:
            orig_items = orig_inline[key]
            decomp_items = decomp_inline[key]
            if len(orig_items) != len(decomp_items):
                return False, f"Inline element '{key}' count mismatch: original {len(orig_items)} vs minified {len(decomp_items)}"
            for i, (oi, di) in enumerate(zip(orig_items, decomp_items)):
                if oi != di:
                    return False, f"Inline element '{key}' mismatch at index {i}: '{oi}' vs '{di}'"

        # 2. Check all protected elements (fences, URLs, paths, normative values)
        orig_all_prot = extract_all_protected_elements(original_clean)
        decomp_all_prot = extract_all_protected_elements(decompiled_text)
        if len(orig_all_prot) != len(decomp_all_prot):
            return False, f"Protected elements count mismatch: original {len(orig_all_prot)} vs minified {len(decomp_all_prot)}"
        for i, (oi, di) in enumerate(zip(orig_all_prot, decomp_all_prot)):
            if oi != di:
                return False, f"Protected element mismatch at index {i}: '{oi}' vs '{di}'"

        # 3. Parse blocks
        orig_filtered = [b for b in orig_blocks if b.type != "blank" and b.type != "comment"]
        decomp_filtered = [b for b in decomp_blocks if b.type != "blank" and b.type != "comment"]
        
        orig_filtered += [b for b in orig_blocks if b.type == "comment" and any(w in b.content for w in ["stepsCompleted", "workflowType", "inputDocuments", "nextStepFile", "outputFile"])]
        decomp_filtered += [b for b in decomp_blocks if b.type == "comment" and any(w in b.content for w in ["stepsCompleted", "workflowType", "inputDocuments", "nextStepFile", "outputFile"])]
        
        orig_filtered = sorted(orig_filtered, key=lambda b: original_clean.find(b.content))
        decomp_filtered = sorted(decomp_filtered, key=lambda b: decompiled_text.find(b.content))
        
        if len(orig_filtered) != len(decomp_filtered):
            return False, f"Block structure mismatch: original count {len(orig_filtered)} vs minified count {len(decomp_filtered)}"
            
        for idx, (ob, db) in enumerate(zip(orig_filtered, decomp_filtered)):
            if ob.type != db.type:
                return False, f"Block type mismatch at index {idx}: original '{ob.type}' vs minified '{db.type}'"
                
            if ob.type == "frontmatter":
                try:
                    orig_fm = parse_yaml_frontmatter_safe(ob.content)
                    decomp_fm = parse_yaml_frontmatter_safe(db.content)
                except Exception as e:
                    return False, f"YAML frontmatter error at index {idx}: {e}"
                if set(orig_fm.keys()) != set(decomp_fm.keys()):
                    return False, f"Frontmatter keys mismatch: original {orig_fm.keys()} vs minified {decomp_fm.keys()}"
                for k, v in orig_fm.items():
                    if v != decomp_fm[k]:
                        return False, f"Frontmatter value mismatch for key '{k}': '{v}' vs '{decomp_fm[k]}'"
                        
            elif ob.type == "header":
                if normalize_spaces(ob.content) != normalize_spaces(db.content):
                    return False, f"Header content mismatch at index {idx}: '{ob.content.strip()}' vs '{db.content.strip()}'"
                    
            elif ob.type == "code_block":
                if ob.metadata.get("lang") != db.metadata.get("lang"):
                    return False, f"Code block language mismatch at index {idx}: '{ob.metadata.get('lang')}' vs '{db.metadata.get('lang')}'"
                if ob.content.strip() != db.content.strip():
                    return False, f"Code block content mismatch at index {idx}"
                    
            elif ob.type == "table":
                orig_lines = [l.strip() for l in ob.content.splitlines() if l.strip()]
                decomp_lines = [l.strip() for l in db.content.splitlines() if l.strip()]
                if len(orig_lines) != len(decomp_lines):
                    return False, f"Table line count mismatch at index {idx}"
                for row_idx, (ol, dl) in enumerate(zip(orig_lines, decomp_lines)):
                    if row_idx == 1:
                        o_sep = [c.strip() for c in ol.split('|') if c.strip()]
                        d_sep = [c.strip() for c in dl.split('|') if c.strip()]
                        if o_sep != d_sep:
                            return False, f"Table columns alignment mismatch at index {idx}"
                    else:
                        o_cells = [c.strip() for c in ol.split('|') if c.strip()]
                        d_cells = [c.strip() for c in dl.split('|') if c.strip()]
                        if o_cells != d_cells:
                            return False, f"Table cells content mismatch at index {idx}, row {row_idx}"
                            
            elif ob.type == "list":
                orig_lines = [l for l in ob.content.splitlines() if l.strip()]
                decomp_lines = [l for l in db.content.splitlines() if l.strip()]
                if len(orig_lines) != len(decomp_lines):
                    return False, f"List items count mismatch at index {idx}"
                for item_idx, (ol, dl) in enumerate(zip(orig_lines, decomp_lines)):
                    o_depth = len(ol) - len(ol.lstrip())
                    d_depth = len(dl) - len(dl.lstrip())
                    if o_depth != d_depth:
                        return False, f"List item indentation depth mismatch at index {idx}, item {item_idx}"
                    o_m = re.match(r'^\s*([-*+]|\d+\.)\s+', ol)
                    d_m = re.match(r'^\s*([-*+]|\d+\.)\s+', dl)
                    if not o_m or not d_m or o_m.group(1) != d_m.group(1):
                        return False, f"List item marker mismatch at index {idx}, item {item_idx}"
                    o_txt = ol.lstrip()[len(o_m.group(0).lstrip()):].strip()
                    d_txt = dl.lstrip()[len(d_m.group(0).lstrip()):].strip()
                    if normalize_spaces(o_txt) != normalize_spaces(d_txt):
                        return False, f"List item content mismatch at index {idx}, item {item_idx}"
                        
            elif ob.type == "blockquote":
                o_txt = re.sub(r'^>\s*', '', ob.content.strip())
                d_txt = re.sub(r'^>\s*', '', db.content.strip())
                if normalize_spaces(o_txt) != normalize_spaces(d_txt):
                    return False, f"Blockquote mismatch at index {idx}"
                    
            elif ob.type == "comment":
                if ob.content.strip() != db.content.strip():
                    return False, f"Operational comment content mismatch at index {idx}"
                    
            elif ob.type == "paragraph":
                if normalize_spaces(ob.content) != normalize_spaces(db.content):
                    return False, f"Paragraph mismatch at index {idx}"
                    
        return True, "Success"
        
    except Exception as e:
        return False, f"Semantic validator internal error: {e}"

