import os
import sys
import subprocess
import time
import json
import hashlib
import shutil

def calculate_file_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_file_sha1(filepath):
    sha1_hash = hashlib.sha1()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha1_hash.update(byte_block)
    return sha1_hash.hexdigest()

def main():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.normpath(os.path.join(dir_path, "../"))
    
    # Paths
    fixtures_dir = os.path.join(project_root, "tests/fixtures/bmad_project")
    output_dir = os.path.join(project_root, "tests/fixtures/bmad_project_mimificado")
    output_dir_1 = os.path.join(project_root, "tests/fixtures/bmad_project_mimificado_1")
    output_dir_2 = os.path.join(project_root, "tests/fixtures/bmad_project_mimificado_2")
    
    # Configure offline environment
    env = os.environ.copy()
    env["TIKTOKEN_CACHE_DIR"] = os.path.join(project_root, "resources")
    
    print("==============================================================")
    print("RUNNING CIDA MOTOR BENCHMARK SUITE (DETERMINISTIC VERIFICATION)")
    print("==============================================================\n")

    # 1. Tokenizer Offline Integrity Check
    cache_file = os.path.join(project_root, "resources/9b5ad71b2ce5302211f9c61530b329a4922fc6a4")
    if not os.path.exists(cache_file):
        cache_file = os.path.join(project_root, "resources/cl100k_base.tiktoken")
        
    if not os.path.exists(cache_file):
        print("Error: cl100k_base tokenizer offline cache not found.")
        sys.exit(1)
    actual_hash = calculate_file_sha1(cache_file)
    expected_hashes = ["9b5ad71b2ce5302211f9c61530b329a4922fc6a4", "6494e42d5aad2bbb441ea9793af9e7db335c8d9c"]
    if actual_hash not in expected_hashes:
        print(f"Error: Tokenizer cache integrity verification failed. Got {actual_hash}")
        sys.exit(1)
    print("[OK] Tokenizer offline cache integrity verified (cl100k_base SHA1 matches expected hash).")

    # 2. Build Go binary to ensure running latest compilation
    go_cli = os.path.join(project_root, "motor_v3.exe" if sys.platform == "win32" else "motor_v3")
    print(f"Building Go binary: {go_cli}...")
    build_cmd = ["go", "build", "-o", go_cli, "motor_v3.go"]
    build_res = subprocess.run(build_cmd, cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if build_res.returncode != 0:
        print(f"Error building Go binary:\n{build_res.stderr.decode('utf-8')}")
        sys.exit(1)
    print("[OK] Go binary built successfully.")

    # Clean up target directories
    for path in [output_dir, output_dir_1, output_dir_2]:
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)

    # 3. Execution - RUN 1
    print("Running minifier: Run 1...")
    cmd_1 = [go_cli, fixtures_dir, output_dir_1, "--profile", "auto", "--dictionary-scope", "file"]
    start_time = time.time()
    res_1 = subprocess.run(cmd_1, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    dur_1 = time.time() - start_time
    if res_1.returncode != 0:
        print(f"Run 1 failed:\n{res_1.stderr}")
        sys.exit(1)

    # 4. Execution - RUN 2
    print("Running minifier: Run 2...")
    cmd_2 = [go_cli, fixtures_dir, output_dir_2, "--profile", "auto", "--dictionary-scope", "file"]
    start_time = time.time()
    res_2 = subprocess.run(cmd_2, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    dur_2 = time.time() - start_time
    if res_2.returncode != 0:
        print(f"Run 2 failed:\n{res_2.stderr}")
        sys.exit(1)

    # 5. Compare Run 1 vs Run 2 Outputs (Strict Determinism Verification)
    print("\nVerifying outputs determinism...")
    files_1 = []
    for root, _, files in os.walk(output_dir_1):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), output_dir_1)
            files_1.append(rel)
            
    files_2 = []
    for root, _, files in os.walk(output_dir_2):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), output_dir_2)
            files_2.append(rel)
            
    if sorted(files_1) != sorted(files_2):
        print(f"Error: Outputs files set mismatch.\nRun 1: {files_1}\nRun 2: {files_2}")
        sys.exit(1)
        
    for rel_path in files_1:
        if "report_local" in rel_path:
            continue
        f1 = os.path.join(output_dir_1, rel_path)
        f2 = os.path.join(output_dir_2, rel_path)
        
        h1 = calculate_file_sha256(f1)
        h2 = calculate_file_sha256(f2)
        
        if h1 != h2:
            print(f"Error: Determinism violation in file {rel_path}.\nRun 1 SHA256: {h1}\nRun 2 SHA256: {h2}")
            sys.exit(1)
            
    print("[OK] Output binary determinism verified (all minified files and sidecars match exactly).")

    # 6. Verify variable data absence in versioned report.json
    report_json_path = os.path.join(output_dir_1, "report.json")
    if not os.path.exists(report_json_path):
        print("Error: report.json was not generated in Run 1.")
        sys.exit(1)
        
    with open(report_json_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)
        
    for e in entries:
        # Verify relative path is used
        if os.path.isabs(e["arquivo"]):
            print(f"Error: Absolute path found in report: {e['arquivo']}")
            sys.exit(1)
        # Verify execution time is zeroed
        if e["tempo_de_execução"] != 0.0:
            print(f"Error: Non-zero execution time found in report: {e['tempo_de_execução']}")
            sys.exit(1)
            
    # Verify no absolute path separators or typical path indicators like 'IdeaProjects'
    report_content = open(report_json_path, 'r', encoding='utf-8').read()
    if "IdeaProjects" in report_content or "Users" in report_content or "\\" in report_content:
        print("Error: Variable environment path info detected in versioned report.json.")
        sys.exit(1)
        
    print("[OK] Report determinism verified (contains relative paths, zeroed timings, and no local environments data).")
    print("\nDeterminism verification: SUCCESS (Both runs generated identical, variable-free outputs with matching SHA256).")

    # Copy files to final output_dir
    for rel_path in files_1:
        src_f = os.path.join(output_dir_1, rel_path)
        dst_f = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(dst_f), exist_ok=True)
        shutil.copy2(src_f, dst_f)

    # Clean temporary directories
    shutil.rmtree(output_dir_1)
    shutil.rmtree(output_dir_2)

    # Print summary table
    print("\nSummary Results:")
    print("-" * 105)
    print(f"{'File':<25} | {'Profile':<10} | {'Orig Tokens':<12} | {'Base Tokens':<12} | {'New Tokens':<12} | {'Gain':<8} | {'Gain %':<8} | {'Status':<10}")
    print("-" * 105)
    
    total_orig = 0
    total_new = 0
    
    for e in entries:
        filename = os.path.basename(e["arquivo"])
        total_orig += e["tokens_originais"]
        total_new += e["tokens_novos"]
        print(f"{filename:<25} | {e['perfil']:<10} | {e['tokens_originais']:<12} | {e['tokens_baseline']:<12} | {e['tokens_novos']:<12} | {e['ganho_absoluto']:<8} | {e['ganho_percentual_medido']:>6.2f}% | {e['status_semântico']:<10}")
        
    print("-" * 105)
    overall_gain_abs = total_orig - total_new
    overall_gain_pct = (overall_gain_abs / total_orig * 100) if total_orig > 0 else 0
    print(f"{'OVERALL':<25} | {'':<10} | {total_orig:<12} | {'':<12} | {total_new:<12} | {overall_gain_abs:<8} | {overall_gain_pct:>6.2f}% |")
    print("-" * 105)

if __name__ == "__main__":
    main()

