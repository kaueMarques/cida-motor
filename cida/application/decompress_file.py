from typing import Optional
from cida.domain.errors import SidecarValidationError, ReconstructionError, SourcePathError
from cida.domain.reconstruction import reconstruct_content
from cida.domain.sidecar import validate_sidecar_schema

class FileDecompressorUsecase:
    def __init__(self, file_repo, json_codec, hash_service=None):
        self.file_repo = file_repo
        self.json_codec = json_codec
        self.hash_service = hash_service

    def decompress(self, compressed_filepath: str, sidecar_filepath: Optional[str] = None) -> bytes:

        if not self.file_repo.exists(compressed_filepath):
            raise SourcePathError(f"Compressed file not found: {compressed_filepath}")

        if sidecar_filepath is None:
            sidecar_filepath = compressed_filepath + ".cidatkn"

        sidecar_data = None
        if self.file_repo.exists(sidecar_filepath):
            try:
                sidecar_raw = self.file_repo.read_text(sidecar_filepath)
                sidecar_data = self.json_codec.decode(sidecar_raw)
            except Exception as e:
                raise SidecarValidationError(f"Failed to read/decode sidecar file: {e}")

            validate_sidecar_schema(sidecar_data)

        compressed_text = self.file_repo.read_text(compressed_filepath)

        if sidecar_data:
            reconstructed_text = reconstruct_content(compressed_text, sidecar_data)
        else:
            reconstructed_text = compressed_text

        reconstructed_bytes = reconstructed_text.encode('utf-8')

        if sidecar_data and "source_sha256" in sidecar_data and self.hash_service:
            expected_sha = sidecar_data["source_sha256"]
            actual_sha = self.hash_service.sha256(reconstructed_bytes)
            if expected_sha.lower() != actual_sha.lower():
                raise ReconstructionError(f"Reconstructed SHA256 mismatch: expected '{expected_sha}', got '{actual_sha}'")

        return reconstructed_bytes

    def decompress_to_file(self, compressed_filepath: str, output_filepath: str, sidecar_filepath: Optional[str] = None) -> bytes:
        reconstructed_bytes = self.decompress(compressed_filepath, sidecar_filepath)
        self.file_repo.write_bytes(output_filepath, reconstructed_bytes)
        return reconstructed_bytes
