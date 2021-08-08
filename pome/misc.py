def get_longest_matching_prefix(word, prefix_list):
    """Find the longest prefix of word that is in prefix_list. None otherwise."""
    to_return = None
    for i in range(len(word)):
        prefix = word[: i + 1]
        if prefix in prefix_list:
            to_return = prefix
    return to_return
