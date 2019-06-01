import logging
from urllib import request, error as url_error

from django.conf import settings


def is_server_live(server_path: str) -> bool:
    # Ignore the server check if we're in production
    if settings.DEBUG:
        try:
            resp = request.urlopen(server_path)
            if resp.status == 200:
                logging.info(f'CRA live server running at {server_path}')
                return True
            else:
                logging.warning(f'CRA live server is up but not serving at {server_path}')
                return False
        except url_error.URLError as e:
            logging.warning(f'CRA live server is not running {server_path}')
            return False
    else:
        return False
