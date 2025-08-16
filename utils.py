from typing import List

def split_message(text: str, max_length: int = 4000) -> List[str]:
    """
    Split a long text into chunks, each at most max_length characters,
    trying to split at line boundaries (newline characters).
    If a single line exceeds max_length, it will be split mid-line.
    """
    lines = text.split('\n')
    chunks = []
    current_chunk = ""

    for line in lines:
        # If line itself is longer than max_length, split the line directly
        if len(line) > max_length:
            # flush current chunk first
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            # split long line into smaller parts
            for i in range(0, len(line), max_length):
                chunks.append(line[i:i+max_length])
        else:
            # check if adding this line would exceed max_length
            if current_chunk:
                # +1 for newline
                if len(current_chunk) + 1 + len(line) > max_length:
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += "\n" + line
            else:
                current_chunk = line

    # Add last chunk if exists
    if current_chunk:
        chunks.append(current_chunk)

    return chunks
