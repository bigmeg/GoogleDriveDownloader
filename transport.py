import os, threading, time, configparser
from pySmartDL import SmartDL, utils
from googleapiclient.errors import HttpError
from apiclient import discovery
import oauth2client
from googleapiclient.http import MediaFileUpload
from oauth2client import client
import httplib2
from mimetypes import MimeTypes


class Flag:
    noauth_local_webserver = True
    logging_level = 'ERROR'


dir_path = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(dir_path, 'settings.ini'))
mime = MimeTypes()
SCOPES = config['transport']['SCOPE']
CLIENT_SECRET_FILE = os.path.join(dir_path, config['transport']['CLIENT_SECRET_FILE'])
CREDENTIAL_FILE = os.path.join(dir_path, config['transport']['CREDENTIAL_FILE'])
APPLICATION_NAME = config['transport']['APPLICATION_NAME']
CHUNKSIZE = int(config['transport']['CHUNKSIZE']) * 1024**2
RETRY = int(config['transport']['RETRY'])


class Manager(object):
    def __init__(self):
        self.store = oauth2client.file.Storage(CREDENTIAL_FILE)
        self.credentials = self.store.get()
        self.auth_ready = self.credentials and not self.credentials.invalid
        self.download_arr, self.upload_arr, self.error_arr = [], [], []
        threading.Thread(target=self.checker, daemon=True).start()
        threading.Thread(target=self.uploader, daemon=True).start()
        self.res_down, self.res_up, self.res_err = [], [], []
        threading.Thread(target=self.reporter, daemon=True).start()

    def checker(self):
        while True:
            for obj in self.download_arr:
                if obj.isFinished():
                    self.download_arr.remove(obj)
                    if obj.isSuccessful():
                        if obj.upload:
                            obj.status = 'waiting to upload'
                            self.upload_arr.append(obj)
                        elif obj.delete:
                            os.remove(obj.dest)
                    else:
                        self.error_arr.append(obj)
            time.sleep(0.66)

    def uploader(self):
        while True:
            if not self.auth_ready or len(self.upload_arr) == 0:
                time.sleep(0.66)
                continue
            obj = self.upload_arr[0]
            obj.status = "uploading"

            service = discovery.build('drive', 'v3', http=self.credentials.authorize(httplib2.Http()))
            media = MediaFileUpload(obj.dest,
                                    mimetype=mime.guess_type(os.path.basename(obj.dest))[0],
                                    chunksize=CHUNKSIZE,
                                    resumable=True)
            request = service.files().create(body={'name': os.path.basename(obj.dest)},
                                             media_body=media)
            response = None
            fail = False
            for retry in range(RETRY):
                try:
                    while response is None:
                        start_time = time.time()
                        status, response = request.next_chunk()
                        time_elapsed = time.time() - start_time
                        if retry > 0:
                            obj.status = "uploading retrying at " + retry
                        if status:
                            status.speed = '%.1f' % (CHUNKSIZE / 1024**2 / time_elapsed) + 'MB/s'
                            left = status.total_size - status.resumable_progress
                            status.eta = utils.time_human(int(left / (CHUNKSIZE / time_elapsed)))
                            obj.up_status = status
                    break
                except HttpError as e:
                    if e.resp.status in [404]:
                        service = discovery.build('drive', 'v3', http=self.credentials.authorize(httplib2.Http()))
                        request = service.files().create(body={'name': os.path.basename(obj.dest)},
                                                         media_body=media)
                        response = None
                    elif e.resp.status in [500, 502, 503, 504]:
                        continue
                    else:
                        obj.errors.append(e)
                        obj.status = "upload error"
                        self.error_arr.append(obj)
                        fail = True
                        break
                except Exception as e:
                    obj.errors.append(e)
                    obj.status = "upload error"
                    self.error_arr.append(obj)
                    fail = True
                    break

            self.upload_arr.remove(obj)
            if not fail and obj.delete:
                os.remove(obj.dest)

    def reporter(self):
        while True:
            time.sleep(0.66)
            res_down_temp, res_up_temp, res_err_temp = [], [], []
            for obj in self.download_arr:
                value = {
                    "filename": obj.filename,
                    "status": obj.status,
                    "download_size": obj.get_dl_size(human=True),
                    "file_size": utils.sizeof_human(obj.filesize),
                    "speed": obj.get_speed(human=True),
                    "progress": obj.get_progress(),
                    "eta": obj.get_eta(human=True)
                }
                res_down_temp.append(value)
            for obj in self.upload_arr:
                up_status = obj.up_status if hasattr(obj, 'up_status') else None
                value = {
                    "filename": obj.filename,
                    "upload_size": utils.sizeof_human(up_status.resumable_progress) if up_status else 0,
                    "status": obj.status,
                    "progress": up_status.progress() if up_status else 0,
                    "speed": up_status.speed if up_status else 0,
                    "file_size": utils.sizeof_human(obj.filesize),
                    "eta": up_status.eta if up_status else 0
                }
                res_up_temp.append(value)
            for obj in self.error_arr:
                value = {
                    "filename": obj.filename,
                    "status": obj.status,
                    "errors": [str(err) for err in obj.get_errors()]
                }
                res_err_temp.append(value)
            self.res_down, self.res_up, self.res_err = res_down_temp, res_up_temp, res_err_temp

    def add_new_task(self, url, filename, upload=True, delete=True):
        def add_new_task_non_block(_url, _filename, _upload, _delete):
            dest = os.path.expanduser('~/Downloads/' + _filename)
            obj = SmartDL(_url, dest=dest, progress_bar=False, threads=1, fix_urls=False)
            obj.filename = _filename
            obj.upload = _upload
            obj.delete = _delete
            try:
                obj.start(blocking=False)
                self.download_arr.append(obj)
            except Exception as e:
                obj.errors.append(e)
                self.error_arr.append(obj)
        threading.Thread(target=add_new_task_non_block, args=(url, filename, upload, delete)).start()

    def get_auth_url(self):
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.redirect_uri = client.OOB_CALLBACK_URN
        flow.user_agent = APPLICATION_NAME
        self.flow = flow
        return flow.step1_get_authorize_url()

    def put_auth_code(self, code):
        try:
            credential = self.flow.step2_exchange(code)
        except client.FlowExchangeError:
            return False
        self.store.put(credential)
        credential.set_store(self.store)
        self.credentials = credential
        self.auth_ready = True
        return True

    def status(self):
        return self.res_down, self.res_up, self.res_err


if __name__ == "__main__":
    man = Manager()
    if not man.auth_ready:
        print(man.get_auth_url())
        print(man.put_auth_code(input("Please visit the authentication link above and input the code: ").strip()))
    while True:
        string = input("Please specify command: s(status) or [link name]").strip()
        if string == 's':
            res_down, res_up, res_err = man.status()
            print(res_down, res_up, res_err)
        else:
            link = string[0:string.find(' ')]
            name = string[string.find(' ')+1:]
            man.add_new_task(link, name)
