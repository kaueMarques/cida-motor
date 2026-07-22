import os
import sys
import argparse
import time
import json
import re
import shutil
import hashlib
from markdown.protected_regions import ProtectedRegionsManager
from markdown.phrase_dictionary import (
    count_tokens, build_file_dictionary, apply_dictionary,
    generate_alias_candidates, find_candidate_words
)
from markdown.semantic_validator import validate_semantics
from markdown.report import ReportGenerator
from markdown.sidecar import write_sidecar, create_sidecar_data, validate_sidecar, reject_duplicate_keys, SidecarValidationError, validate_sidecar_schema

def optimize_markdown_dictionary_file_scope(content, transformed_text, filepath, verify_semantics):
    # Base tokens of transformed_text (without dictionary)
    base_tokens = count_tokens(transformed_text)
    best_tokens = base_tokens
    best_minified = transformed_text
    best_sidecar_data = None
    
    pm = ProtectedRegionsManager()
    protected_text = pm.protect(transformed_text)
    
    exclude_set = set(re.findall(r'\b\w+\b', transformed_text))
    candidate_words = find_candidate_words(protected_text)
    if not candidate_words:
        return transformed_text, None, 0
        
    from collections import Counter
    word_counts = Counter(candidate_words)
    
    # Sort candidate words by frequency * length to prioritize highest impact
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1] * len(x[0]), reverse=True)
    
    aliases = generate_alias_candidates(exclude_set, limit=len(word_counts) + 10)
    
    current_dict = {}
    
    alias_idx = 0
    for word, freq in sorted_words:
        if freq < 2:
            continue
        if alias_idx >= len(aliases):
            break
            
        alias = aliases[alias_idx]
        
        # Add word to current dictionary
        current_dict[word] = alias
        alias_idx += 1
        
        # Test applying current dictionary
        candidate_minified = apply_dictionary(transformed_text, current_dict, pm)
        
        # Invert dictionary for sidecar
        entries_dict = {alias: word for word, alias in current_dict.items()}
        
        try:
            sidecar_data = create_sidecar_data(filepath, content.encode('utf-8'), entries_dict)
        except Exception:
            # Revert last addition
            current_dict.pop(word)
            alias_idx -= 1
            continue
            
        if verify_semantics:
            is_valid, _ = validate_semantics(content, candidate_minified, current_dict)
            if not is_valid:
                # Revert last addition
                current_dict.pop(word)
                alias_idx -= 1
                continue
                
        # Calculate effective cost
        tokens_min = count_tokens(candidate_minified)
        tokens_sidecar = count_tokens(json.dumps(sidecar_data, ensure_ascii=False, indent=4))
        tokens_instr = count_tokens("Use the companion sidecar file to resolve aliases.")
        
        effective_tokens = tokens_min + tokens_sidecar + tokens_instr
        
        if effective_tokens < best_tokens:
            best_tokens = effective_tokens
            best_minified = candidate_minified
            best_sidecar_data = sidecar_data
        else:
            # Revert last addition
            current_dict.pop(word)
            alias_idx -= 1
            
    final_tokens_dict = count_tokens(json.dumps(best_sidecar_data, ensure_ascii=False, indent=4)) if best_sidecar_data else 0
    return best_minified, best_sidecar_data, final_tokens_dict

# Re-use Java/code minifier from motor_v2
def minificar_codigo_para_ia(codigo_fonte, dicionario=None):
    codigo = re.sub(r'/\*.*?\*/', '', codigo_fonte, flags=re.DOTALL)
    codigo = re.sub(r'//.*', '', codigo)
    codigo = re.sub(r'package\s+[\w\.]+;', '', codigo)
    codigo = re.sub(r'import\s+(?:static\s+)?[\w\.\*]+;', '', codigo)
    codigo = re.sub(r'@\w+(?:\([^)]*\))?\s*', '', codigo)
    codigo = re.sub(r'\b(System\.out\.\w+|console\.\w+|logger\.\w+|print|Log\.\w+|trace|debug|error|assert)\s*\([^)]*\);?', '', codigo)
    codigo = re.sub(r'(["\']).{15,}?\1', '""', codigo)
    codigo = re.sub(r'\b(public|private|protected|export|final|volatile|strictfp)\s+', '', codigo)
    codigo = re.sub(r'\b(this|self)\.', '', codigo)
    codigo = re.sub(r'\s+', ' ', codigo)
    codigo = re.sub(r'\s*([+\-*/%&|<>!^~?:;,{}()\[\]=]+)\s*', r'\1', codigo)
    if dicionario:
        for palavra, id_token in sorted(dicionario.items(), key=lambda x: len(x[0]), reverse=True):
            codigo = re.sub(rf'\b{re.escape(palavra)}\b', id_token, codigo)
    return codigo.strip()

