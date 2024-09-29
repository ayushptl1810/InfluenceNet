def strtobool(val):
    """
    Convert a string representation of truth to True or False.

    True values are 'y', 'yes', 't', 'true', 'on', and '1'.
    False values are 'n', 'no', 'f', 'false', 'off', and '0'.
    Raises ValueError if 'val' is anything else.
    """
    val_lower = val.lower()
    true_set = {'y', 'yes', 't', 'true', 'on', '1'}
    false_set = {'n', 'no', 'f', 'false', 'off', '0'}

    if val_lower in true_set:
        return True
    elif val_lower in false_set:
        return False
    else:
        raise ValueError(f"Invalid truth value: {val!r}")
