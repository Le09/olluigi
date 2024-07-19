import logging
import os


logging.basicConfig(level=logging.CRITICAL)
_logger = logging.getLogger("olluigi")

configuration = {
    "model": "llama2-uncensored",
    "url": "http://localhost:11434/api/generate",
    "debug": False,
}


def base_path(file_path):
    return os.path.dirname(file_path)


def write_out(output_file, text, task=None):
    with open(output_file, "w") as file:
        if task:
            file.write(f"Task: {task}\n\n")
        file.write(text + "\n")
    print(f"Results saved to {output_file}")


def out_name(file_path, suffix="llm_answer", dir=False):
    base_name = os.path.basename(file_path)
    bn, extension = os.path.splitext(base_name)
    path = os.path.dirname(file_path)
    name = f"{bn}_{suffix}"
    result = os.path.join(path, name)
    return result if dir else result + extension


def read_file(file_path):
    with open(file_path, "r") as file:
        text = file.read()
    return text