# Auto-detect profile
def detect_profile(filepath, content):
    name = os.path.basename(filepath).lower()
    ext = os.path.splitext(name)[1].lower()
    
    if ext == '.java':
        return 'java'
        
    bmad_names = [
        'workflow.md', 'skill.md', 'agents.md', 'checklist.md', 
        'project-context.md', 'prd.md', 'architecture.md'
    ]
    if name in bmad_names or name.startswith('step-') or name.endswith('-template.md'):
        return 'bmad'
        
    path_parts = filepath.lower().replace('\\', '/').split('/')
    if any(p in path_parts for p in ['_bmad', '_bmad-output', 'steps-c', 'steps-e', 'steps-v']):
        return 'bmad'
        
    if ext not in ['.md', '.txt']:
        return 'code'
        
    if re.search(r'stepsCompleted|workflowType|inputDocuments|nextStepFile|outputFile', content):
        return 'bmad'
        
    if re.search(r'<[^>]+>|\{[\w.-]+\}|\$\{\w+\}', content):
        return 'bmad'
        
    return 'markdown'

# Transformations
def remove_html_comments(text):
    comments = re.findall(r'<!--(.*?)-->', text, flags=re.DOTALL)
    result = text
    for c in comments:
        if any(w in c for w in ["stepsCompleted", "workflowType", "inputDocuments", "nextStepFile", "outputFile"]):
            continue
        result = result.replace(f"<!--{c}-->", "")
    return result

def trim_trailing_whitespace(text):
    return "\n".join(line.rstrip() for line in text.splitlines())

def normalize_newlines(text):
    return re.sub(r'\n{3,}', '\n\n', text)

def table_whitespace(text):
    lines = []
    for line in text.splitlines():
        if line.strip().startswith('|') and line.strip().endswith('|'):
            parts = line.split('|')
            new_parts = [p.strip() for p in parts]
            lines.append('|'.join(new_parts))
        else:
            lines.append(line)
    return '\n'.join(lines)

def list_compaction(text):
    from markdown.block_parser import parse_markdown
    blocks = parse_markdown(text)
    new_text = []
    for b in blocks:
        if b.type == "list":
            lines = [line for line in b.content.splitlines(keepends=True) if line.strip()]
            new_text.append("".join(lines))
        else:
            new_text.append(b.content)
    return "".join(new_text)

def build_corpus_dictionary(all_files_content, min_margin=5):
    exclude_set = set()
    for text in all_files_content:
        exclude_set.update(re.findall(r'\b\w+\b', text))
        
    from collections import Counter
    word_counts = Counter()
    for text in all_files_content:
        pm = ProtectedRegionsManager()
        protected = pm.protect(text)
        candidate_words = find_candidate_words(protected)
        word_counts.update(candidate_words)
        
    aliases = generate_alias_candidates(exclude_set, limit=len(word_counts) + 10)
    
    candidates_with_gain = []
    alias_idx = 0
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1] * len(x[0]), reverse=True)
    
    for word, freq in sorted_words:
        if freq < 3:
            continue
        if alias_idx >= len(aliases):
            break
        alias = aliases[alias_idx]
        tokens_word = count_tokens(word)
        tokens_alias = count_tokens(alias)
        gross_gain = freq * (tokens_word - tokens_alias)
        entry_cost = count_tokens(f"{alias}={word}\n")
        
        if gross_gain - entry_cost > 0:
            candidates_with_gain.append((word, alias, gross_gain - entry_cost))
            alias_idx += 1
            
    total_gain = sum(g for _, _, g in candidates_with_gain)
    if total_gain <= min_margin:
        return {}
        
    return {word: alias for word, alias, _ in candidates_with_gain}

def is_binary_file(filepath):
    # Check extension first
    ext = os.path.splitext(filepath)[1].lower()
    binary_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.zip', '.pdf', '.exe', '.dll', '.class', '.jar', '.db', '.pyc']
    if ext in binary_extensions:
        return True
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
    except:
        pass
    return False

