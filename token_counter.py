import sys
import os
import tiktoken

# Force using the offline cache in resources
dir_path = os.path.dirname(os.path.abspath(__file__))
os.environ["TIKTOKEN_CACHE_DIR"] = os.path.join(dir_path, "resources")

def count_tokens(text):
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return 0

if __name__ == "__main__":
    text = sys.stdin.read()
    print(count_tokens(text))
