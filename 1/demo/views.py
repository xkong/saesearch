# coding: utf-8

from django.conf import settings
from django.http import HttpResponse
from django.views.generic.base import TemplateView, View

from sae.storage import Bucket as SaeBucket

from utils.kvdb.bucket import Bucket


class SearchIndexView(TemplateView):
    template_name = 'search_index.html'

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        searched = "ajaxSearch();"
        content_data = {'query': query, 'searched': searched}
        return self.render_to_response(content_data)


class UpdateSearchIndexView(View):

    """
    Update indexes for haystack and whoosh. You should call this view from
    crontab.
    """

    def get(self, request, *args, **kwargs):
        from django.core.management import call_command
        from_ = kwargs.get('from', 24)
        call_command('update_index', age=int(from_))
        return HttpResponse("done")


class JiebaInitView(View):

    """
    Initial jieba cache. Read dict.txt and jieba.cache and save to KVDB.
    You should upload dict.txt and jieba.cache to the root path
    of your custom sae storage.
    Hint: upload these two files using cyberduck.
    """

    def get(self, request, *args, **kwargs):

        bucket_name = getattr(settings, "SAE_STORAGE_BUCKET_NAME",
                              'xkong1946')
        sae_bucket = SaeBucket(bucket_name)
        kv_bucket = Bucket()
        files = ['dict.txt', 'jieba.cache']
        ret = []
        for file_ in files:
            contents = sae_bucket.get_object_contents(file_)
            kv_bucket.save(file_, contents)
            ret.append(file_)
        # or return json
        return HttpResponse("done")
