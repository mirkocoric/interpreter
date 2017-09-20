def print_list(lst):
    return ' '.join(list_repr(el) for el in lst)


def list_repr(lst):
    return (str(lst) if not isinstance(lst, list) else
            '[' + ' '.join(list_repr(el) for el in lst) + ']')
