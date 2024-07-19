import re
import chunkipy


def lenw(s):
    """Word count (simple version)."""
    return len(s.split())


def split_text(text, max_chunk_size=200):
    max_chunk_size *= 5  # average word length
    chunks = []
    re_primary = r".*(!|\.|\?)\s"
    re_secondary = r".*(\\n|:|;|,)"
    re_space = r".*\s"
    while len(text) > max_chunk_size:
        chunk_sized = text[:max_chunk_size]
        match = re.search(re_primary, chunk_sized)
        if not match:
            match = re.search(re_secondary, chunk_sized)
        if not match:
            match = re.search(re_space, chunk_sized)
        split_point = match.end() if match else max_chunk_size
        chunks.append(text[:split_point])
        text = text[split_point:]
    chunks.append(text)
    return chunks


def fast_split_text_into_chunks(text, max_chunk_size=200):
    """
    Split text into chunks of size less than max_chunk_size.
    Minimize the number of chunks and avoid breaking paragraphs if possible.
    """
    paragraphs = text.split("\n\n")

    chunks = []
    current_chunk = []
    current_chunk_size = 0

    for paragraph in paragraphs:
        paragraph_size = lenw(paragraph)
        # Check if adding this paragraph would exceed the max_chunk_size
        if current_chunk_size + paragraph_size <= max_chunk_size:
            current_chunk.append(paragraph)
            current_chunk_size += paragraph_size
        else:  # Save the current chunk and start a new one
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            if paragraph_size > max_chunk_size:
                chunks += split_text(paragraph, max_chunk_size)
                current_chunk = []
                current_chunk_size = 0
            else:
                current_chunk = [paragraph]
                current_chunk_size = paragraph_size

    if current_chunk:  # Add the last chunk if it exists
        chunks.append("\n\n".join(current_chunk))

    return chunks


def split_text_into_chunks(text, max_chunk_size=200):
    text_chunker = chunkipy.TextChunker(max_chunk_size, tokens=True)
    return text_chunker.chunk(text)
