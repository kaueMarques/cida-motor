import os
import sys
import pytest
from unittest.mock import patch
from cida.interfaces.decompress_cli import main as decompress_main
from cida.application.decompress_file import FileDecompressorUsecase
from cida.infrastructure.filesystem import PhysicalFilesystem
from cida.infrastructure.hashing import HashService
from cida.infrastructure.json_codec import JsonCodec
from cida.domain.errors import SourcePathError, ReconstructionError

def test_decompress_cli_main_success(tmp_path):
    fs = PhysicalFilesystem()
    hs = HashService()
    jc = JsonCodec()

    src_file = tmp_path / "compressed.md"
    sidecar_file = tmp_path / "compressed.md.cidatkn"
    dst_file = tmp_path / "decompressed.md"

    orig_content = b"This is repeattoken candidate text repeattoken candidate text"
    orig_sha = hs.sha256(orig_content)

    compressed_content = "This is AA candidate text AA candidate text"
    src_file.write_text(compressed_content)

    sidecar_data = {
        "format": "cida-token-sidecar",
        "version": 1,
        "source": "compressed.md",
        "source_sha256": orig_sha,
        "entries": {"AA": "repeattoken"}
    }
    sidecar_file.write_text(jc.encode(sidecar_data, indent=4))

    test_args = ["decompress_cli.py", "--src", str(src_file), "--dst", str(dst_file)]
    with patch.object(sys, "argv", test_args):
        decompress_main()

    assert dst_file.exists()
    assert dst_file.read_bytes() == orig_content

def test_decompress_cli_main_cida_error(tmp_path):
    test_args = ["decompress_cli.py", "--src", str(tmp_path / "nonexistent.md"), "--dst", str(tmp_path / "out.md")]
    with patch.object(sys, "argv", test_args), patch("sys.exit") as mock_exit:
        decompress_main()
        mock_exit.assert_called_with(4)

def test_decompress_cli_main_unexpected_error(tmp_path):
    test_args = ["decompress_cli.py", "--src", str(tmp_path / "file.md"), "--dst", str(tmp_path / "out.md")]
    with patch.object(sys, "argv", test_args), \
         patch("cida.application.decompress_file.FileDecompressorUsecase.decompress_to_file", side_effect=Exception("crash")), \
         patch("sys.exit") as mock_exit:
        decompress_main()
        mock_exit.assert_called_with(5)

def test_decompress_file_usecase_edge_cases(tmp_path):
    fs = PhysicalFilesystem()
    hs = HashService()
    jc = JsonCodec()

    usecase = FileDecompressorUsecase(fs, jc, hs)

    # Source missing
    with pytest.raises(SourcePathError):
        usecase.decompress_file(str(tmp_path / "missing.md"))

    # Sidecar missing
    src = tmp_path / "doc.md"
    src.write_text("hello")
    with pytest.raises(SourcePathError):
        usecase.decompress_file(str(src))

    # Sha mismatch error
    sidecar_file = tmp_path / "doc.md.cidatkn"
    sidecar_data = {
        "format": "cida-token-sidecar",
        "version": 1,
        "source": "doc.md",
        "source_sha256": "0" * 64,
        "entries": {"AA": "val"}
    }
    sidecar_file.write_text(jc.encode(sidecar_data, indent=4))
    with pytest.raises(ReconstructionError, match="Reconstructed content SHA-256 digest mismatch"):
        usecase.decompress_file(str(src))
