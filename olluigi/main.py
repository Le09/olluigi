#!/usr/bin/env python3

import luigi
import sys

from configargparse import ArgumentParser

from . import git
from . import utils
from . import pipelines


def main_arguments_parser():
    parser = ArgumentParser(
        description="Olluigi", default_config_files=["./.olluigi.rc", "~/.olluigi.rc"]
    )
    parser.add_argument("input_file")
    parser.add("-c", "--config", is_config_file=True, help="config file path")

    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        nargs="?",
        default="",
        help="Prompt to execute. If not set, will use the clarify command.",
    )
    parser.add_argument(
        "--url",
        "-u",
        type=str,
        nargs="?",
        help="LLM url.",
        default="http://localhost:11434/api/generate",
    )
    parser.add_argument(
        "--model", "-m", type=str, nargs="?", help="LLM model.", default="gemma2"
    )
    parser.add_argument(
        "--name", "-n", type=str, nargs="?", help="Prompt name.", default="prompt"
    )
    parser.add_argument(
        "--git",
        "-g",
        action="store_true",
        help="Whether to commit the results to git when used with clarify.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Do not call LLM. LLM is slow.",
    )

    return parser


def main():
    if len(sys.argv) == 1:
        main_arguments_parser().print_help(sys.stderr)
        sys.exit(1)

    args = main_arguments_parser().parse_args()
    config_arguments = ["url", "model", "debug"]
    for arg in config_arguments:
        utils.configuration[arg] = args.__dict__[arg]
    if args.prompt:
        p = [
            pipelines.Prompt(
                input_file=args.input_file, prompt=args.prompt, name=args.name
            )
        ]
    else:
        if args.git:
            folder_path = utils.base_path(args.input_file)
            git.is_git_repo_clean(folder_path)
        p = [pipelines.Clarify(input_file=args.input_file, git=args.git)]
    luigi.build(p)


if __name__ == "__main__":
    main()
