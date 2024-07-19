import json
import re
import requests

from olluigi.utils import configuration


def send_to_ollama(prompt):
    url = configuration["url"]
    payload = {
        "prompt": prompt,
        "model": "gemma2",
        "stream": False,
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def clarify_step(txt):
    task = (
        "Read the following paragraph."
        "First, evaluate its clarity with a number between 0 and 1, where 0 means it is incomprehensible and 1 that it is perfectly legible."
        "Second, suggest a way to rephrase it that is concise, clear and direct, while avoiding changing the word choices too much."
        "Provide your answer as json with the key 'clarity' and the key 'rephrasing'."
    )
    prompt = "\n".join([task, txt])
    result = send_to_ollama(prompt)
    d, e = parse_json_answer(result)
    d["original"] = txt
    d["explanation"] = e
    assert 0 <= d["clarity"] <= 1
    return d


def parse_json_answer(response):
    markdown_text = response["response"]
    json_block_pattern = re.compile(r"```json(.*?)```", re.DOTALL)
    json_block_match = json_block_pattern.search(markdown_text)

    if not json_block_match:
        raise ValueError("No JSON block found in the Markdown text")
    json_block = json_block_match.group(1).strip()
    d = json.loads(json_block)
    e = (
        markdown_text[: json_block_match.start()]
        + markdown_text[json_block_match.end() :]
    )
    return d, e
