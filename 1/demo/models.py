# coding: utf-8

from django.db import models


class DemoNote(models.Model):
    title = models.CharField(verbose_name="title", max_length=32)
    content = models.TextField(verbose_name="content")