def verify_destination_sidecars(src_abs, dst_abs):
    for root, _, files in os.walk(dst_abs):
        for f in files:
            if f.endswith(".cidatkn"):
                sidecar_path = os.path.join(root, f)
                try:
                    with open(sidecar_path, 'r', encoding='utf-8') as sf:
                        data = json.load(sf, object_pairs_hook=reject_duplicate_keys)
                    validate_sidecar_schema(data)
                    if data.get("source") != "corpus":
                        orig_file_path = os.path.join(src_abs, data["source"])
                        if os.path.exists(orig_file_path):
                            with open(orig_file_path, 'rb') as obf:
                                orig_bytes = obf.read()
                            validate_sidecar(data, data["source"], orig_bytes)
                except Exception as e:
                    print(f"Sidecar validation failed for {f}: {e}", file=sys.stderr)
                    sys.exit(5)

def main():
    parser = argparse.ArgumentParser(description="Token-oriented Markdown Minifier for BMAD")
    parser.add_argument("--src", required=True, help="Source directory or file")
    parser.add_argument("--dst", required=True, help="Destination directory")
    parser.add_argument("--profile", default="auto", choices=["auto", "code", "java", "markdown", "bmad"], help="Processing profile")
    parser.add_argument("--dictionary-scope", default="file", choices=["none", "file", "corpus"], help="Dictionary scope")
    parser.add_argument("--fail-on-inflation", action="store_true", help="Fail if any file has token count inflation")
    parser.add_argument("--report", default="both", choices=["text", "json", "both"], help="Report format")
    parser.add_argument("--report-path", default="report", help="Report output path (without extension)")
    parser.add_argument("--verify-semantics", action="store_true", default=True, help="Run semantic validations")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no files written)")
    parser.add_argument("--java-raw-json", help="Path to temporary Java raw metrics JSON")
    
    args = parser.parse_args()
    
    src_abs = os.path.abspath(args.src)
    dst_abs = os.path.abspath(args.dst)
    
    if not os.path.exists(src_abs):
        print(f"Error: Source not found: {src_abs}")
        sys.exit(1)
        
    # Collect files - ONLY collect markdown/text
    files_to_process = []
    if os.path.isfile(src_abs):
        if src_abs.endswith('.md') or src_abs.endswith('.txt'):
            files_to_process.append(src_abs)
    else:
        for root, dirs, files in os.walk(src_abs):
            if dst_abs in os.path.abspath(root):
                continue
            for f in files:
                filepath = os.path.join(root, f)
                if "tknd" in filepath or "_mimificado" in f:
                    continue
                if f.endswith('.md') or f.endswith('.txt'):
                    files_to_process.append(filepath)
                
    report_gen = ReportGenerator()
    
    # Read Java raw metrics if present
    java_raw_metrics = []
    if args.java_raw_json and os.path.exists(args.java_raw_json):
        try:
            with open(args.java_raw_json, 'r', encoding='utf-8') as jf:
                java_raw_metrics = json.load(jf, object_pairs_hook=reject_duplicate_keys)
            # Remove the temp JSON file
            os.remove(args.java_raw_json)
        except Exception as je:
            print(f"Warning: failed to read Java raw metrics JSON: {je}")

    # Process Java raw metrics into report
    for entry in java_raw_metrics:
        orig_content = entry["original_content"]
        mini_content = entry["minified_content"]
        
        orig_tokens = count_tokens(orig_content)
        final_tokens = count_tokens(mini_content)
        
        base_content = minificar_codigo_para_ia(orig_content)
        base_tokens = count_tokens(base_content)
        
        report_gen.add_entry(
            filepath=os.path.join(src_abs, entry["filepath"]),
            profile="java",
            tokens_orig=orig_tokens,
            tokens_base=base_tokens,
            tokens_new=final_tokens,
            dict_included=entry.get("dict_included", False),
            tokens_sidecar=entry.get("tokens_sidecar", 0),
            tokens_aux=entry.get("tokens_auxiliares", 0),
            accepted_transforms=["go_minification"],
            rejected_transforms=[],
            semantic_status="SUCCESS",
            execution_time=entry["elapsed_ns"] / 1e9
        )
    
    # 1. Corpus-level dictionary preparation
    corpus_dict = {}
    corpus_hash = ""
    if args.dictionary_scope == "corpus":
        all_contents = []
        for fp in files_to_process:
            if not is_binary_file(fp) and (fp.endswith('.md') or fp.endswith('.txt')):
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                        all_contents.append(f.read())
                except:
                    pass
        corpus_dict = build_corpus_dictionary(all_contents)
        
        if corpus_dict:
            # Build deterministic manifest for corpus
            manifest_files = []
            for fp in files_to_process:
                if not is_binary_file(fp) and (fp.endswith('.md') or fp.endswith('.txt')):
                    rel = os.path.relpath(fp, src_abs).replace('\\', '/')
                    try:
                        with open(fp, 'rb') as f:
                            file_bytes = f.read()
                        sha = hashlib.sha256(file_bytes).hexdigest()
                        manifest_files.append({"path": rel, "sha256": sha})
                    except:
                        pass
            # Sort files by path to ensure determinism
            manifest_files.sort(key=lambda x: x["path"])
            manifest = {"files": manifest_files}
            manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode('utf-8')
            corpus_hash = hashlib.sha256(manifest_bytes).hexdigest()
            
            # Simulate minification to check net gain
            total_orig_tokens = 0
            total_mini_tokens = 0
            for fp in files_to_process:
                if is_binary_file(fp):
                    continue
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                        c = f.read()
                except:
                    continue
                total_orig_tokens += count_tokens(c)
                
                # Apply transforms
                prof = args.profile
                if prof == "auto":
                    prof = detect_profile(fp, c)
                
                if prof in ["markdown", "bmad"]:
                    curr = c
                    curr = remove_html_comments(curr)
                    curr = trim_trailing_whitespace(curr)
                    curr = normalize_newlines(curr)
                    curr = table_whitespace(curr)
                    curr = list_compaction(curr)
                    pm = ProtectedRegionsManager()
                    cand = apply_dictionary(curr, corpus_dict, pm)
                    if args.verify_semantics:
                        is_valid, _ = validate_semantics(c, cand, corpus_dict)
                        if is_valid and count_tokens(cand) < count_tokens(curr):
                            curr = cand
                    total_mini_tokens += count_tokens(curr)
                else:
                    mini = minificar_codigo_para_ia(c, corpus_dict)
                    total_mini_tokens += count_tokens(mini)
                    
            # Calculate sidecars token cost
            items = list(corpus_dict.items())
            sidecar_tokens_total = 0
            for i in range(0, len(items), 500):
                chunk = items[i:i+500]
                entries_map = {alias: word for word, alias in chunk}
                sidecar_data = {
                    "format": "cida-token-sidecar",
                    "version": 1,
                    "source": "corpus",
                    "source_sha256": corpus_hash,
                    "entries": entries_map
                }
                sidecar_tokens_total += count_tokens(json.dumps(sidecar_data, ensure_ascii=False, indent=4))
                
            auxiliary_tokens = count_tokens("Use the companion sidecar file to resolve aliases.")
            net_savings = (total_orig_tokens - total_mini_tokens) - (sidecar_tokens_total + auxiliary_tokens)
            
            if net_savings <= 0:
                # Revert: no corpus dictionary used
                corpus_dict = {}
                corpus_hash = ""
            else:
                # Write sidecars if not dry-run
                if not args.dry_run:
                    tknd_dir = os.path.join(dst_abs, "tknd")
                    os.makedirs(tknd_dir, exist_ok=True)
                    for i in range(0, len(items), 500):
                        chunk = items[i:i+500]
                        prefixChars = "ABCDEF"
                        start_id = prefixChars[min(i // 500, len(prefixChars)-1)] + str(i % 500)
                        entries_map = {alias: word for word, alias in chunk}
                        sidecar_data = {
                            "format": "cida-token-sidecar",
                            "version": 1,
                            "source": "corpus",
                            "source_sha256": corpus_hash,
                            "entries": entries_map
                        }
                        dict_file_path = os.path.join(tknd_dir, f"{start_id}.cidatkn")
                        with open(dict_file_path, 'w', encoding='utf-8') as df:
                            json.dump(sidecar_data, df, indent=4, ensure_ascii=False)

    # 2. Process each file
    inflation_detected = False
    
    for filepath in files_to_process:
        start_time = time.time()
        
        if is_binary_file(filepath):
            if not args.dry_run:
                rel_path = os.path.relpath(filepath, src_abs) if os.path.isdir(src_abs) else os.path.basename(filepath)
                dest_path = os.path.join(dst_abs, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(filepath, dest_path)
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue
            
        profile = args.profile
        if profile == "auto":
            profile = detect_profile(filepath, content)
            
        orig_tokens = count_tokens(content)
        
        # Baseline: simulate legacy minification (simply md_minifier or motor_v2 logic)
        if profile in ["markdown", "bmad"]:
            legacy = re.sub(r'^---\s*[\r\n]+.*?[\r\n]+---\s*[\r\n]+', '', content, flags=re.DOTALL)
            legacy = re.sub(r'<!--.*?-->', '', legacy, flags=re.DOTALL)
            legacy = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[\1]', legacy)
            legacy = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', legacy)
            legacy = re.sub(r'(?<!\w)(\*\*|__|\*|_)(.*?)\1(?!\w)', r'\2', legacy)
            legacy = re.sub(r'^[-*_]{3,}\s*$', '', legacy, flags=re.MULTILINE)
            legacy = re.sub(r'\|\s+', '|', legacy)
            legacy = re.sub(r'\s+\|', '|', legacy)
            legacy = re.sub(r' {2,}', ' ', legacy)
            legacy = re.sub(r'\n{3,}', '\n\n', legacy)
            base_tokens = count_tokens(legacy.strip())
        else:
            legacy = minificar_codigo_para_ia(content)
            base_tokens = count_tokens(legacy)
            
        # Otimização
        accepted_transforms = []
        rejected_transforms = []
        
        dict_included = False
        tokens_sidecar = 0
        tokens_aux = 0
        best_sidecar_data = None
        
        if profile in ["markdown", "bmad"]:
            current_text = content
            
            candidates = [
                ("remove_html_comments", remove_html_comments),
                ("trim_trailing_whitespace", trim_trailing_whitespace),
                ("normalize_newlines", normalize_newlines),
                ("table_whitespace", table_whitespace),
                ("list_compaction", list_compaction),
            ]
            
            for name, trans_fn in candidates:
                candidate_text = trans_fn(current_text)
                
                if args.verify_semantics:
                    is_valid, _ = validate_semantics(content, candidate_text)
                    if not is_valid:
                        rejected_transforms.append(f"{name}_semantic_fail")
                        continue
                        
                cand_tokens = count_tokens(candidate_text)
                curr_tokens = count_tokens(current_text)
                
                if cand_tokens < curr_tokens:
                    current_text = candidate_text
                    accepted_transforms.append(name)
                else:
                    rejected_transforms.append(f"{name}_no_gain")
            
            # Apply Dictionary
            if args.dictionary_scope == "file":
                rel_path = os.path.relpath(filepath, src_abs) if os.path.isdir(src_abs) else os.path.basename(filepath)
                candidate_text, sidecar_data, dict_tokens = optimize_markdown_dictionary_file_scope(
                    content, current_text, rel_path, args.verify_semantics
                )
                if sidecar_data:
                    cand_tokens = count_tokens(candidate_text)
                    cand_sidecar_tokens = count_tokens(json.dumps(sidecar_data, ensure_ascii=False, indent=4))
                    cand_aux_tokens = count_tokens("Use the companion sidecar file to resolve aliases.")
                    
                    economia_bruta = orig_tokens - cand_tokens
                    overhead = cand_sidecar_tokens + cand_aux_tokens
                    if economia_bruta - overhead > 0:
                        current_text = candidate_text
                        dict_included = True
                        tokens_sidecar = cand_sidecar_tokens
                        tokens_aux = cand_aux_tokens
                        best_sidecar_data = sidecar_data
                        accepted_transforms.append("file_dictionary")
                    else:
                        rejected_transforms.append("file_dictionary_no_gain")
                else:
                    rejected_transforms.append("file_dictionary_no_gain")
                    
            elif args.dictionary_scope == "corpus" and corpus_dict:
                pm = ProtectedRegionsManager()
                candidate_text = apply_dictionary(current_text, corpus_dict, pm)
                
                if args.verify_semantics:
                    is_valid, _ = validate_semantics(content, candidate_text, corpus_dict)
                    if is_valid:
                        cand_tokens = count_tokens(candidate_text)
                        curr_tokens = count_tokens(current_text)
                        if cand_tokens < curr_tokens:
                            cand_sidecar_tokens = int(sidecar_tokens_total * orig_tokens / total_orig_tokens)
                            cand_aux_tokens = int(auxiliary_tokens * orig_tokens / total_orig_tokens)
                            
                            economia_bruta = orig_tokens - cand_tokens
                            overhead = cand_sidecar_tokens + cand_aux_tokens
                            if economia_bruta - overhead > 0:
                                current_text = candidate_text
                                dict_included = True
                                tokens_sidecar = cand_sidecar_tokens
                                tokens_aux = cand_aux_tokens
                                accepted_transforms.append("corpus_dictionary")
                            else:
                                rejected_transforms.append("corpus_dictionary_no_gain")
                        else:
                            rejected_transforms.append("corpus_dictionary_no_gain")
                    else:
                        rejected_transforms.append("corpus_dictionary_semantic_fail")
                        
            final_text = current_text
            final_tokens = count_tokens(final_text)
            
            # Revert if no gain (economia_liquida <= 0)
            economia_bruta = orig_tokens - final_tokens
            overhead = tokens_sidecar + tokens_aux
            if economia_bruta - overhead <= 0:
                final_text = content
                final_tokens = orig_tokens
                dict_included = False
                tokens_sidecar = 0
                tokens_aux = 0
                best_sidecar_data = None
                semantic_status = "UNCHANGED_NO_TOKEN_GAIN"
            else:
                semantic_status = "SUCCESS"
                
        else:
            final_text = minificar_codigo_para_ia(content, corpus_dict if args.dictionary_scope == "corpus" else None)
            final_tokens = count_tokens(final_text)
            dict_included = True if corpus_dict else False
            tokens_sidecar = 0
            tokens_aux = 0
            if dict_included:
                tokens_sidecar = int(sidecar_tokens_total * orig_tokens / total_orig_tokens)
                tokens_aux = int(auxiliary_tokens * orig_tokens / total_orig_tokens)
                
            economia_bruta = orig_tokens - final_tokens
            overhead = tokens_sidecar + tokens_aux
            if economia_bruta - overhead <= 0:
                final_text = content
                final_tokens = orig_tokens
                dict_included = False
                tokens_sidecar = 0
                tokens_aux = 0
                semantic_status = "UNCHANGED_NO_TOKEN_GAIN"
            else:
                semantic_status = "SUCCESS"
            
        exec_time = time.time() - start_time
        
        # Verify semantics of final_text
        if args.verify_semantics:
            validation_dict = {}
            if dict_included:
                if best_sidecar_data:
                    validation_dict = {v: k for k, v in best_sidecar_data["entries"].items()}
                elif corpus_dict:
                    validation_dict = corpus_dict
            
            is_valid, msg = validate_semantics(content, final_text, validation_dict)
            if not is_valid:
                print(f"Semantic validation failed for {filepath}: {msg}", file=sys.stderr)
                sys.exit(3)
        
        # Check inflation
        if final_tokens > orig_tokens:
            inflation_detected = True
            print(f"WARNING: Inflation in {filepath} ({orig_tokens} -> {final_tokens})")
            
        if not args.dry_run:
            rel_path = os.path.relpath(filepath, src_abs) if os.path.isdir(src_abs) else os.path.basename(filepath)
            dest_path = os.path.join(dst_abs, rel_path)
            
            if profile in ["java", "code"] and not dest_path.endswith('.tknc'):
                dest_path += '.tknc'
                
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(final_text)
                
            if dict_included and best_sidecar_data is not None:
                sidecar_path = dest_path + ".cidatkn"
                write_sidecar(sidecar_path, best_sidecar_data)
                
        report_gen.add_entry(
            filepath=filepath,
            profile=profile,
            tokens_orig=orig_tokens,
            tokens_base=base_tokens,
            tokens_new=final_tokens,
            dict_included=dict_included,
            tokens_sidecar=tokens_sidecar,
            tokens_aux=tokens_aux,
            accepted_transforms=accepted_transforms,
            rejected_transforms=rejected_transforms,
            semantic_status=semantic_status,
            execution_time=exec_time
        )
        
    # Save reports
    report_name = args.report_path
    if not args.dry_run and args.report in ["text", "both", "json"]:
        report_gen.save_reports(report_name + ".md", report_name + ".json", src_abs, args.report)
        print("\nBenchmark reports saved:")
        print(f"  Markdown: {report_name}.md")
        print(f"  JSON:     {report_name}.json")
    
    if args.fail_on_inflation and inflation_detected:
        print("Error: Inflation detected during token optimization.")
        sys.exit(1)
        
    if not args.dry_run:
        verify_destination_sidecars(src_abs, dst_abs)

if __name__ == "__main__":
    main()
