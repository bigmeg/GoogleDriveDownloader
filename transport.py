import os, threading, time, configparser
import aria2_wrapper
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
REFRESH_INTERVAL = int(config['transport']['REFRESH_INTERVAL'])


class Manager(object):
    def __init__(self):
        self.aria2_man = aria2_wrapper.PyAria2Initializer(refresh_interval=REFRESH_INTERVAL)
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
            time.sleep(REFRESH_INTERVAL)

    def uploader(self):
        while True:
            if not self.auth_ready or len(self.upload_arr) == 0:
                time.sleep(REFRESH_INTERVAL)
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
                            obj.speed = int(CHUNKSIZE / time_elapsed)
                            obj.completed_size = status.resumable_progress
                            obj.eta = int((status.total_size - status.resumable_progress) / (CHUNKSIZE / time_elapsed))
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
            time.sleep(REFRESH_INTERVAL)
            res_down_temp, res_up_temp, res_err_temp = [], [], []
            for obj in self.download_arr:
                res_down_temp.append(obj.get_summary_dict())
            for obj in self.upload_arr:
                res_up_temp.append(obj.get_summary_dict())
            for obj in self.error_arr:
                value = {"filename": obj.filename,
                         "status": obj.status,
                         "errors": [str(err) for err in obj.get_errors()]}
                res_err_temp.append(value)
            self.res_down, self.res_up, self.res_err = res_down_temp, res_up_temp, res_err_temp

    def add_new_task(self, url, filename, upload=True, delete=True):
        dest_folder = os.path.expanduser('~/Downloads/')
        obj = self.aria2_man.new_task(url, dest_folder, filename)
        obj.upload = upload
        obj.delete = delete
        try:
            obj.start()
            self.download_arr.append(obj)
        except Exception as e:
            obj.errors.append(e)
            self.error_arr.append(obj)

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
