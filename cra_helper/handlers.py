import logging
import re
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.handlers.exception import response_for_exception
from django.shortcuts import redirect

from cra_helper import PATH_RE_TO_CRA_URL, CRA_AUTO_RELOAD

logger = logging.getLogger(__name__)
main_hot_update_regex = re.compile(r'^/main\.[a-f0-9]+\.hot-update\.js$')


class CRAStaticFilesHandler(StaticFilesHandler):
    """
    This file handler redirects static asset 404's and hot update requests
    to the correct Create-React-App live server
    """

    def _should_handle(self, path):
        if self.should_forward_cra(path):
            return True
        return super()._should_handle(path)

    def get_response(self, req):
        from django.http import Http404
        path = req.path

        # handle static files
        if self._should_handle(path):
            try:
                # Try to handle the request as usual
                return self.serve(req)
            except Http404 as e:
                cra_url = self.get_request_url(req)

                # if not debugging or auto reload is disable -> return error as usual
                # if debugging and cannot find cra_url -> return error
                if not settings.DEBUG or not cra_url:
                    return response_for_exception(req, e)

                # if debugging and cra_url is found -> redirect to cra live server
                return redirect(cra_url)

        return super().get_response(req)

    @staticmethod
    def should_forward_cra(path):
        return settings.DEBUG and \
               CRA_AUTO_RELOAD and \
               (path.startswith('/sockjs-node') or
                path.startswith('/__webpack_dev_server__') or
                main_hot_update_regex.match(path))

    @staticmethod
    def get_request_url(req):
        """Match request to correct react live server"""

        # find the referer
        referer = req.META.get('HTTP_REFERER')

        # try to find a cra app path that matches the referer
        if referer:
            referer_path = urlparse(referer).path
            for path_re, cra_url in PATH_RE_TO_CRA_URL.items():
                if path_re.match(referer_path):
                    return cra_url + req.get_full_path()
