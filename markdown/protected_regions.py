import re

class ProtectedRegionsManager:
    """
    Manages extraction and restoration of protected regions (code, URLs, paths, variables)
    to ensure they are not altered or substituted during minification.
    """
    def __init__(self):
        self.protected_map = {}
        self.counter = 0

    def protect(self, text):
        patterns = [
            # Inline code
            r'`[^`\n]+`',
            # Link/Image destinations specifically
            r'(?<=\]\()[^)]+(?=\))',
            # URLs
            r'https?://[^\s)\]]+',
            # Placeholders: {{var}}, {var}, ${VAR}
            r'\{\{[\w.-]+\}\}',
            r'\{[\w.-]+\}',
            r'\$\{[\w_]+\}',
            # XML/HTML tags
            r'<[^>]+>',
            # BMAD critical terms (exact word match)
            r'\bstepsCompleted\b',
            r'\bworkflowType\b',
            r'\binputDocuments\b',
            r'\bnextStepFile\b',
            r'\boutputFile\b',
            r'\bbmad-create-architecture\b',
            r'\bbmad-dev-story\b',
            r'\bsteps-c/?\b',
            r'\bsteps-e/?\b',
            r'\bsteps-v/?\b',
            r'\b_bmad/?\b',
            r'\b_bmad-output/?\b',
            # File paths (relative or absolute)
            r'\b[\w.-]+/[\w.-]+(?:/[\w.-]+)*\b/?',
            r'\b[a-zA-Z]:\\[\w.-\\]*\b',
            # Terminal commands or class/method names
            r'\b[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\(\)',
        ]
        
        # Combine patterns
        combined = re.compile('|'.join(patterns))
        
        def replace_fn(match):
            val = match.group(0)
            placeholder = f"___PROTECTED_REGION_{self.counter}___"
            self.protected_map[placeholder] = val
            self.counter += 1
            return placeholder
            
        return combined.sub(replace_fn, text)

    def restore(self, text):
        current_text = text
        # Restore in reverse order to handle any potential nesting cleanly
        for placeholder, original in reversed(list(self.protected_map.items())):
            current_text = current_text.replace(placeholder, original)
        return current_text
