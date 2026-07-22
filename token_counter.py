import sys
import os

# Ensure project root is in path to import markdown module
dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, dir_path)

from markdown.phrase_dictionary import get_encoder

if __name__ == "__main__":
    try:
        enc = get_encoder()
        text = sys.stdin.read()
        print(len(enc.encode(text)))
    except Exception as e:
        print(f"Error in token_counter: {e}", file=sys.stderr)
        sys.exit(2)
