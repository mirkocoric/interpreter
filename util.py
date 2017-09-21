def list_repr(lst):
    return ' '.join(list_item_repr(el) for el in lst)


def list_item_repr(lst):
    return (str(lst) if not isinstance(lst, list) else
            '[' + ' '.join(list_item_repr(el) for el in lst) + ']')
