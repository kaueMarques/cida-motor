import re

class Block:
    def __init__(self, block_type, content, metadata=None):
        self.type = block_type
        self.content = content
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Block(type={self.type}, content_len={len(self.content)})"

def parse_markdown(text):
    """
    Splits the markdown text into block objects deterministically.
    """
    lines = text.splitlines(keepends=True)
    blocks = []
    
    in_frontmatter = False
    frontmatter_lines = []
    
    in_code_block = False
    code_block_lines = []
    code_block_lang = ""
    
    # Check if frontmatter exists at the start
    has_frontmatter = False
    if lines and lines[0].strip() == "---":
        has_frontmatter = True
        
    line_idx = 0
    while line_idx < len(lines):
        line = lines[line_idx]
        stripped = line.strip()
        
        # 1. Frontmatter handling
        if has_frontmatter and line_idx == 0:
            in_frontmatter = True
            frontmatter_lines.append(line)
            line_idx += 1
            continue
            
        if in_frontmatter:
            frontmatter_lines.append(line)
            if stripped == "---":
                in_frontmatter = False
                blocks.append(Block("frontmatter", "".join(frontmatter_lines)))
                frontmatter_lines = []
            line_idx += 1
            continue
            
        # 2. Fenced Code Block handling
        if stripped.startswith("```"):
            if in_code_block:
                code_block_lines.append(line)
                blocks.append(Block("code_block", "".join(code_block_lines), {"lang": code_block_lang}))
                code_block_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_block_lang = stripped[3:].strip()
                code_block_lines.append(line)
            line_idx += 1
            continue
            
        if in_code_block:
            code_block_lines.append(line)
            line_idx += 1
            continue
            
        # Flush any current generic blocks if we hit a new block-starting marker
        is_header = stripped.startswith("#") and re.match(r'^#{1,6}\s+', stripped) is not None
        is_table = stripped.startswith("|") or (stripped.endswith("|") and "|" in stripped)
        is_list = re.match(r'^(\s*)([-*+]|\d+\.)\s+', line) is not None
        is_comment_start = stripped.startswith("<!--")
        
        if is_comment_start:
            if "-->" in stripped:
                blocks.append(Block("comment", line))
                line_idx += 1
                continue
            else:
                comment_lines = [line]
                line_idx += 1
                while line_idx < len(lines):
                    comment_line = lines[line_idx]
                    comment_lines.append(comment_line)
                    if "-->" in comment_line:
                        break
                    line_idx += 1
                blocks.append(Block("comment", "".join(comment_lines)))
                line_idx += 1
                continue

        if is_header:
            blocks.append(Block("header", line))
            line_idx += 1
            continue

        is_blockquote = stripped.startswith(">")

        if is_table:
            table_lines = [line]
            line_idx += 1
            while line_idx < len(lines):
                next_line = lines[line_idx]
                next_stripped = next_line.strip()
                if next_stripped.startswith("|") or (next_stripped.endswith("|") and "|" in next_stripped):
                    table_lines.append(next_line)
                    line_idx += 1
                else:
                    break
            blocks.append(Block("table", "".join(table_lines)))
            continue

        if is_list:
            list_lines = [line]
            line_idx += 1
            while line_idx < len(lines):
                next_line = lines[line_idx]
                next_stripped = next_line.strip()
                if not next_stripped:
                    # check next line after empty line
                    if line_idx + 1 < len(lines):
                        after_next = lines[line_idx + 1]
                        if re.match(r'^(\s*)([-*+]|\d+\.)\s+', after_next):
                            list_lines.append(next_line)
                            line_idx += 1
                            continue
                    break
                
                if re.match(r'^(\s*)([-*+]|\d+\.)\s+', next_line) or next_line.startswith(" ") or next_line.startswith("\t"):
                    list_lines.append(next_line)
                    line_idx += 1
                else:
                    break
            blocks.append(Block("list", "".join(list_lines)))
            continue

        if is_blockquote:
            bq_lines = [line]
            line_idx += 1
            while line_idx < len(lines):
                next_line = lines[line_idx]
                next_stripped = next_line.strip()
                if next_stripped.startswith(">"):
                    bq_lines.append(next_line)
                    line_idx += 1
                else:
                    break
            blocks.append(Block("blockquote", "".join(bq_lines)))
            continue

        is_hr = re.match(r'^[-*_]{3,}\s*$', stripped) is not None
        if is_hr:
            blocks.append(Block("hr", line))
            line_idx += 1
            continue

        if not stripped:
            blocks.append(Block("blank", line))
            line_idx += 1
            continue

        para_lines = [line]
        line_idx += 1
        while line_idx < len(lines):
            next_line = lines[line_idx]
            next_stripped = next_line.strip()
            if (not next_stripped or
                next_stripped.startswith("#") or
                next_stripped.startswith("```") or
                next_stripped.startswith("<!--") or
                next_stripped.startswith("|") or
                re.match(r'^(\s*)([-*+]|\d+\.)\s+', next_line) or
                next_stripped.startswith(">") or
                re.match(r'^[-*_]{3,}\s*$', next_stripped)):
                break
            para_lines.append(next_line)
            line_idx += 1
        blocks.append(Block("paragraph", "".join(para_lines)))
        
    return blocks
