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
    """
    return bool(list(itertools.islice(dataset, 1)))

