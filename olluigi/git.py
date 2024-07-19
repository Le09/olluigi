from olluigi import utils
import git
import re


def is_git_repo_clean(folder_path):
    try:
        repo = git.Repo(folder_path)
    except git.exc.InvalidGitRepositoryError:
        raise Exception(f"The path {folder_path} is not a git repository.")
    if repo.is_dirty():
        raise Exception(f"The working tree at {folder_path} is not clean.")


def switch_branch(folder_path, suffix):
    repo = git.Repo(folder_path)
    current_name = repo.active_branch.name
    new_name = f"{current_name}_{suffix}"
    if new_name in repo.heads:
        raise Exception(f"The branch {new_name} already exists.")
    new_branch = repo.create_head(new_name)
    repo.head.reference = new_branch
    repo.head.reset(index=True, working_tree=True)


def whitespace_tolerant_replace(text, to_replace, new_text):
    # So we have the problem with chunkipy that it does not respect the whitespace
    escaped_phrases = [re.escape(r) for r in to_replace.split()]
    pattern = re.compile(r"\s+".join(escaped_phrases), re.IGNORECASE)
    return pattern.sub(new_text, text, count=1)


def commit_change(file, to_replace, new_text, message):
    text = utils.read_file(file)
    text = whitespace_tolerant_replace(text, to_replace, new_text)
    if new_text not in text:
        raise Exception(f"Failed to apply the change to {file}.")
    utils.write_out(file, text)

    folder_path = utils.base_path(file)

    repo = git.Repo(folder_path)
    repo.git.add(update=True)
    repo.git.commit(message=message)
