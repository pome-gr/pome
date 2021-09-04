import os
import pathlib
from glob import glob


def get_longest_matching_prefix(word, prefix_list):
    """Find the longest prefix of word that is in prefix_list. None otherwise."""
    to_return = None
    for i in range(len(word)):
        prefix = word[: i + 1]
        if prefix in prefix_list:
            to_return = prefix
    return to_return


def get_recursive_json_hash():
    """Gives compound hash of all json stats in repository."""
    the_hash = None
    for dirpath, dirnames, filenames in os.walk("."):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for filetype in ["*.json", "*.csv"]:
            for filename in glob(os.path.join(dirpath, filetype)):
                if os.path.exists(filename):
                    if the_hash is None:
                        the_hash = hash(pathlib.Path(filename).stat())
                    else:
                        the_hash = hash((the_hash, hash(pathlib.Path(filename).stat())))

    return the_hash
