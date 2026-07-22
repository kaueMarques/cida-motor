import os
import sys
import argparse
import time
import json
import re
import shutil
from markdown.protected_regions import ProtectedRegionsManager
from markdown.phrase_dictionary import (
    count_tokens, build_file_dictionary, apply_dictionary,
    generate_alias_candidates, find_candidate_words
)
from markdown.semantic_validator import validate_semantics
from markdown.report import ReportGenerator

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

def main():
    parser = argparse.ArgumentParser(description="Token-oriented Markdown Minifier for BMAD")
    parser.add_argument("--src", required=True, help="Source directory or file")
    parser.add_argument("--dst", required=True, help="Destination directory")
    parser.add_argument("--profile", default="auto", choices=["auto", "code", "java", "markdown", "bmad"], help="Processing profile")
    parser.add_argument("--dictionary-scope", default="file", choices=["none", "file", "corpus", "workflow-session"], help="Dictionary scope")
    parser.add_argument("--fail-on-inflation", action="store_true", help="Fail if any file has token count inflation")
    parser.add_argument("--report", default="text", choices=["text", "json", "both"], help="Report format")
    parser.add_argument("--report-path", default="report", help="Report output path (without extension)")
    parser.add_argument("--verify-semantics", action="store_true", default=True, help="Run semantic validations")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no files written)")
    
    args = parser.parse_args()
    
    src_abs = os.path.abspath(args.src)
    dst_abs = os.path.abspath(args.dst)
    
    if not os.path.exists(src_abs):
        print(f"Error: Source not found: {src_abs}")
        sys.exit(1)
        
    # Collect files
    files_to_process = []
    if os.path.isfile(src_abs):
        files_to_process.append(src_abs)
    else:
        for root, dirs, files in os.walk(src_abs):
            # Exclude destination folder to prevent infinite loop
            if dst_abs in os.path.abspath(root):
                continue
            for f in files:
                filepath = os.path.join(root, f)
                # Exclude dictionary folder and already minified files
                if "tknd" in filepath or "_mimificado" in f:
                    continue
                files_to_process.append(filepath)
                
    report_gen = ReportGenerator()
    
    # 1. Corpus-level dictionary preparation
    corpus_dict = {}
    if args.dictionary_scope in ["corpus", "workflow-session"]:
        all_contents = []
        for fp in files_to_process:
            if not is_binary_file(fp) and (fp.endswith('.md') or fp.endswith('.txt')):
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                        all_contents.append(f.read())
                except:
                    pass
        corpus_dict = build_corpus_dictionary(all_contents)
        
        # Write corpus dictionary file if not dry run and we have entries
        if corpus_dict and not args.dry_run:
            tknd_dir = os.path.join(dst_abs, "tknd")
            os.makedirs(tknd_dir, exist_ok=True)
            # Write in segments of 500
            items = list(corpus_dict.items())
            for i in range(0, len(items), 500):
                chunk = items[i:i+500]
                # Format start ID based on index
                prefixChars = "ABCDEF"
                start_id = prefixChars[min(i // 500, len(prefixChars)-1)] + str(i % 500)
                dict_file_path = os.path.join(tknd_dir, f"{start_id}.tknd")
                with open(dict_file_path, 'w', encoding='utf-8') as df:
                    for word, alias in chunk:
                        df.write(f"{alias}={word}\n")

    # 2. Process each file
    inflation_detected = False
    
    for filepath in files_to_process:
        start_time = time.time()
        
        # Handle binary files - just copy them
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
            # Legacy md_minifier logic:
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
            # Code/Java baseline:
            legacy = minificar_codigo_para_ia(content)
            base_tokens = count_tokens(legacy)
            
        # Otimização
        accepted_transforms = []
        rejected_transforms = []
        
        if profile in ["markdown", "bmad"]:
            current_text = content
            
            # Transformation candidates list
            # We apply each candidate and verify monotonic reduction + semantic validity
            candidates = [
                ("remove_html_comments", remove_html_comments),
                ("trim_trailing_whitespace", trim_trailing_whitespace),
                ("normalize_newlines", normalize_newlines),
                ("table_whitespace", table_whitespace),
                ("list_compaction", list_compaction),
            ]
            
            for name, trans_fn in candidates:
                candidate_text = trans_fn(current_text)
                
                # Check semantic validation
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
            header_dict = ""
            dict_included = False
            tokens_dict = 0
            
            if args.dictionary_scope == "file":
                pm = ProtectedRegionsManager()
                file_dict, header_dict = build_file_dictionary(current_text, pm)
                if file_dict:
                    candidate_text = header_dict + apply_dictionary(current_text, file_dict, pm)
                    
                    # Verify semantics of dictionary applied version
                    if args.verify_semantics:
                        is_valid, _ = validate_semantics(content, candidate_text, file_dict)
                        if is_valid:
                            cand_tokens = count_tokens(candidate_text)
                            curr_tokens = count_tokens(current_text)
                            if cand_tokens < curr_tokens:
                                current_text = candidate_text
                                dict_included = True
                                tokens_dict = count_tokens(header_dict)
                                accepted_transforms.append("file_dictionary")
                            else:
                                rejected_transforms.append("file_dictionary_no_gain")
                        else:
                            rejected_transforms.append("file_dictionary_semantic_fail")
                            
            elif args.dictionary_scope in ["corpus", "workflow-session"] and corpus_dict:
                pm = ProtectedRegionsManager()
                candidate_text = apply_dictionary(current_text, corpus_dict, pm)
                
                # Verify semantics
                if args.verify_semantics:
                    is_valid, _ = validate_semantics(content, candidate_text, corpus_dict)
                    if is_valid:
                        cand_tokens = count_tokens(candidate_text)
                        curr_tokens = count_tokens(current_text)
                        if cand_tokens < curr_tokens:
                            current_text = candidate_text
                            dict_included = True
                            tokens_dict = 0 # Dictionary cost is counted globally at corpus level
                            accepted_transforms.append("corpus_dictionary")
                        else:
                            rejected_transforms.append("corpus_dictionary_no_gain")
                    else:
                        rejected_transforms.append("corpus_dictionary_semantic_fail")
                        
            final_text = current_text
            final_tokens = count_tokens(final_text)
            
            # Monotonic Safety fallback: If final tokens is not less than original, revert
            if final_tokens >= orig_tokens:
                final_text = content
                final_tokens = orig_tokens
                semantic_status = "UNCHANGED_NO_TOKEN_GAIN"
            else:
                semantic_status = "SUCCESS"
                
        else:
            # Code/Java optimization:
            final_text = minificar_codigo_para_ia(content, corpus_dict if args.dictionary_scope in ["corpus", "workflow-session"] else None)
            final_tokens = count_tokens(final_text)
            dict_included = True if corpus_dict else False
            tokens_dict = 0
            semantic_status = "SUCCESS"
            
        exec_time = time.time() - start_time
        
        # Check inflation
        if final_tokens > orig_tokens:
            inflation_detected = True
            print(f"WARNING: Inflation in {filepath} ({orig_tokens} -> {final_tokens})")
            
        # Write output
        if not args.dry_run:
            rel_path = os.path.relpath(filepath, src_abs) if os.path.isdir(src_abs) else os.path.basename(filepath)
            
            # Preserve folder structure
            dest_path = os.path.join(dst_abs, rel_path)
            
            # Suffix .tknc for java, keep .md for markdown
            if profile in ["java", "code"] and not dest_path.endswith('.tknc'):
                dest_path += '.tknc'
                
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(final_text)
                
        report_gen.add_entry(
            filepath=filepath,
            profile=profile,
            tokens_orig=orig_tokens,
            tokens_base=base_tokens,
            tokens_new=final_tokens,
            dict_included=dict_included,
            tokens_dict=tokens_dict,
            accepted_transforms=accepted_transforms,
            rejected_transforms=rejected_transforms,
            semantic_status=semantic_status,
            execution_time=exec_time
        )
        
    # Save reports
    report_name = args.report_path
    if args.report in ["text", "both"]:
        report_gen.save_reports(report_name + ".md", report_name + ".json")
    elif args.report == "json":
        report_gen.save_reports(report_name + ".md", report_name + ".json")
        
    print("\nBenchmark reports saved:")
    print(f"  Markdown: {report_name}.md")
    print(f"  JSON:     {report_name}.json")
    
    if args.fail_on_inflation and inflation_detected:
        print("Error: Inflation detected during token optimization.")
        sys.exit(1)

if __name__ == "__main__":
    main()
