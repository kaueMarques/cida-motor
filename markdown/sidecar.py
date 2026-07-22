import json
import hashlib
import os

class SidecarValidationError(Exception):
    pass

def calculate_sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def create_sidecar_data(source_name, original_content, entries):
    """
    Creates the dictionary structure for the sidecar JSON.
    entries: list of dicts like {"alias": "AA", "value": "original"}
    """
    # Unique check for aliases and values
    aliases = set()
    values = set()
    for entry in entries:
        alias = entry.get("alias")
        val = entry.get("value")
        if not alias or not val:
            raise SidecarValidationError("Invalid entry: alias and value are required")
        if alias in aliases:
            raise SidecarValidationError(f"Duplicate alias in entries: {alias}")
        if val in values:
            raise SidecarValidationError(f"Duplicate value in entries: {val}")
        aliases.add(alias)
        values.add(val)

    # Sort entries deterministically by alias
    sorted_entries = sorted(entries, key=lambda x: x["alias"])

    return {
        "format": "cida-token-dictionary",
        "version": 1,
        "source": os.path.basename(source_name),
        "source_sha256": calculate_sha256(original_content),
        "tokenizer": "cl100k_base",
        "entries": sorted_entries
    }

def validate_sidecar_schema(data):
    if not isinstance(data, dict):
        raise SidecarValidationError("Sidecar must be a JSON object")
    
    required_keys = ["format", "version", "source", "source_sha256", "tokenizer", "entries"]
    for k in required_keys:
        if k not in data:
            raise SidecarValidationError(f"Missing required key: {k}")
            
    if data["format"] != "cida-token-dictionary":
        raise SidecarValidationError(f"Unsupported format: {data['format']}")
        
    if data["version"] != 1:
        raise SidecarValidationError(f"Unsupported version: {data['version']}")
        
    if data["tokenizer"] != "cl100k_base":
        raise SidecarValidationError(f"Unsupported tokenizer: {data['tokenizer']}")
        
    if not isinstance(data["entries"], list):
        raise SidecarValidationError("entries must be a list")
        
    aliases = set()
    values = set()
    for entry in data["entries"]:
        if not isinstance(entry, dict):
            raise SidecarValidationError("Each entry must be an object")
        alias = entry.get("alias")
        val = entry.get("value")
        if not alias or not val:
            raise SidecarValidationError("Entry missing alias or value")
        if alias in aliases:
            raise SidecarValidationError(f"Duplicate alias detected: {alias}")
        if val in values:
            raise SidecarValidationError(f"Duplicate value detected: {val}")
        aliases.add(alias)
        values.add(val)

def read_sidecar(sidecar_path):
    if not os.path.exists(sidecar_path):
        raise SidecarValidationError(f"Sidecar file not found: {sidecar_path}")
    try:
        with open(sidecar_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        raise SidecarValidationError(f"Failed to parse sidecar JSON: {e}")
        
    validate_sidecar_schema(data)
    return data

def write_sidecar(sidecar_path, data):
    validate_sidecar_schema(data)
    os.makedirs(os.path.dirname(os.path.abspath(sidecar_path)), exist_ok=True)
    with open(sidecar_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
