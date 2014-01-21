# coding: utf-8

import json
from lxml import etree

import plumber

class SetupPipe(plumber.Pipe):

    def transform(self, xml):
        return (xml, {})


class TitlePipe(plumber.Pipe):

    def transform(self, item):
        titles = {}
        xml, dict_data = item
        title_group = xml.find('.//title-group')

        if title_group.find('article-title') is not None:
            titles[title_group.find('article-title').attrib.get('{http://www.w3.org/XML/1998/namespace}lang')] = title_group.findtext('article-title')

        for trans_title in title_group.findall('.//trans-title-group'):
            titles[trans_title.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')] = trans_title.findtext('trans-title')

        dict_data['title-group'] = titles

        return (xml, dict_data)


class AbbrevJournalTitlePipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item

        abbrev_journal_title = xml.findtext('.//journal-title-group/abbrev-journal-title[@abbrev-type="publisher"]')

        if abbrev_journal_title is not None:
            dict_data['abbrev-journal-title'] = abbrev_journal_title

        return (xml, dict_data)


class AbstractPipe(plumber.Pipe):

    def transform(self, item):
        abstracts = {}
        xml, dict_data = item
        abstract_group = xml.find('.//article-meta')

        if xml.find('.//article-meta/abstract') is not None:
            abstracts[abstract_group.find('.//abstract').attrib.get('{http://www.w3.org/XML/1998/namespace}lang')] = abstract_group.findtext('.//abstract').strip()

        for trans_abstract in abstract_group.findall('.//trans-abstract'):
            abstracts[trans_abstract.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')] = trans_abstract.text.strip()

        dict_data['abstract'] = abstracts

        return (xml, dict_data)


class JournalIDPipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item

        journal_id = xml.find('.//journal-meta/journal-id[@journal-id-type="nlm-ta"]')

        if journal_id is not None:
            dict_data['journal-id'] = journal_id.text

        return (xml, dict_data)


class LpagePipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item
        lpage = xml.find('.//article-meta/lpage')

        if lpage is not None:
            dict_data['lpage'] = lpage.text

        return (xml, dict_data)


class FpagePipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item
        fpage = xml.find('.//article-meta/fpage')

        if fpage is not None:
            dict_data['fpage'] = fpage.text

        return (xml, dict_data)


class JournalTitlePipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item
        journal_title = xml.find('.//journal-title-group/journal-title')

        if journal_title is not None:
            dict_data['journal-title'] = journal_title.text

        return (xml, dict_data)


class AuthorPipe(plumber.Pipe):

    def transform(self, item):
        contribs = {}
        list_author = []

        xml, dict_data = item

        for contrib in xml.findall('.//contrib-group/contrib[@contrib-type="author"]'):
            list_author.append({'given-names':contrib.findtext('.//given-names'),
                                'surname':contrib.findtext('.//surname'),
                                'affiliations':[ref.attrib['rid'] for ref in contrib.findall('.//xref') if ref is not None]})

        contribs['authors'] = list_author
        dict_data['contrib-group'] = contribs

        return (xml, dict_data)


class AffiliationPipe(plumber.Pipe):

    def transform(self, item):
        list_aff = []

        xml, dict_data = item

        affiliations = xml.findall('.//article-meta/aff')

        if affiliations is not None:

            for aff in affiliations:
                ref_id = aff.get('id')
                institution = aff.findtext('.//institution[@content-type="orgname"]')
                country = aff.findtext('.//country')
                dict_aff = {}

                if institution:
                    dict_aff['institution'] = institution

                if ref_id:
                    dict_aff['ref'] = ref_id

                if country:
                    dict_aff['country'] = country

                list_aff.append(dict_aff)

        dict_data['affiliations'] = list_aff

        return (xml, dict_data)


class KeywordPipe(plumber.Pipe):

    def transform(self, item):
        keywords = {}
        xml, dict_data = item

        for kwd in xml.findall('.//article-meta/kwd-group'):
            keywords[kwd.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')] = [k.text for k in kwd.findall('.//kwd') if k.text]

        dict_data['keyword-group'] = keywords

        return (xml, dict_data)


class DefaultLanguagePipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item

        if xml.getroot().attrib.get('{http://www.w3.org/XML/1998/namespace}lang') is not None:
            dict_data['default-language'] = xml.getroot().attrib.get('{http://www.w3.org/XML/1998/namespace}lang')

        return (xml, dict_data)


class VolumePipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item
        volume = xml.find('.//article-meta/volume')

        if volume is not None:
            dict_data['volume'] = volume.text

        return (xml, dict_data)


class NumberPipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item
        number = xml.find('.//article-meta/issue')

        if number is not None:
            dict_data['number'] = number.text

        return (xml, dict_data)


class PubDatePipe(plumber.Pipe):

    def transform(self, item):
        dates = {}
        xml, dict_data = item

        for date in xml.findall('.//pub-date/'):
            if date.tag and date.text:
                dates[date.tag] = date.text

        dict_data['pub-date'] = dates

        return (xml, dict_data)


class ISSNPipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item
        issn = xml.find('.//journal-meta/issn[@pub-type="epub"]')

        if issn is not None:
            dict_data['issn'] = issn.text

        return (xml, dict_data)


class PublisherNamePipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item
        publisher_name = xml.find('.//journal-meta/publisher/publisher-name')

        if publisher_name is not None:
            dict_data['publisher-name'] = publisher_name.text

        return (xml, dict_data)


class SubjectPipe(plumber.Pipe):

    def transform(slef, item):
        subjects = {}
        xml, dict_data = item

        for sub_subject in xml.findall('.//article-meta/article-categories/subj-group'):
            if sub_subject.get('subj-group-type'):
                subjects[sub_subject.attrib['subj-group-type']] = [subject.text for subject in sub_subject if subject.text]

        dict_data['subjects'] = subjects

        return (xml, dict_data)


class PublisherIDPipe(plumber.Pipe):

    def transform(self, item):
        article_ids = {}
        xml, dict_data = item

        for article_id in xml.findall('.//article-meta/article-id'):
            if article_id.get('pub-id-type') and article_id.text:
                article_ids[article_id.get('pub-id-type')] = article_id.text

        dict_data['article-ids'] = article_ids

        return (xml, dict_data)


class TearDownPipe(plumber.Pipe):

    def transform(self, item):
        xml, dict_data = item
        return json.dumps(dict_data, indent=2)


if __name__ == '__main__':
    ppl = plumber.Pipeline(SetupPipe(),
                           TitlePipe(),
                           AbbrevJournalTitlePipe(),
                           AbstractPipe(),
                           JournalIDPipe(),
                           AuthorPipe(),
                           AffiliationPipe(),
                           KeywordPipe(),
                           DefaultLanguagePipe(),
                           LpagePipe(),
                           FpagePipe(),
                           JournalTitlePipe(),
                           VolumePipe(),
                           NumberPipe(),
                           PubDatePipe(),
                           ISSNPipe(),
                           PublisherNamePipe(),
                           SubjectPipe(),
                           PublisherIDPipe(),
                           TearDownPipe())

    xml = etree.parse(open('<FILELIKEOBJECT>', 'rb'))
    data = ppl.run([xml])

    for dt in data:
        print dt
