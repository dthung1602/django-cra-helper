import os

import requests
from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader

from cra_helper import CRA_APPS_NAME, CRA_URLS, CRA_LIVES, CRA_FS_APP_DIRS
from cra_helper.process_index_html import process_html


class ReactLoader(BaseLoader):

    def get_template_sources(self, template_name):
        # remove .html
        app_name = template_name[0: len(template_name) - 5]

        # find app name in declared cra apps
        if app_name in CRA_APPS_NAME:
            # if server is running in dev mode & cra live server is running
            # return then url of live server
            if settings.DEBUG and CRA_LIVES[app_name]:
                origin_name = CRA_URLS[app_name]

            # else return the built index.html
            else:
                origin_name = os.path.join(CRA_FS_APP_DIRS[app_name], 'build', 'index.html')

            yield Origin(
                name=origin_name,
                template_name=template_name,
                loader=self
            )

    def get_contents(self, origin):
        # fetch from cra live server
        if origin.name.startswith('http'):
            try:
                response = requests.get(origin.name, verify=False)
                if response.status_code != 200:
                    raise Exception()
            except Exception as e:
                raise TemplateDoesNotExist(origin)
            return process_html(response.text)

        # load from file
        try:
            with open(origin.name, encoding=self.engine.file_charset) as fp:
                return fp.read()
        except FileNotFoundError:
            raise TemplateDoesNotExist(origin)
