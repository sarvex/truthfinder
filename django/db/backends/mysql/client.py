import os
import sys

from django.db.backends import BaseDatabaseClient

class DatabaseClient(BaseDatabaseClient):
    executable_name = 'mysql'

    def runshell(self):
        settings_dict = self.connection.settings_dict
        args = [self.executable_name]
        db = settings_dict['OPTIONS'].get('db', settings_dict['NAME'])
        user = settings_dict['OPTIONS'].get('user', settings_dict['USER'])
        passwd = settings_dict['OPTIONS'].get('passwd', settings_dict['PASSWORD'])
        host = settings_dict['OPTIONS'].get('host', settings_dict['HOST'])
        port = settings_dict['OPTIONS'].get('port', settings_dict['PORT'])
        if defaults_file := settings_dict['OPTIONS'].get('read_default_file'):
            args += [f"--defaults-file={defaults_file}"]
        if user:
            args += [f"--user={user}"]
        if passwd:
            args += [f"--password={passwd}"]
        if host:
            args += [f"--socket={host}"] if '/' in host else [f"--host={host}"]
        if port:
            args += [f"--port={port}"]
        if db:
            args += [db]

        if os.name == 'nt':
            sys.exit(os.system(" ".join(args)))
        else:
            os.execvp(self.executable_name, args)

