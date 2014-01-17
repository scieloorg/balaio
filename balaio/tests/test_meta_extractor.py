# coding: utf-8
import unittest
from lxml import etree
from StringIO import StringIO

from balaio import meta_extractor


class SetupPipeTest(unittest.TestCase):

    def test_if_setup_return_xml_dict(self):
        xml = None

        mta_extractor = meta_extractor.SetupPipe()
        mta_extractor.transform(xml)

        self.assertEqual(mta_extractor.transform(xml), (None, {}))


class TitlePipeTest(unittest.TestCase):

    def test_if_title_pipe_return_correct_dict(self):
        xml_str = '''
            <article>
              <article-meta>
                <title-group>
                  <article-title xml:lang="pt">Pesquisa em saude</article-title>
                  <trans-title-group xml:lang="es">
                    <trans-title>Investigacion en salud</trans-title>
                  </trans-title-group>
                </title-group>
              </article-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                "title-group": {
                    "pt": "Pesquisa em saude",
                    "es": "Investigacion en salud"
                }
              }

        mta_extractor = meta_extractor.TitlePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_if_title_pipe_treats_the_absent_of_trans_title_group(self):
        xml_str = '''
            <article>
              <article-meta>
                <title-group>
                  <article-title xml:lang="pt">Pesquisa em saude</article-title>
                </title-group>
              </article-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                "title-group": {
                    "pt": "Pesquisa em saude",
                }
              }

        mta_extractor = meta_extractor.TitlePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_if_title_pipe_treats_the_absent_of_article_title(self):
        xml_str = '''
            <article>
              <article-meta>
                <title-group>
                  <trans-title-group xml:lang="es">
                    <trans-title>Investigacion en salud</trans-title>
                  </trans-title-group>
                </title-group>
              </article-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                "title-group": {
                    "es": "Investigacion en salud"
                }
              }

        mta_extractor = meta_extractor.TitlePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)


class AbbrevJournalTitlePipeTest(unittest.TestCase):

    def test_if_abbrev_journal_title_pipe_return_correct_dict(self):
        xml_str = '''
            <article>
              <journal-meta>
                <journal-title-group>
                  <journal-title>Revista de Saúde Pública</journal-title>
                  <abbrev-journal-title abbrev-type="publisher">Rev. Saude Publica</abbrev-journal-title>
                </journal-title-group>
              </journal-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {"abbrev-journal-title": "Rev. Saude Publica"}

        mta_extractor = meta_extractor.AbbrevJournalTitlePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_abbrev_journal_title_pipe_treats_the_absent_of_abbrev_journal_title(self):
        xml_str = '''
            <article>
              <journal-meta>
                <journal-title-group>
                  <journal-title>Revista de Saúde Pública</journal-title>
                </journal-title-group>
              </journal-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {}

        mta_extractor = meta_extractor.AbbrevJournalTitlePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_abbrev_journal_title_pipe_treats_the_absent_of_journal_meta(self):
        xml_str = '''
            <article>
                <journal-title-group>
                  <journal-title>Revista de Saúde Pública</journal-title>
                  <abbrev-journal-title abbrev-type="publisher">Rev. Saude Publica</abbrev-journal-title>
                </journal-title-group>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {'abbrev-journal-title': 'Rev. Saude Publica'}

        mta_extractor = meta_extractor.AbbrevJournalTitlePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_abbrev_journal_title_pipe_treats_the_absent_of_journal_title_group(self):
        xml_str = '''
            <article>
              <journal-meta>
                  <journal-title>Revista de Saúde Pública</journal-title>
                  <abbrev-journal-title abbrev-type="publisher">Rev. Saude Publica</abbrev-journal-title>
              </journal-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {}

        mta_extractor = meta_extractor.AbbrevJournalTitlePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)


class AbstractPipePipeTest(unittest.TestCase):

    def test_if_abstract_pipe_return_correct_dict(self):
        xml_str = '''
            <article>
              <article-meta>
                <abstract xml:lang="pt">
                    Discute-se a utilizacao do conceito de ...
                </abstract>
                <trans-abstract xml:lang="es">
                    Se discute la utilizacion del concepto de ...
                </trans-abstract>
              </article-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                    "abstract": {
                        "pt": "Discute-se a utilizacao do conceito de ...",
                        "es": "Se discute la utilizacion del concepto de ..."
                    }
                }
        mta_extractor = meta_extractor.AbstractPipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_abbrev_journal_title_pipe_treats_the_absent_of_trans_abstract(self):
        xml_str = '''
            <article>
              <article-meta>
                <abstract xml:lang="pt">
                    Discute-se a utilizacao do conceito de ...
                </abstract>
              </article-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
            "abstract": {
                "pt": "Discute-se a utilizacao do conceito de ...",
            }
        }

        mta_extractor = meta_extractor.AbstractPipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_abbrev_journal_title_pipe_treats_the_absent_of_abstract(self):
        xml_str = '''
            <article>
              <article-meta>
                <trans-abstract xml:lang="es">
                    Se discute la utilizacion del concepto de ...
                </trans-abstract>
              </article-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
            "abstract": {
                "es": "Se discute la utilizacion del concepto de ...",
            }
        }

        mta_extractor = meta_extractor.AbstractPipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)


