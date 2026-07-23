import os
import re
import pytest
import glob
from cida.infrastructure.filesystem import PhysicalFilesystem
from cida.infrastructure.tokenizer import OfflineTokenizer
from cida.infrastructure.hashing import HashService
from cida.markdown.dictionary import apply_dictionary, build_file_dictionary
from cida.markdown.protected_regions import ProtectedRegionsManager
from cida.markdown.semantic_equivalence import validate_semantics

@pytest.fixture(autouse=True)
def setup_env():
    old_val = os.environ.get("TIKTOKEN_CACHE_DIR")
    os.environ["TIKTOKEN_CACHE_DIR"] = os.path.abspath("resources")
    yield
    if old_val is not None:
        os.environ["TIKTOKEN_CACHE_DIR"] = old_val
    else:
        os.environ.pop("TIKTOKEN_CACHE_DIR", None)

def decompress_lossless(compressed_text: str, sidecar_entries: dict) -> str:
    """
    Reverses dictionary alias substitutions at word boundaries to reconstruct original text.
    In Lossless mode: decompress(compress(original_bytes)) == original_bytes.
    """
    if not sidecar_entries:
        return compressed_text

    result = compressed_text
    # Remove AI RAG DICT header if added
    if result.startswith("> 🤖 AI RAG DICT: "):
        parts = result.split("\n\n", 1)
        if len(parts) > 1:
            result = parts[1]

    # Reconstruct aliases back to original words using word boundaries
    sorted_entries = sorted(sidecar_entries.items(), key=lambda x: len(x[0]), reverse=True)
    for alias, word in sorted_entries:
        pattern = re.compile(rf'\b{re.escape(alias)}\b')
        result = pattern.sub(word, result)

    return result

def test_real_corpus_lossless_roundtrip():
    fs = PhysicalFilesystem()
    tok = OfflineTokenizer()
    hs = HashService()

    # Find real Markdown files in the repository corpus
    real_files = glob.glob("tests/fixtures/bmad_project/*.md") + glob.glob("specs/**/*.md", recursive=True) + glob.glob("*.md")
    assert len(real_files) > 0

    results = []
    for filepath in sorted(real_files):
        original_bytes = fs.read_bytes(filepath)
        original_sha256 = hs.sha256(original_bytes)
        original_text = original_bytes.decode('utf-8', errors='ignore')

        # Run dictionary optimization in Lossless mode (only reversible alias substitution)
        pm = ProtectedRegionsManager()
        dictionary, header = build_file_dictionary(original_text, pm, tok, min_margin=0)

        compressed_text = original_text
        sidecar_created = False
        sidecar_entries = {}

        if dictionary:
            compressed_text = header + apply_dictionary(original_text, dictionary, pm)
            sidecar_entries = {alias: word for word, alias in dictionary.items()}
            sidecar_created = True

        # Decompress lossless
        reconstructed_text = decompress_lossless(compressed_text, sidecar_entries)
        reconstructed_bytes = reconstructed_text.encode('utf-8')

        # Assert lossless byte-perfect equality
        assert reconstructed_bytes == original_bytes, f"Lossless roundtrip failed for {filepath}"

        # Verify semantic validity for markdown files
        is_semantic_valid = True
        if filepath.endswith(".md") and not filepath.endswith("LICENSE.md"):
            is_semantic_valid, reason = validate_semantics(original_text, compressed_text, dictionary)
            assert is_semantic_valid, f"Semantic validation failed for {filepath}: {reason}"

        results.append({
            "source": filepath,
            "original_sha256": original_sha256,
            "reconstructed_sha256": hs.sha256(reconstructed_bytes),
            "original_size": len(original_bytes),
            "reconstructed_size": len(reconstructed_bytes),
            "roundtrip_byte_perfect": reconstructed_bytes == original_bytes,
            "semantic_valid": is_semantic_valid,
            "sidecar_created": sidecar_created
        })

    assert len(results) > 0
    assert all(r["roundtrip_byte_perfect"] for r in results)
    assert all(r["semantic_valid"] for r in results)
