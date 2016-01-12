# coding: utf-8

from django.conf.urls import url

from django.views.generic.base import TemplateView

from demo.views import (SearchIndexView,
                        UpdateSearchIndexView,
                        JiebaInitView)

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name="index.html")),
    url(r'^re_search/$', SearchIndexView.as_view(), name="search_redirect"),
    url(r'^update_index/$', UpdateSearchIndexView.as_view(), name="update_index"),
    url(r'^init_jieba/$', JiebaInitView.as_view(), name="init_jieba")
]
