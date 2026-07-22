import json
import hashlib
import os
import re

class SidecarValidationError(ValueError):
    pass

def calculate_sha256(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def create_sidecar_data(source_name, original_content, entries):
    """
    Creates the dictionary structure for the sidecar JSON.
    source_name: relative path to source file.
    original_content: string or bytes of original file content.
    entries: dictionary of {alias: value}.
    """
    if not isinstance(entries, dict):
        raise SidecarValidationError("Entries must be a dictionary")

    # Check for empty entries, types, duplicate values
    aliases = set()
    values = set()
    for alias, val in entries.items():
        if not isinstance(alias, str) or not isinstance(val, str):
            raise SidecarValidationError("Alias and value must be strings")
        if not alias.strip() or not val.strip():
            raise SidecarValidationError("Alias and value must not be empty")
        if alias in aliases:
            raise SidecarValidationError(f"Duplicate alias in entries: {alias}")
        if val in values:
            raise SidecarValidationError(f"Duplicate value in entries: {val}")
        aliases.add(alias)
        values.add(val)

    # Sort entries deterministically by alias keys
    sorted_entries = {}
    for alias in sorted(entries.keys()):
        sorted_entries[alias] = entries[alias]

    source_rel = source_name.replace('\\', '/')
    return {
        "format": "cida-token-sidecar",
        "version": 1,
        "source": source_rel,
        "source_sha256": calculate_sha256(original_content),
        "entries": sorted_entries
    }

def validate_sidecar_schema(data):
    if not isinstance(data, dict):
        raise SidecarValidationError("Sidecar must be a JSON object")
    
    required_keys = ["format", "version", "source", "source_sha256", "entries"]
    for k in required_keys:
        if k not in data:
            raise SidecarValidationError(f"Missing required key: {k}")
            
    if data["format"] != "cida-token-sidecar":
        raise SidecarValidationError(f"Unsupported format: {data['format']}")
        
    if data["version"] != 1:
        raise SidecarValidationError(f"Unsupported version: {data['version']}")
        
    if not isinstance(data["entries"], dict):
        raise SidecarValidationError("entries must be a dictionary")
        
    aliases = set()
    values = set()
    for alias, val in data["entries"].items():
        if not isinstance(alias, str) or not isinstance(val, str):
            raise SidecarValidationError("Alias and value must be strings")
        if not alias.strip() or not val.strip():
            raise SidecarValidationError("Alias and value must not be empty")
        if alias in aliases:
            raise SidecarValidationError(f"Duplicate alias detected: {alias}")
        if val in values:
            raise SidecarValidationError(f"Duplicate value detected: {val}")
        aliases.add(alias)
        values.add(val)

def validate_sidecar(data, expected_rel_path, original_bytes):
    """
    Fully validates the sidecar data against the expected relative path and original file bytes.
    """
    validate_sidecar_schema(data)
    
    # Check source path compatibility (normalized to forward slashes)
    src_norm = data["source"].replace('\\', '/')
    exp_norm = expected_rel_path.replace('\\', '/')
    if src_norm != exp_norm:
        raise SidecarValidationError(f"Source path mismatch: expected '{exp_norm}', got '{src_norm}'")
        
    # Validate SHA-256 format
    sha = data["source_sha256"]
    if not sha or len(sha) != 64 or not all(c in '0123456789abcdefABCDEF' for c in sha):
        raise SidecarValidationError(f"SHA-256 is missing, malformed or non-hexadecimal: {sha}")
        
    # Verify calculated SHA-256
    calculated_sha = calculate_sha256(original_bytes)
    if sha.lower() != calculated_sha.lower():
        raise SidecarValidationError(f"SHA-256 mismatch: calculated '{calculated_sha}', got '{sha}'")
        
    # Verify aliases do not collide with content words
    original_text = original_bytes.decode('utf-8', errors='ignore')
    original_words = set(re.findall(r'\b\w+\b', original_text))
    for alias in data["entries"].keys():
        if alias in original_words:
            raise SidecarValidationError(f"Alias '{alias}' collides with content word in original file")

def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SidecarValidationError(
                f"Duplicate JSON key: {key}"
            )
        result[key] = value
    return result

def read_sidecar(sidecar_path):
    if not os.path.exists(sidecar_path):
        raise SidecarValidationError(f"Sidecar file not found: {sidecar_path}")
    try:
        with open(sidecar_path, 'r', encoding='utf-8') as f:
            data = json.load(f, object_pairs_hook=reject_duplicate_keys)
    except Exception as e:
        raise SidecarValidationError(f"Failed to parse sidecar JSON: {e}")
        
    validate_sidecar_schema(data)
    return data

def write_sidecar(sidecar_path, data):
    validate_sidecar_schema(data)
    os.makedirs(os.path.dirname(os.path.abspath(sidecar_path)), exist_ok=True)
    with open(sidecar_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

