# coding: utf-8
#
"""
Haystack indexes.

"""
from haystack import indexes

from demo.models import DemoNote


class NoteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return DemoNote

    def get_updated_field(self):
        return 'content'
