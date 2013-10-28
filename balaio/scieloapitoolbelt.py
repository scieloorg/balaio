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


def section_titles(dataset):
    """
    Returns sections titles from dataset
    dataset[0]['code'] = rsp-01
    dataset[0]['titles'] = [[pt, Artigos originais],
                            [es, Artículos originales],
                            [en, Original articles],
                            ]
    dataset[1]['code'] = rsp-02
    dataset[1]['titles'] = [[pt, Notícias],
                            [es, Noticias],
                            [en, News],
                            ]

    :return: [Artigos originais, Artículos originales, Original articles, ...]
    """
    valid_input = False
    if isinstance(dataset, list):
        if 'code' in dataset[0].keys() and 'titles' in dataset[0].keys():
            if isinstance(dataset[0]['titles'], list):
                if isinstance(dataset[0]['titles'][0], list):
                    if len(dataset[0]['titles'][0][0]) == 2:
                        valid_input = True
    if valid_input:
        r = []
        for section in dataset:
            # section is dict which has code and titles as key
            for lang, title in section['titles']:
                # section['titles'] = [[pt, Artigos ...], [es, Artículos], ]
                r.append(title)

    return r
