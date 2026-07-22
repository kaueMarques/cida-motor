import unittest
import os
import json
import tempfile
import shutil
from markdown.sidecar import (
    create_sidecar_data, validate_sidecar_schema, read_sidecar, write_sidecar,
    SidecarValidationError, calculate_sha256, validate_sidecar
)

class TestSidecarDictionaries(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.source_content = "This is a clean implementation test content."
        self.entries = {
            "AA": "implementation",
            "BB": "content"
        }
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_create_and_validate_sidecar_success(self):
        data = create_sidecar_data("test.md", self.source_content.encode('utf-8'), self.entries)
        # Should validate without throwing any error
        validate_sidecar_schema(data)
        
        self.assertEqual(data["format"], "cida-token-sidecar")
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["source"], "test.md")
        self.assertEqual(data["source_sha256"], calculate_sha256(self.source_content.encode('utf-8')))
        self.assertEqual(len(data["entries"]), 2)
        
        # Verify entries structure
        self.assertEqual(data["entries"]["AA"], "implementation")
        self.assertEqual(data["entries"]["BB"], "content")
        
    def test_duplicate_value_throws(self):
        bad_entries = {
            "AA": "common",
            "BB": "common"
        }
        with self.assertRaises(SidecarValidationError):
            create_sidecar_data("test.md", self.source_content.encode('utf-8'), bad_entries)
            
    def test_unsupported_format(self):
        data = create_sidecar_data("test.md", self.source_content.encode('utf-8'), self.entries)
        data["format"] = "other-format"
        with self.assertRaises(SidecarValidationError):
            validate_sidecar_schema(data)
            
    def test_unsupported_version(self):
        data = create_sidecar_data("test.md", self.source_content.encode('utf-8'), self.entries)
        data["version"] = 2
        with self.assertRaises(SidecarValidationError):
            validate_sidecar_schema(data)
            
    def test_missing_required_keys(self):
        data = create_sidecar_data("test.md", self.source_content.encode('utf-8'), self.entries)
        del data["source_sha256"]
        with self.assertRaises(SidecarValidationError):
            validate_sidecar_schema(data)
            
    def test_write_and_read_sidecar(self):
        data = create_sidecar_data("test.md", self.source_content.encode('utf-8'), self.entries)
        sidecar_path = os.path.join(self.temp_dir, "test.md.cidatkn")
        
        write_sidecar(sidecar_path, data)
        
        self.assertTrue(os.path.exists(sidecar_path))
        
        read_data = read_sidecar(sidecar_path)
        self.assertEqual(read_data["source_sha256"], data["source_sha256"])
        self.assertEqual(read_data["entries"], data["entries"])

    def test_compress_decompress_roundtrip(self):
        # Configure offline cache for this test too
        import sys
        dir_path = os.path.dirname(os.path.abspath(__file__))
        os.environ["TIKTOKEN_CACHE_DIR"] = os.path.normpath(os.path.join(dir_path, "../resources"))

        content = "# Title\nThis is a long line with implementation detail and another implementation detail."
        
        from token_optimizer import optimize_markdown_dictionary_file_scope
        
        minified, sidecar_data, dict_tokens = optimize_markdown_dictionary_file_scope(content, content, "test.md", verify_semantics=True)
        
        if sidecar_data:
            mapping = sidecar_data["entries"]
            
            import re
            decompressed = minified
            sorted_aliases = sorted(mapping.keys(), key=len, reverse=True)
            for alias in sorted_aliases:
                pattern = re.compile(rf'\b{re.escape(alias)}\b')
                decompressed = pattern.sub(mapping[alias], decompressed)
                
            from markdown.semantic_validator import validate_semantics
            is_valid, msg = validate_semantics(content, minified, mapping)
            self.assertTrue(is_valid, f"Roundtrip semantic check failed: {msg}")

if __name__ == "__main__":
    unittest.main()