class JournalIDPipeTest(unittest.TestCase):

    def test_if_journal_id_pipe_return_correct_dict(self):
        xml_str = '''
                <article>
                  <journal-meta>
                    <journal-id journal-id-type="nlm-ta">Rev Saude Publica</journal-id>
                  </journal-meta>
                </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                    "journal-id": "Rev Saude Publica",
                   }

        mta_extractor = meta_extractor.JournalIDPipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_abbrev_journal_title_pipe_treats_the_absent_of_journal_id(self):
        xml_str = '''
                <article>
                  <journal-meta>
                  </journal-meta>
                </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {}

        mta_extractor = meta_extractor.JournalIDPipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)


class LpagePipeTest(unittest.TestCase):

    def test_if_lpage_pipe_return_correct_dict(self):
        xml_str = '''
                <article>
                  <article-meta>
                    <lpage>655</lpage>
                  </article-meta>
                </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                    "lpage": "655",
                   }

        mta_extractor = meta_extractor.LpagePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_abbrev_journal_title_pipe_treats_the_absent_of_lpage(self):
        xml_str = '''
                <article>
                  <article-meta>
                  </article-meta>
                </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {}

        mta_extractor = meta_extractor.LpagePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)


class FpagePipeTest(unittest.TestCase):

    def test_if_Fpage_pipe_return_correct_dict(self):
        xml_str = '''
                <article>
                  <article-meta>
                    <fpage>647</fpage>
                  </article-meta>
                </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                    "fpage": "647",
                   }

        mta_extractor = meta_extractor.FpagePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_abbrev_journal_title_pipe_treats_the_absent_of_fpage(self):
        xml_str = '''
                <article>
                  <article-meta>
                  </article-meta>
                </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {}

        mta_extractor = meta_extractor.FpagePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)


class JournalTitlePipeTest(unittest.TestCase):

    def test_if_jouranl_title_pipe_return_correct_dict(self):
        xml_str = '''
                <article>
                  <journal-meta>
                    <journal-title-group>
                      <journal-title>Revista de Saude Publica</journal-title>
                    </journal-title-group>
                  </journal-meta>
                </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                    "journal-title": "Revista de Saude Publica",
                   }

        mta_extractor = meta_extractor.JournalTitlePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_abbrev_journal_title_pipe_treats_the_absent_of_fpage(self):
        xml_str ='''
                <article>
                  <journal-meta>
                    <journal-title-group>
                    </journal-title-group>
                  </journal-meta>
                </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {}

        mta_extractor = meta_extractor.JournalTitlePipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)


