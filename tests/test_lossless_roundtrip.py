import os
import sys
import subprocess
import pytest
from pathlib import Path
from cida.infrastructure.filesystem import PhysicalFilesystem
from cida.infrastructure.tokenizer import OfflineTokenizer
from cida.infrastructure.hashing import HashService
from cida.infrastructure.json_codec import JsonCodec
from cida.application.optimize_file import FileOptimizerUsecase
from cida.application.decompress_file import FileDecompressorUsecase

@pytest.fixture(autouse=True)
def setup_env():
    old_val = os.environ.get("TIKTOKEN_CACHE_DIR")
    os.environ["TIKTOKEN_CACHE_DIR"] = os.path.abspath("resources")
    yield
    if old_val is not None:
        os.environ["TIKTOKEN_CACHE_DIR"] = old_val
    else:
        os.environ.pop("TIKTOKEN_CACHE_DIR", None)

def test_production_decompressor_e2e_roundtrip(tmp_path):
    fs = PhysicalFilesystem()
    tok = OfflineTokenizer()
    hs = HashService()
    json_codec = JsonCodec()

    optimizer = FileOptimizerUsecase(tok, fs, hs, json_codec)
    decompressor = FileDecompressorUsecase(fs, json_codec, hs)

    # Collect corpus files recursively excluding ignored paths
    root_path = Path(".")
    ignored_dirs = {".git", ".cida-local", "node_modules", "venv", ".venv", "htmlcov", "__pycache__", "Microsoft", ".pytest_cache", "resources"}

    eligible_files = []
    for ext in ["*.md", "*.txt"]:
        for p in root_path.rglob(ext):
            if any(part in ignored_dirs for part in p.parts):
                continue
            if "_mimificado" in p.name or p.name.endswith(".cidatkn"):
                continue
            eligible_files.append(p)

    eligible_files.sort()
    assert len(eligible_files) > 0

    compressed_count = 0

    for file_path in eligible_files:
        raw_bytes = fs.read_bytes(str(file_path))
        original_text = raw_bytes.decode('utf-8').replace('\r\n', '\n')
        original_bytes = original_text.encode('utf-8')
        original_sha = hs.sha256(original_bytes)


        rel_path = str(file_path).replace('\\', '/')
        compressed_text, sidecar_data, dict_tokens = optimizer.optimize_markdown_dictionary_file_scope(
            original_text, original_text, rel_path, verify_semantics=True
        )

        dst_file = tmp_path / file_path.name
        fs.write_text(str(dst_file), compressed_text)

        sidecar_file = tmp_path / (file_path.name + ".cidatkn")
        if sidecar_data:
            fs.write_text(str(sidecar_file), json_codec.encode(sidecar_data, indent=4))
            compressed_count += 1
            assert fs.exists(str(sidecar_file))
            assert len(sidecar_data.get("entries", {})) > 0

        # Run production application decompressor
        reconstructed_bytes = decompressor.decompress(str(dst_file), str(sidecar_file) if sidecar_data else None)

        assert reconstructed_bytes == original_bytes, f"Byte mismatch for {file_path}"
        assert hs.sha256(reconstructed_bytes) == original_sha, f"SHA mismatch for {file_path}"
        assert len(reconstructed_bytes) == len(original_bytes)

    # Ensure at least one realistic file underwent real token compression with sidecar
    assert compressed_count > 0, "No file was compressed in lossless E2E roundtrip"

def test_cli_decompressor_subprocess_roundtrip(tmp_path):
    fs = PhysicalFilesystem()
    hs = HashService()

    fixture_src = Path("tests/fixtures/lossless/repetitive_realistic.md")
    assert fixture_src.exists()

    original_bytes = fs.read_bytes(str(fixture_src))
    original_sha = hs.sha256(original_bytes)

    dst_dir = tmp_path / "out"
    dst_dir.mkdir()

    # 1. Compress with CLI in lossless mode
    compress_cmd = [
        sys.executable, "token_optimizer.py",
        "--src", str(fixture_src),
        "--dst", str(dst_dir),
        "--mode", "lossless",
        "--dictionary-scope", "file"
    ]
    res_comp = subprocess.run(compress_cmd, capture_output=True, text=True)
    assert res_comp.returncode == 0, f"Compression CLI failed: {res_comp.stderr}"

    comp_file = dst_dir / fixture_src.name
    sidecar_file = dst_dir / (fixture_src.name + ".cidatkn")

    assert comp_file.exists()
    assert sidecar_file.exists()

    compressed_bytes = fs.read_bytes(str(comp_file))
    assert compressed_bytes != original_bytes, "Expected compression gain on realistic fixture"

    # 2. Decompress with CLI
    decomp_out = tmp_path / "reconstructed.md"
    decompress_cmd = [
        sys.executable, "-m", "cida.interfaces.decompress_cli",
        "--src", str(comp_file),
        "--dst", str(decomp_out),
        "--sidecar", str(sidecar_file)
    ]
    res_decomp = subprocess.run(decompress_cmd, capture_output=True, text=True)
    assert res_decomp.returncode == 0, f"Decompression CLI failed: {res_decomp.stderr}"

    reconstructed_bytes = fs.read_bytes(str(decomp_out))
    assert reconstructed_bytes == original_bytes
    assert hs.sha256(reconstructed_bytes) == original_sha
