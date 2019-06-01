import os
import subprocess
import sys
from subprocess import PIPE
from threading import Thread

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from cra_helper import CRA_FS_APP_DIRS, CRA_APPS_NAME
from cra_helper.process_index_html import process_html


class Command(BaseCommand):
    def __init__(self):
        super().__init__()
        self.error = False

    help = "Build react apps"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            'react_app', metavar='react_app', type=str, nargs='*',
            help='Names of React app(s) to build'
        )
        parser.add_argument(
            '--yarn', dest='use_yarn', action='store_true',
            help='Use yarn instead of npm'
        )
        parser.add_argument(
            '--collectstatic', dest='collectstatic', action='store_true',
            help='Run collectstatic after building'
        )

    def handle(self, *args, **options):
        # find npm or yarn
        cmd = subprocess.Popen('which npm'.split(), stdout=PIPE).stdout.read().strip()
        if options['use_yarn'] or not cmd:
            cmd = subprocess.Popen('which yarn'.split(), stdout=PIPE).stdout.read().strip()
        if not cmd:
            raise CommandError('Cannot find npm or yarn binary')
        cmd = cmd.decode('utf8')
        if cmd.endswith('npm'):
            cmd += ' run'

        # select react apps to be build
        if options['react_app']:
            all_apps = set(CRA_APPS_NAME)
            apps = set(options['react_app'])
            if not all_apps.issuperset(apps):
                invalid_apps = ', '.join(list(apps.difference(all_apps)))
                raise CommandError('Cannot find these react apps: ' + invalid_apps)
            app_dirs = [CRA_FS_APP_DIRS[app_name] for app_name in apps]
        else:
            app_dirs = CRA_FS_APP_DIRS.values()

        # start building each react app in one thread
        threads = []
        for app_dir in app_dirs:
            thread = Thread(target=self.run_build, args=(cmd, app_dir))
            thread.start()
            threads.append(thread)

        # wait for threads to complete
        for thread in threads:
            thread.join()

        if self.error:
            exit(1)

        # collect static
        if options['collectstatic']:
            manage_py = os.path.join(settings.BASE_DIR, 'manage.py')

            error = subprocess.Popen(f'python {manage_py} collectstatic'.split(), stderr=PIPE) \
                .stderr.read().decode('utf8')

            if error:
                print(error, file=sys.stderr)
                exit(1)

    def run_build(self, cmd, app_dir):
        # build react app
        print(f'Building react app at {app_dir}')

        result = subprocess.Popen(f'{cmd} build --prefix {app_dir}'.split(), stdout=PIPE, stderr=PIPE)
        err = result.stderr.read()
        out = result.stdout.read()

        if err:
            print(f'>>> ERROR while building react app {app_dir}', file=sys.stderr)
            print(out.decode('utf8'), file=sys.stderr)
            print(err.decode('utf8'), file=sys.stderr)
            print('\n', file=sys.stderr)
            self.error = True
            return

        # post compile process index.html
        print(f'Post processing index.html at {app_dir}')

        index_html_path = os.path.join(app_dir, 'build', 'index.html')
        try:
            with open(index_html_path, 'r+') as file:
                content = process_html(file.read())
                file.seek(0)
                file.truncate()
                file.write(content)
        except Exception as e:
            print('Cannot post process ' + index_html_path, file=sys.stderr)
            print(e, file=sys.stderr)
            self.error = True
            return

        print(f'Finish building {app_dir}')
