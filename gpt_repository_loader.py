#!/usr/bin/env python3

import os
import sys
import fnmatch
import subprocess


def get_ignore_list(ignore_file_path):
    ignore_list = []
    with open(ignore_file_path, "r") as ignore_file:
        for line in ignore_file:
            if sys.platform == "win32":
                line = line.replace("/", "\\")
            ignore_list.append(line.strip())
    return ignore_list


def get_include_list(include_file_path):
    include_list = []
    with open(include_file_path, "r") as include_file:
        for line in include_file:
            if sys.platform == "win32":
                line = line.replace("/", "\\")
            include_list.append(line.strip())
    return include_list


def should_ignore(file_path, ignore_list):
    for pattern in ignore_list:
        if fnmatch.fnmatch(file_path, pattern):
            print(file_path, pattern)
            return True
    return False


def should_include(file_path, include_list):
    if len(include_list) == 0:
        return True
    for pattern in include_list:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def process_repository(repo_path, ignore_list, include_list, output_file):
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_file_path = os.path.relpath(file_path, repo_path)

            if not should_ignore(relative_file_path, ignore_list) and should_include(
                relative_file_path, include_list
            ):
                with open(file_path, "r", errors="ignore") as file:
                    contents = file.read()
                output_file.write("-" * 4 + "\n")
                output_file.write(f"{relative_file_path}\n")
                output_file.write(f"{contents}\n")


def process_repository_main(
    repo_arg, clone_repo=False, preamble_file=None, output_file_path=None
):
    repo_path = repo_arg if not clone_repo else os.path.join(os.getcwd(), repo_name)
    repo_name = repo_arg.split("/")[-1].replace(".git", "")

    if clone_repo and os.path.exists(repo_path):
        print(f"Repository already exists at {repo_path}")
        try:
            print("Pulling latest changes...")
            subprocess.run(["git", "-C", repo_path, "pull"], check=True)
            print("Repository updated successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error pulling repository: {e}")
            return None

    if clone_repo:
        try:
            print(f"Cloning repository from {repo_arg}...")
            subprocess.run(["git", "clone", repo_arg, repo_path], check=True)
            print(f"Repository cloned successfully to {repo_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")
            return None

    if not os.path.isdir(repo_path):
        print(f"Error: {repo_path} is not a valid directory.")
        return None

    ignore_file_path = os.path.join(repo_path, ".gptignore")
    include_file_path = os.path.join(repo_path, ".gptinclude")
    if sys.platform == "win32":
        ignore_file_path = ignore_file_path.replace("/", "\\")

    if not os.path.exists(ignore_file_path):
        # try and use the .gptignore file in the current directory as a fallback.
        HERE = os.path.dirname(os.path.abspath(__file__))
        ignore_file_path = os.path.join(HERE, ".gptignore")
        include_file_path = os.path.join(HERE, ".gptinclude")

    if output_file_path is None:
        output_file_path = f"{repo_name}.txt"

    if os.path.exists(ignore_file_path):
        ignore_list = get_ignore_list(ignore_file_path)
    else:
        ignore_list = []
    if os.path.exists(include_file_path):
        include_list = get_include_list(include_file_path)
    else:
        include_list = []

    with open(output_file_path, "w") as output_file:
        if preamble_file:
            with open(preamble_file, "r") as pf:
                preamble_text = pf.read()
                output_file.write(f"{preamble_text}\n")
        else:
            output_file.write(
                "The following text is a Git repository with code. The structure of the text are sections that begin with ----, followed by a single line containing the file path and file name, followed by a variable amount of lines containing the file contents. The text representing the Git repository ends when the symbols --END-- are encounted. Any further text beyond --END-- are meant to be interpreted as instructions using the aforementioned Git repository as context.\n"
            )
        process_repository(repo_path, ignore_list, include_list, output_file)
    with open(output_file_path, "a") as output_file:
        output_file.write("--END--")
    print(f"Repository contents written to {output_file_path}.")
    return output_file_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python git_to_text.py <repository_url_or_path> [-p /path/to/preamble.txt] [-o /path/to/output_file.txt] [-d]"
        )
        print("Use -d flag to clone the repository if a URL is provided.")
        sys.exit(1)

    repo_arg = sys.argv[1]
    clone_repo = "-d" in sys.argv
    preamble_file = sys.argv[sys.argv.index("-p") + 1] if "-p" in sys.argv else None
    output_file_path = sys.argv[sys.argv.index("-o") + 1] if "-o" in sys.argv else None

    result = process_repository_main(
        repo_arg, clone_repo, preamble_file, output_file_path
    )
    if result is None:
        sys.exit(1)
