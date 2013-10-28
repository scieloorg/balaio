# coding: utf-8
import mocker
import unittest

from balaio import scieloapitoolbelt


class SimplifyIssueSectionsTests(unittest.TestCase):

    def test_section_titles(self):
        """
        Symplify the result of scieloapi query like that dataset['sections']

        dataset['sections'][0]['code'] = rsp-01
        dataset['sections'][0]['titles'] = [[pt, Artigos originais],
                                [es, Artículos originales],
                                [en, Original articles],
                                ]
        dataset['sections'][1]['code'] = rsp-02
        dataset['sections'][1]['titles'] = [[pt, Notícias],
                                [es, Noticias],
                                [en, News],
                                ]

        :return: [Artigos originais, Artículos originales, Original articles, ...]
        """
        dataset = {'sections': [
                        {u'code': u'BWHO-hm3b', u'titles': [[u'en', u'News'], [u'es', u'Noticias'], [u'pt', u'Notícias']]},
                        {u'code': u'BWHO-prtj', u'titles': [[u'en', u'Police & Practice']]},
                        {u'code': u'BWHO-r9vg', u'titles': [[u'en', u'Research']]},
                     ]
            }
        self.assertEqual(scieloapitoolbelt.section_titles(dataset['sections']),
                [u'News', u'Noticias', u'Notícias', u'Police & Practice', u'Research']
            )
