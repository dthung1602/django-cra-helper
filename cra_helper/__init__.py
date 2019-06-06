import os
import re

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from cra_helper.server_check import is_server_live

if not hasattr(settings, 'CRA_AUTO_RELOAD'):
    CRA_AUTO_RELOAD = True
else:
    CRA_AUTO_RELOAD = settings.CRA_AUTO_RELOAD

if not hasattr(settings, 'CRA_APPS'):
    raise ImproperlyConfigured('Missing CRA_APPS in setting.py')

CRA_APPS = settings.CRA_APPS

CRA_APPS_NAME = list(CRA_APPS.keys())

# The path to the CRA project directory, relative to the Django project's base directory
CRA_FS_APP_DIRS = {app_name: os.path.join(settings.BASE_DIR, app_name) for app_name in CRA_APPS_NAME}

# add react build directories to staticfiles dirs
static_dirs = [os.path.join(d, 'build', 'static') for d in CRA_FS_APP_DIRS]
settings.STATICFILES_DIRS += static_dirs

CRA_LIVES = {app_name: False for app_name in CRA_APPS}
CRA_URLS = []
CRA_BUNDLE_PATHS = []
PATH_RE_TO_CRA_URL = []

if settings.DEBUG:

    # check if all app has path
    if not all(['path' in app_config for app_config in CRA_APPS.values()]):
        raise ImproperlyConfigured('Missing path config')

    # check if all app has port
    if not all(['port' in app_config for app_config in CRA_APPS.values()]):
        raise ImproperlyConfigured('Missing port config')

    # check for duplicate path
    used_paths = [config['path'] for config in CRA_APPS.values()]
    if len(used_paths) != len(set(used_paths)):
        raise ImproperlyConfigured('Duplicated path of react app')

    # check for duplicate app port
    used_ports = [config['port'] for config in CRA_APPS.values()]
    if len(used_ports) != len(set(used_ports)):
        raise ImproperlyConfigured('Duplicated port of react app')

    # compile path regex
    for config in CRA_APPS.values():
        if isinstance(config['path'], str):
            config['path_re'] = re.compile(config['path'])

    # The URL the create-react-app live server is accessible at
    CRA_URLS = {app_name: f'http://localhost:{config["port"]}' for app_name, config in CRA_APPS.items()}

    # The ability to access this file means the create-react-app live server is running
    CRA_BUNDLE_PATHS = {app_name: f'{url}/static/js/bundle.js' for app_name, url in CRA_URLS.items()}

    # Check if Create-React-App live server is up and running
    CRA_LIVES = {app_name: is_server_live(path) for app_name, path in CRA_BUNDLE_PATHS.items()}

    # A mapping from path to cra_url
    PATH_RE_TO_CRA_URL = {config['path_re']: CRA_URLS[app_name] for app_name, config in CRA_APPS.items()}
