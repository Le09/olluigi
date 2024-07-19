import os

import olluigi.chunking as chunking


import pytest


@pytest.fixture
def test_blogpost_text():
    path = os.path.join(os.path.dirname(__file__), "test_file.txt")
    with open(path, "r") as file:
        text = file.read()
    return text


def test_chunking(test_blogpost_text):
    chunks = chunking.split_text_into_chunks(test_blogpost_text, 200)
    assert len(chunks) == 8
    assert all(chunking.lenw(chunk) <= 200 for chunk in chunks)


def test_fast_split_paragraph():
    text = "This is a test sentence. This is another test sentence."

    chunks = chunking.split_text(text, 6)
    assert len(chunks) == 2
    assert chunks[0] == "This is a test sentence. "
    assert chunks[1] == "This is another test sentence."

    chunks = chunking.split_text(text, 11)
    assert chunks == [text]

    text = "One two three four five six, seven height nine. Eleven"
    chunks = chunking.split_text(text, 7)
    assert len(chunks) == 2
    assert chunks[0] == "One two three four five six,"
    assert chunks[1] == " seven height nine. Eleven"


def test_fast_chunking(test_blogpost_text):
    chunks = chunking.fast_split_text_into_chunks(test_blogpost_text)
    assert len(chunks) == 10
