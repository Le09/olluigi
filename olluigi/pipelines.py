import luigi
import os
import json
import olluigi.ollama as oll
from olluigi import utils, chunking, git

from olluigi.utils import configuration


class SplitTextTask(luigi.Task):
    input_file = luigi.Parameter()
    chunk_size = luigi.IntParameter(default=200)
    output_dir = luigi.Parameter(default="chunks")
    git = luigi.BoolParameter(default=False)

    def output(self):
        output_file = os.path.join(self.output_dir, "split.txt")
        return luigi.LocalTarget(output_file)

    def run(self):
        if self.git:
            path = utils.base_path(self.input_file)
            filename = os.path.basename(self.input_file)
            git.switch_branch(path, filename + "_clarify")

        os.makedirs(self.output_dir, exist_ok=True)
        text = utils.read_file(self.input_file)

        chunks = chunking.split_text_into_chunks(text, max_chunk_size=self.chunk_size)

        for i, chunk in enumerate(chunks):
            with open(
                os.path.join(self.output_dir, f"chunk_{i}.txt"), "w"
            ) as chunk_file:
                chunk_file.write(chunk)
        utils.write_out(self.output().path, "\n")


class ProcessChunkTaskClarify(luigi.Task):
    resources = {"ollama": 1}
    chunk_file = luigi.Parameter()
    output_dir = luigi.Parameter(default="processed_chunks")
    git = luigi.BoolParameter(default=False)
    input_file = luigi.Parameter()

    def output(self):
        output_file = os.path.join(self.output_dir, os.path.basename(self.chunk_file))
        return luigi.LocalTarget(output_file)

    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        chunk = utils.read_file(self.chunk_file)

        if not configuration["debug"]:
            processed_chunk = oll.clarify_step(chunk)
        else:
            processed_chunk = {
                "clarity": 0.5,
                "rephrasing": "This is a rephrased paragraph.",
                "explanation": "This is an explanation.",
                "original": chunk,
            }
        processed_chunk_as_json = json.dumps(processed_chunk)

        if self.git:
            message = os.path.basename(self.chunk_file)
            git.commit_change(
                self.input_file,
                to_replace=processed_chunk["original"],
                new_text=processed_chunk["rephrasing"],
                message=message,
            )

        with self.output().open("w") as out_file:
            out_file.write(processed_chunk_as_json)


class ProcessChunkTaskPrompt(luigi.Task):
    resources = {"ollama": 1}
    chunk_file = luigi.Parameter()
    prompt = luigi.Parameter()
    output_dir = luigi.Parameter(default="processed_chunks")

    def output(self):
        output_file = os.path.join(self.output_dir, os.path.basename(self.chunk_file))
        return luigi.LocalTarget(output_file)

    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        chunk = utils.read_file(self.chunk_file)

        prompt = "\n".join([self.prompt, chunk])
        if not configuration["debug"]:
            result = oll.send_to_ollama(prompt)["response"]
        else:
            result = prompt

        with self.output().open("w") as out_file:
            out_file.write(result)


class AggregateTaskToFileByClarity(luigi.Task):
    chunk_dir = luigi.Parameter()
    processed_chunks = luigi.ListParameter()
    output_file = luigi.Parameter()
    git = luigi.BoolParameter(default=False)
    input_file = luigi.Parameter()

    def requires(self):
        chunk_files = [
            os.path.join(self.chunk_dir, f)
            for f in os.listdir(self.chunk_dir)
            if f.startswith("chunk_")
        ]
        return [
            ProcessChunkTaskClarify(
                chunk_file=chunk_file,
                output_dir=self.processed_chunks,
                git=self.git,
                input_file=self.input_file,
            )
            for chunk_file in chunk_files
        ]

    def output(self):
        return luigi.LocalTarget(self.output_file)

    def run(self):
        results = []
        for input_task in self.input():
            with input_task.open("r") as in_file:
                processed_chunk = json.loads(in_file.read())
                results.append(processed_chunk)
        results.sort(key=lambda x: x["clarity"])

        content = ""
        for result in results:
            content += f"Clarity: {result['clarity']}\n"
            content += f"Rephrased Paragraph:\n{result['rephrasing']}\n\n"
            content += f"Explanation:\n{result['explanation']}\n\n"
            content += f"Original Paragraph:\n{result['original']}\n\n"

        with self.output().open("w") as out_file:
            out_file.write(content)


class AggregateTaskToFile(luigi.Task):
    chunk_dir = luigi.Parameter()
    processed_chunks = luigi.ListParameter()
    output_file = luigi.Parameter()
    process_task = luigi.Parameter(default=ProcessChunkTaskPrompt)
    prompt = luigi.Parameter()

    def requires(self):
        chunk_files = [
            os.path.join(self.chunk_dir, f)
            for f in os.listdir(self.chunk_dir)
            if f.startswith("chunk_")
        ]
        return [
            self.process_task(
                chunk_file=chunk_file,
                output_dir=self.processed_chunks,
                prompt=self.prompt,
            )
            for chunk_file in chunk_files
        ]

    def output(self):
        return luigi.LocalTarget(self.output_file)

    def run(self):
        results = []
        for input_task in self.input():
            with input_task.open("r") as in_file:
                results.append(in_file.read())
        content = "\n".join(results)
        with self.output().open("w") as out_file:
            out_file.write(content)


class Clarify(luigi.WrapperTask):
    input_file = luigi.Parameter()
    chunk_size = luigi.IntParameter(default=200)
    git = luigi.BoolParameter(default=False)

    def requires(self):
        out_name = utils.out_name(self.input_file, "clarify")
        chunk_dir = utils.out_name(self.input_file, "chunks", dir=True)
        processed_chunks_dir = chunk_dir + "_processed"
        split_task = SplitTextTask(
            input_file=self.input_file,
            chunk_size=self.chunk_size,
            output_dir=chunk_dir,
            git=self.git,
        )
        yield split_task
        yield [
            AggregateTaskToFileByClarity(
                chunk_dir=chunk_dir,
                output_file=out_name,
                processed_chunks=processed_chunks_dir,
                git=self.git,
                input_file=self.input_file,
            )
        ]


class Prompt(luigi.WrapperTask):
    input_file = luigi.Parameter()
    chunk_size = luigi.IntParameter(default=200)
    prompt = luigi.Parameter()
    name = luigi.Parameter(default="prompt")

    def requires(self):
        out_name = utils.out_name(self.input_file, self.name)
        chunk_dir = utils.out_name(self.input_file, "chunks_" + self.name, dir=True)
        processed_chunks_dir = chunk_dir + "_processed"
        split_task = SplitTextTask(
            input_file=self.input_file,
            chunk_size=self.chunk_size,
            output_dir=chunk_dir,
        )
        yield split_task
        yield [
            AggregateTaskToFile(
                chunk_dir=chunk_dir,
                output_file=out_name,
                processed_chunks=processed_chunks_dir,
                prompt=self.prompt,
            )
        ]
