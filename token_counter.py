import sys
import tiktoken

def count_tokens(text):
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return 0

if __name__ == "__main__":
    
    text = sys.stdin.read()
    print(count_tokens(text))
