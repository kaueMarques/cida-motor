import unittest
import os
import subprocess
import sys
import tempfile
import shutil

class TestCLIExitCodes(unittest.TestCase):
    def setUp(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.normpath(os.path.join(dir_path, "../"))
        self.go_cli = os.path.join(self.project_root, "motor_v3.exe" if sys.platform == "win32" else "motor_v3")
        
        # Build Go binary unconditionally to ensure latest changes are included
        subprocess.run(["go", "build", "-o", self.go_cli, "motor_v3.go"], cwd=self.project_root)
            
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_exit_code_1_no_args(self):
        # Running Go CLI without arguments should exit with code 1
        res = subprocess.run([self.go_cli], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(res.returncode, 1)
        
    def test_exit_code_4_not_found(self):
        # Running Go CLI on a non-existent source directory should exit with code 4
        res = subprocess.run([self.go_cli, "non_existent_folder_xyz"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(res.returncode, 4)

if __name__ == "__main__":
    unittest.main()