class AuthorPipeTest(unittest.TestCase):

    def test_if_author_pipe_return_correct_dict(self):
        xml_str = '''
              <article>
                <journal-meta>
                  <contrib-group>
                    <contrib contrib-type="author">
                      <name>
                        <surname>Soysal</surname>
                        <given-names>Ahmet</given-names>
                      </name>
                      <xref ref-type="aff" rid="aff1">
                        <sup>I</sup>
                      </xref>
                    </contrib>
                    <contrib contrib-type="author">
                      <name>
                        <surname>Simsek</surname>
                        <given-names>Hatice</given-names>
                      </name>
                      <xref ref-type="aff" rid="aff1">
                        <sup>I</sup>
                      </xref>
                    </contrib>
                  </contrib-group>
                </journal-meta>
              </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                "contrib-group": {
                  "authors": [
                    {
                      "given-names": "Ahmet",
                      "surname": "Soysal",
                      "affiliations": [
                        "aff1"
                      ]
                    },
                    {
                      "given-names": "Hatice",
                      "surname": "Simsek",
                      "affiliations": [
                        "aff1"
                      ]
                    }]
                  }
                }

        mta_extractor = meta_extractor.AuthorPipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_if_author_title_pipe_treats_the_absent_of_contrib(self):
        xml_str = '''
              <article>
                <journal-meta>
                  <contrib-group>
                      <name>
                        <surname>Soysal</surname>
                        <given-names>Ahmet</given-names>
                      </name>
                      <xref ref-type="aff" rid="aff1">
                        <sup>I</sup>
                      </xref>
                    <contrib contrib-type="author">
                      <name>
                        <surname>Simsek</surname>
                        <given-names>Hatice</given-names>
                      </name>
                      <xref ref-type="aff" rid="aff1">
                        <sup>I</sup>
                      </xref>
                    </contrib>
                  </contrib-group>
                </journal-meta>
              </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                "contrib-group": {
                  "authors": [
                    {
                      "given-names": "Hatice",
                      "surname": "Simsek",
                      "affiliations": [
                        "aff1"
                      ]
                    }]
                  }
                }

        mta_extractor = meta_extractor.AuthorPipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    def test_if_author_title_pipe_treats_the_absent_of_any_ref(self):
        xml_str = '''
            <article>
                <journal-meta>
                  <contrib-group>
                    <contrib contrib-type="author">
                      <name>
                        <surname>Soysal</surname>
                        <given-names>Ahmet</given-names>
                      </name>
                    </contrib>
                    <contrib contrib-type="author">
                      <name>
                        <surname>Simsek</surname>
                        <given-names>Hatice</given-names>
                      </name>
                      <xref ref-type="aff" rid="aff1">
                        <sup>I</sup>
                      </xref>
                    </contrib>
                  </contrib-group>
                </journal-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
                "contrib-group": {
                  "authors": [
                    {
                      "given-names": "Ahmet",
                      "surname": "Soysal",
                      "affiliations": []
                    },
                    {
                      "given-names": "Hatice",
                      "surname": "Simsek",
                      "affiliations": [
                        "aff1"
                      ]
                    }]
                  }
                }

        mta_extractor = meta_extractor.AuthorPipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

class AffiliationPipeTest(unittest.TestCase):

    def test_if_affiliation_pipe_return_correct_dict(self):
        xml_str = '''
            <article>
                <article-meta>
                <aff id="aff1">
                    <institution content-type="orgname">Santa Casa de Sao Paulo</institution>
                    <addr-line>
                    <named-content content-type="city">Sao Paulo</named-content>
                    <named-content content-type="state">SP</named-content>
                    </addr-line>
                    <country>Brasil</country>
                </aff>
                <aff id="aff2">
                    <institution content-type="orgname">Universidade de Sao Paulo</institution>
                    <addr-line>
                    <named-content content-type="city">Sao Paulo</named-content>
                    <named-content content-type="state">SP</named-content>
                    </addr-line>
                    <country>Brasil</country>
                </aff>
                </article-meta>
            </article>'''

        xml = etree.parse(StringIO(xml_str))

        expected = {
              "affiliations": [
                {
                  "ref": "aff1",
                  "institution": "Santa Casa de Sao Paulo",
                  "country": "Brasil"
                },
                {
                  "ref": "aff2",
                  "institution": "Universidade de Sao Paulo",
                  "country": "Brasil"
                },
              ],
            }

        mta_extractor = meta_extractor.AffiliationPipe()
        xml, dict_data = mta_extractor.transform([xml, {}])

        self.assertEqual(dict_data, expected)

    # def test_if_author_title_pipe_treats_the_absent_of_contrib(self):
    #     xml_str = '''
    #           <article>
    #             <journal-meta>
    #               <contrib-group>
    #                   <name>
    #                     <surname>Soysal</surname>
    #                     <given-names>Ahmet</given-names>
    #                   </name>
    #                   <xref ref-type="aff" rid="aff1">
    #                     <sup>I</sup>
    #                   </xref>
    #                 <contrib contrib-type="author">
    #                   <name>
    #                     <surname>Simsek</surname>
    #                     <given-names>Hatice</given-names>
    #                   </name>
    #                   <xref ref-type="aff" rid="aff1">
    #                     <sup>I</sup>
    #                   </xref>
    #                 </contrib>
    #               </contrib-group>
    #             </journal-meta>
    #           </article>'''

    #     xml = etree.parse(StringIO(xml_str))

    #     expected = {
    #             "contrib-group": {
    #               "authors": [
    #                 {
    #                   "given-names": "Hatice",
    #                   "surname": "Simsek",
    #                   "affiliations": [
    #                     "aff1"
    #                   ]
    #                 }]
    #               }
    #             }

    #     mta_extractor = meta_extractor.AuthorPipe()
    #     xml, dict_data = mta_extractor.transform([xml, {}])

    #     self.assertEqual(dict_data, expected)

    # def test_if_author_title_pipe_treats_the_absent_of_any_ref(self):
    #     xml_str = '''
    #         <article>
    #             <journal-meta>
    #               <contrib-group>
    #                 <contrib contrib-type="author">
    #                   <name>
    #                     <surname>Soysal</surname>
    #                     <given-names>Ahmet</given-names>
    #                   </name>
    #                 </contrib>
    #                 <contrib contrib-type="author">
    #                   <name>
    #                     <surname>Simsek</surname>
    #                     <given-names>Hatice</given-names>
    #                   </name>
    #                   <xref ref-type="aff" rid="aff1">
    #                     <sup>I</sup>
    #                   </xref>
    #                 </contrib>
    #               </contrib-group>
    #             </journal-meta>
    #         </article>'''

    #     xml = etree.parse(StringIO(xml_str))

    #     expected = {
    #             "contrib-group": {
    #               "authors": [
    #                 {
    #                   "given-names": "Ahmet",
    #                   "surname": "Soysal",
    #                   "affiliations": []
    #                 },
    #                 {
    #                   "given-names": "Hatice",
    #                   "surname": "Simsek",
    #                   "affiliations": [
    #                     "aff1"
    #                   ]
    #                 }]
    #               }
    #             }

    #     mta_extractor = meta_extractor.AuthorPipe()
    #     xml, dict_data = mta_extractor.transform([xml, {}])

    #     self.assertEqual(dict_data, expected)







