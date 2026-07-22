import os
import sys
import subprocess
import time
import json

def main():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.normpath(os.path.join(dir_path, "../"))
    
    # Paths
    fixtures_dir = os.path.join(project_root, "tests/fixtures/bmad_project")
    output_dir = os.path.join(project_root, "tests/fixtures/bmad_project_mimificado")
    
    # Configure offline environment
    env = os.environ.copy()
    env["TIKTOKEN_CACHE_DIR"] = os.path.join(project_root, "resources")
    
    # We will execute the compiled Go CLI (motor_v3.exe) on the fixtures directory
    go_cli = os.path.join(project_root, "motor_v3.exe")
    
    if not os.path.exists(go_cli):
        print("Error: Go CLI motor_v3.exe binary not found. Please compile it first.")
        sys.exit(1)
        
    print("==============================================================")
    print("RUNNING CIDA MOTOR BENCHMARK SUITE")
    print("==============================================================\n")
    
    cmd = [
        go_cli,
        fixtures_dir,
        output_dir,
        "--profile", "auto",
        "--dictionary-scope", "file"
    ]
    
    start_time = time.time()
    result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    duration = time.time() - start_time
    
    if result.returncode != 0:
        print("Error running benchmark suite:")
        print(result.stderr)
        sys.exit(1)
        
    safe_stdout = result.stdout.encode('ascii', errors='replace').decode('ascii')
    print(safe_stdout)
    
    # Read generated JSON report
    report_json_path = os.path.join(output_dir, "report.json")
    report_md_path = os.path.join(output_dir, "report.md")
    
    if not os.path.exists(report_json_path):
        print("Error: report.json was not generated.")
        sys.exit(1)
        
    with open(report_json_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)
        
    print(f"Benchmark completed successfully in {duration:.4f} seconds.")
    print(f"Processed {len(entries)} files.\n")
    
    # Print summary table
    print("Summary Results:")
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
