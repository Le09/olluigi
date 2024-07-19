# Olluigi

This is a small duct-tape repository providing a CLI to automate some LLM tasks.
Currently, the following tasks are implemented:
- `prompt` that ask the LLM to run an arbitrary prompt on each paragraph of the document, and aggregates all results in a text file.
- `clarify` ask the LLM to clarify each paragraph of a document. The output can be a simple text file with each paragraph ordered by the LLM evaluation of how much clarification is needed. It is also possible to have each paragraph directly git committed, allowing for the review of each change.

This is not a turn-key solution, as it assumes the following daemons are running:
- [Luigi](https://luigi.readthedocs.io/en/stable/) to manage the tasks
- [Ollama](https://github.com/ollama/ollama/) to run the LLM. 

Python and Luigi are hard requirements, but Ollama is not really one. 
It could be possible to use any other LLM provider by simply modifying the `send_to_ollama` function.

## Limitations

This was meant to be a simple script, but a number of difficulties made it necessary to make a more complicated solution. 
Besides implementing more features, this is meant to stay very small and simple.

## What problem does this solve?

Running the LLM on a document is costly, in time and/or money.
Moreover, the results are not deterministic and thus may fail to provide a valid answer.
These problems make it necessary to store intermediary results, and run an aggregate task once all its dependencies are finally done. 
In other words, a pipeline/workflow manager is needed.

My first run of the clarify task on one full document took 24 minutes, only to fail because the LLM processing of one paragraph failed.

Most of the other tasks that should be run, like chunking text or commiting to git, have many pitfalls to avoid.

Here is an example of what a Luigi pipeline looks like: 
https://raw.githubusercontent.com/spotify/luigi/master/doc/user_recs.png

## Installation

This is a standard Python package, so you can install it with pip
(or preferably [pipx](https://pipx.pypa.io/stable/)):

```bash
pip install .
```

Refer to Luigi and Ollama respective documentation pages for installation instructions.

## Usage

Simply run `olluigi` to get the help message giving all possible arguments.
The main usage is:
```bash
olluigi path/to/document.txt
```
To ask the LLM to clarify, or rephrase, each paragraph of the document.
Which will create a new document `document.txt` with all the results.

If given the `--git` flag, it will commit each paragraph change to a new branch.
It expects the document to belong to a git repository (it could be created automatically though).

Other tasks can be run with this syntax:
```bash
olluigi path/to/document.txt --prompt "Summarize this in a short sentence." --name "summary" --model "gemma2" 
```


## Configuration

Everything can be passed as argument to the command line. 
It is also possible to create a configuration file `.olluigi.rc` to avoid repeating the same arguments, if for example you might always use the same model name (which defaults to `llama2-uncensored`). 

## Related projects

Not sure really. Was this already covered by some other project?
