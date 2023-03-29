from collections.abc import MutableMapping


def recursiveMerge(d1, d2):
    """
    Update two dicts of dicts recursively,
    if either mapping has leaves that are non-dicts,
    the second's leaf overwrites the first's.
    """
    for k, v in d1.items():
        if k in d2:
            if all(isinstance(e, MutableMapping) for e in (v, d2[k])):
                d2[k] = recursiveMerge(v, d2[k])
            # we could further check types and merge as appropriate here.
            elif isinstance(v, list):
                # merge/append lists
                if isinstance(d2[k], list):
                    # merge lists
                    v.extend(d2[k])
                else:
                    # append to list
                    v.append(d2[k])
    d3 = d1.copy()
    d3.update(d2)
    return d3
