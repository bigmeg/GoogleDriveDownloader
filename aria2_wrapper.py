import subprocess
import xmlrpc.client
import os
import time
import threading
from utils import time_human, sizeof_human


class PyAria2Manager(object):
    def __init__(self, host='localhost', port=6800, refresh_interval=1):
        if not self._isAria2Installed():
            raise Exception('aria2 is not installed, please install it before.')

        if not self._isAria2rpcRunning():
            cmd = 'aria2c --enable-rpc --max-concurrent-downloads=10 --rpc-listen-port %d' % port
            subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            count = 0
            while not self._isAria2rpcRunning():
                count += 1
                time.sleep(3)
                if count == 5:
                    raise Exception('aria2 RPC server started failure.')

        self.server = xmlrpc.client.ServerProxy('http://%s:%d/rpc' % (host, port))
        self.task = []
        self.lock = threading.Lock()
        threading.Thread(target=self.__task_tracker, daemon=True, args=[refresh_interval]).start()

    def __task_tracker(self, refresh_interval=1):
        while True:
            for task in self.task:
                try:
                    with self.lock:
                        response = self.server.aria2.tellStatus(task.gid)
                    task.status = response['status']
                    task.speed = int(response['downloadSpeed'])
                    task.completed_size = int(response['files'][0]['completedLength'])
                    task.file_size = int(response['files'][0]['length'])
                    task.dest = response['files'][0]['path']
                    task.progress = task.completed_size / task.file_size
                    task.eta = int((task.file_size - task.completed_size) / task.speed) if task.speed > 0 else 0
                    if task.status in ['complete', 'error']:
                        self.task.remove(task)
                    if task.status == 'error':
                        task.errors.append(response.get('errorMessage', 'NoErrorMessageFetched'))
                except Exception as e:
                    print(e)
            time.sleep(refresh_interval)

    def new_task(self, url, dest_folder, filename):
        return PyAria2Task(url, dest_folder, filename, self)

    def _register_task(self, task):
        with self.lock:
            task.gid = self.server.aria2.addUri([task.url],
                                                {'dir': task.dest_folder,
                                                 'out': task.filename,
                                                 'auto-file-renaming': 'false',
                                                 'allow-overwrite': 'true'})
        task.status = 'started'
        self.task.append(task)

    def _isAria2Installed(self):
        for cmdpath in os.environ['PATH'].split(':'):
            if os.path.isdir(cmdpath) and 'aria2c' in os.listdir(cmdpath):
                return True
        return False

    def _isAria2rpcRunning(self):
        pgrep_process = subprocess.Popen('pgrep -l aria2', shell=True, stdout=subprocess.PIPE)
        return pgrep_process.stdout.readline() != b''


class PyAria2Task(object):
    def __init__(self, url, dest_folder, filename, manager):
        self.dest_folder = dest_folder
        self.url = url
        self.filename = filename
        self.manager = manager
        self.status = 'created'
        self.speed = 0
        self.completed_size = 0
        self.file_size = 0
        self.gid = ''
        self.progress = 0
        self.eta = 0
        self.dest = ''
        self.errors = []

    def start(self, blocking=False, status_bar=False):
        if self.status != 'created':
            pass
        try:
            self.manager._register_task(self)
            while blocking and self.status not in ['complete', 'error']:
                if status_bar:
                    print(self.filename, self.status, self.speed, self.file_size, self.progress, self.eta)
                time.sleep(1)
        except Exception as e:
            self.errors.append(e)

    def isFinished(self): return self.status in ['complete', 'error']

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





