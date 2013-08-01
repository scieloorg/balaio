# coding: utf-8
"""
Useful functions to extract results from
scieloapi result sets.
"""
import itertools


def has_any(dataset):
    """
    Returns True or False depending on the existence of
    elements on `dataset`.

    It consumes the dataset if it is a generator.
    """
    result = bool(list(itertools.islice(dataset, 1)))

    # try to close the iterator, if it is the case
    # to avoid inconsistencies.
    try:
        dataset.close()
    except AttributeError:
        pass

    return result


def get_one(dataset):
    """
    Get the first item from `dataset`.

    It does not mess with `dataset` in case it is
    an iterator.
    """
    ds1, ds2 = itertools.tee(dataset)
    if has_any(ds1):
        return next(ds2)
    else:
        raise ValueError('dataset is empty')

