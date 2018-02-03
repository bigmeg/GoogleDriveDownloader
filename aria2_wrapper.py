import subprocess
import xmlrpc.client
import os
import time
import threading
from utils import time_human, sizeof_human


class PyAria2Initializer(object):
    def __init__(self, host='localhost', port=6800, refresh_interval=1):
        self.port = port
        self.host = host
        self.refresh_interval = refresh_interval
        if not self._isAria2Installed():
            raise Exception('aria2 is not installed, please install it before.')
        if not self._isAria2rpcRunning() and not self._startAria2rpc():
            raise Exception('aria2 is cannot be started.')
        self.server = xmlrpc.client.ServerProxy('http://%s:%d/rpc' % (host, port))
        self.lock = threading.Lock()

    def new_task(self, url, dest_folder, filename):
        return PyAria2Task(url, dest_folder, filename, self.lock, self.server, self.refresh_interval)

    def _isAria2Installed(self):
        for cmdpath in os.environ['PATH'].split(':'):
            if os.path.isdir(cmdpath) and 'aria2c' in os.listdir(cmdpath):
                return True
        return False

    def _isAria2rpcRunning(self):
        pgrep_process = subprocess.Popen('pgrep -l aria2', shell=True, stdout=subprocess.PIPE)
        return pgrep_process.stdout.readline() != b''

    def _startAria2rpc(self):
        cmd = 'aria2c --enable-rpc --max-concurrent-downloads=10 --rpc-listen-port %d' % self.port
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        count = 0
        while not self._isAria2rpcRunning():
            count += 1
            if count == 5:
                return False
            time.sleep(3)
        return True


class PyAria2Task(object):
    def __init__(self, url, dest_folder, filename, lock, server, refresh_interval):
        self.url = url
        self.dest_folder = dest_folder
        self.filename = filename
        self.lock = lock
        self.server = server
        self.refresh_interval = refresh_interval
        self.status = 'created'
        self.speed = 0
        self.completed_size = 0
        self.file_size = 0
        self.gid = ''
        self.progress = 0
        self.eta = 0
        self.dest = ''
        self.errors = []

    def start(self, blocking=False):
        if self.status != 'created':
            return
        with self.lock:
            self.gid = self.server.aria2.addUri([self.url],
                                                {'dir': self.dest_folder,
                                                 'out': self.filename,
                                                 'auto-file-renaming': 'false',
                                                 'allow-overwrite': 'true'})
        self.status = 'started'
        if blocking:
            self.__updater()
        else:
            threading.Thread(target=self.__updater, daemon=True).start()

    def __updater(self):
        while self.status not in ['complete', 'error']:
            try:
                with self.lock:
                    response = self.server.aria2.tellStatus(self.gid)
            except ConnectionRefusedError or OSError as e:
                self.status = str(e) + ' aria2 may be down.'
                raise e
            self.status = response['status']
            self.speed = int(response['downloadSpeed'])
            self.completed_size = int(response['files'][0]['completedLength'])
            self.file_size = int(response['files'][0]['length'])
            self.dest = response['files'][0]['path']
            self.progress = (self.completed_size / self.file_size) if self.file_size > 0 else 0
            self.eta = int((self.file_size - self.completed_size) / self.speed) if self.speed > 0 else 0
            if self.status == 'error':
                self.errors.append(response.get('errorMessage', 'NoErrorMessageFetched'))
            time.sleep(self.refresh_interval)

    def isFinished(self): return self.status not in ['created', 'started', 'active', 'waiting']

    def isSuccessful(self): return self.status == 'complete'

    def get_filename(self): return self.filename

    def get_status(self): return self.status

    def get_speed(self, human=True): return sizeof_human(self.speed) if human else self.speed

    def get_completed_size(self, human=True): return sizeof_human(self.completed_size) if human else self.completed_size

    def get_file_size(self, human=True): return sizeof_human(self.file_size) if human else self.file_size

    def get_progress(self): return self.progress

    def get_eta(self, human=True): return time_human(self.eta) if human else self.eta

    def get_dest(self): return self.dest

    def get_errors(self): return self.errors

    def get_summary_dict(self):
        return {"filename": self.filename,
                "status": self.status,
                "completed_size": self.get_completed_size(),
                "file_size": self.get_file_size(),
                "speed": self.get_speed(),
                "progress": self.get_progress(),
                "eta": self.get_eta()}
