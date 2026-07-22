import unittest
import sys
import os
import shutil
import subprocess
import json
import hashlib

# Configure offline tiktoken cache
dir_path = os.path.dirname(os.path.abspath(__file__))
os.environ["TIKTOKEN_CACHE_DIR"] = os.path.normpath(os.path.join(dir_path, "../resources"))

class TestPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath("tests/fixtures/integration_sandbox")
        self.src_dir = os.path.join(self.test_dir, "src")
        self.dst_dir = os.path.join(self.test_dir, "dst")
        
        # Clean up
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
        os.makedirs(self.src_dir, exist_ok=True)
        os.makedirs(self.dst_dir, exist_ok=True)
        
        # Create mock files
        with open(os.path.join(self.src_dir, "A.java"), "w", encoding="utf-8") as f:
            f.write("package com.test;\npublic class A {\n    // comment\n    public void test() {}\n}")
            
        with open(os.path.join(self.src_dir, "B.java"), "w", encoding="utf-8") as f:
            f.write("package com.test;\npublic class B {\n    public void other() {}\n}")
            
        with open(os.path.join(self.src_dir, "workflow.md"), "w", encoding="utf-8") as f:
            f.write("# Workflow\n\nThis is workflow content with must option.\n")
            
        with open(os.path.join(self.src_dir, "step-01.md"), "w", encoding="utf-8") as f:
            f.write("# Step 1\n\nSome step description.\n")
            
        with open(os.path.join(self.src_dir, "logo.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
            
        with open(os.path.join(self.src_dir, "config.json"), "w", encoding="utf-8") as f:
            f.write('{"unsupported": true}')
            
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_integration_pipeline_run(self):
        # Run go program motor_v3.go
        cmd = [
            "go", "run", "motor_v3.go",
            self.src_dir,
            self.dst_dir,
            "--profile", "auto",
            "--dictionary-scope", "file",
            "--report", "both"
        ]
        
        # Setup Tiktoken cache dir env variable
        env = os.environ.copy()
        env["TIKTOKEN_CACHE_DIR"] = os.path.abspath("resources")
        
        result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, f"Execution failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        
        # Check files exist in destination
        self.assertTrue(os.path.exists(os.path.join(self.dst_dir, "A.java.tknc")))
        self.assertTrue(os.path.exists(os.path.join(self.dst_dir, "B.java.tknc")))
        self.assertTrue(os.path.exists(os.path.join(self.dst_dir, "workflow.md")))
        self.assertTrue(os.path.exists(os.path.join(self.dst_dir, "step-01.md")))
        self.assertTrue(os.path.exists(os.path.join(self.dst_dir, "logo.png")))
        self.assertTrue(os.path.exists(os.path.join(self.dst_dir, "config.json")))
        
        # Check that binary and unsupported files were copied without change
        with open(os.path.join(self.src_dir, "logo.png"), "rb") as sf, open(os.path.join(self.dst_dir, "logo.png"), "rb") as df:
            self.assertEqual(sf.read(), df.read())
            
        with open(os.path.join(self.src_dir, "config.json"), "rb") as sf, open(os.path.join(self.dst_dir, "config.json"), "rb") as df:
            self.assertEqual(sf.read(), df.read())
            
        # Check report
        report_json_path = os.path.join(self.dst_dir, "report.json")
        self.assertTrue(os.path.exists(report_json_path))
        
        with open(report_json_path, "r", encoding="utf-8") as rf:
            entries = json.load(rf)
            
        # We expect entries for: A.java, B.java, workflow.md, step-01.md
        # Logo.png and config.json should not be treated as text optimization entries
        self.assertEqual(len(entries), 4)
        
        processed_files = [os.path.basename(e["arquivo"]) for e in entries]
        self.assertIn("A.java", processed_files)
        self.assertIn("B.java", processed_files)
        self.assertIn("workflow.md", processed_files)
        self.assertIn("step-01.md", processed_files)
        
        # Verify no duplicates
        self.assertEqual(len(processed_files), len(set(processed_files)))
        
        # Verify reported contents correspond to final files on disk
        for e in entries:
            rel_path = e["arquivo"]
            dest_file = os.path.join(self.dst_dir, rel_path)
            if e["perfil"] == "java":
                dest_file += ".tknc"
            self.assertTrue(os.path.exists(dest_file))
            with open(dest_file, "r", encoding="utf-8") as df:
                disk_content = df.read()
                
            # Verify that the final token count matches what is on disk
            # Calculate tokens using the tiktoken offline cache
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            disk_tokens = len(enc.encode(disk_content))
            self.assertEqual(e["tokens_novos"], disk_tokens)

if __name__ == "__main__":
    unittest.main()
