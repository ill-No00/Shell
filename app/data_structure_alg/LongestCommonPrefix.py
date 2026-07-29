

def get_common_prefix(s1, s2):
    for i, (char1, char2) in enumerate(zip(s1, s2)):
        if char1 != char2:
            return s1[:i]
    return s1[: min(len(s1), len(s2))]


def longest_common_prefix(arr):
    if not arr:
        return ""

    res = arr[0]
    # Start loop from index 1 and compare 'res' with each element
    for i in range(1, len(arr)):
        res = get_common_prefix(res, arr[i])

        # Optimization: If prefix becomes empty, we can stop early!
        if not res:
            break

    return res

