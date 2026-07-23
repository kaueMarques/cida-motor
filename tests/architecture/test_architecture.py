import os
import ast
import unittest

class TestArchitecture(unittest.TestCase):
    def setUp(self):
        self.project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../"))
        self.domain_dir = os.path.join(self.project_root, "cida/domain")
        self.application_dir = os.path.join(self.project_root, "cida/application")
        self.markdown_dir = os.path.join(self.project_root, "cida/markdown")

    def _get_imports(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def test_domain_dependencies(self):
        """Domain must not import from application, infrastructure, interfaces or markdown layers."""
        for root, _, files in os.walk(self.domain_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    imports = self._get_imports(filepath)
                    for imp in imports:
                        self.assertFalse(
                            imp.startswith("cida.application") or
                            imp.startswith("cida.infrastructure") or
                            imp.startswith("cida.interfaces") or
                            imp.startswith("cida.markdown"),
                            f"Domain file {file} violates clean architecture by importing {imp}"
                        )

    def test_domain_no_forbidden_builtin_modules(self):
        """Domain must not import os, pathlib, subprocess, argparse, tempfile, shutil, tiktoken, yaml, or sys."""
        forbidden = ["os", "pathlib", "subprocess", "argparse", "tempfile", "shutil", "tiktoken", "yaml", "sys"]
        for root, _, files in os.walk(self.domain_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    imports = self._get_imports(filepath)
                    for imp in imports:
                        for f in forbidden:
                            # Allow exact or submodules, e.g. yaml.constructor
                            self.assertFalse(
                                imp == f or imp.startswith(f + "."),
                                f"Domain file {file} violates clean architecture by importing standard/external module: {imp}"
                            )

    def test_application_layer_dependencies(self):
        """Application must not import concrete infrastructure or interfaces."""
        for root, _, files in os.walk(self.application_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    imports = self._get_imports(filepath)
                    for imp in imports:
                        self.assertFalse(
                            imp.startswith("cida.infrastructure") or imp.startswith("cida.interfaces"),
                            f"Application file {file} violates clean architecture by importing infrastructure/interface: {imp}"
                        )

    def test_no_sys_exit_outside_cli(self):
        """sys.exit() is only allowed in interfaces/cli.py and wrapper/helper entrypoints."""
        for root, _, files in os.walk(os.path.join(self.project_root, "cida")):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    if "interfaces/cli.py" in filepath.replace("\\", "/"):
                        continue
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.assertNotIn("sys.exit(", content, f"sys.exit found in non-CLI file: {filepath}")

    def test_no_raw_file_writing_in_domain(self):
        """Writing/Creating files should not happen inside domain files."""
        for root, _, files in os.walk(self.domain_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.assertNotIn("open(", content, f"open(...) file-handler call found in domain file: {filepath}")
                    self.assertNotIn("write(", content, f"write(...) call found in domain file: {filepath}")

    def test_no_environ_access_in_domain(self):
        """os.environ must not be used in domain."""
        for root, _, files in os.walk(self.domain_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.assertNotIn("environ", content, f"Environment variable access found in domain file: {filepath}")

if __name__ == "__main__":
    unittest.main()
