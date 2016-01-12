#coding:utf-8

import sae
sae.add_vendor_dir('vendors')
from ninandemo import wsgi

application = sae.create_wsgi_app(wsgi.application)
