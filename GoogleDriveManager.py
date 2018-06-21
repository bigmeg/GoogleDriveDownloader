import os, threading, time, configparser
from googleapiclient.errors import HttpError
from apiclient import discovery
import oauth2client
from googleapiclient.http import MediaFileUpload
from oauth2client import client
import httplib2
from mimetypes import MimeTypes
import utils


mime = MimeTypes()
dir_path = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(dir_path, 'settings.ini'))
SCOPES = config['transport']['SCOPE']
CLIENT_SECRET_FILE = os.path.join(dir_path, config['transport']['CLIENT_SECRET_FILE'])
CREDENTIAL_FILE = os.path.join(dir_path, config['transport']['CREDENTIAL_FILE'])
APPLICATION_NAME = config['transport']['APPLICATION_NAME']
CHUNKSIZE = int(config['transport']['CHUNKSIZE']) * 1024**2


class GoogleDriveMan:
    def __init__(self):
        self.store = oauth2client.file.Storage(CREDENTIAL_FILE)
        self.credentials = self.store.get()
        self.auth_ready = self.credentials and not self.credentials.invalid
        self.queue = list()

    def get_auth_url(self):
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.redirect_uri = client.OOB_CALLBACK_URN
        flow.user_agent = APPLICATION_NAME
        self.flow = flow
        return flow.step1_get_authorize_url()

    def put_auth_code(self, code):
        try:
            self.credentials = self.flow.step2_exchange(code)
        except client.FlowExchangeError:
            return False
        self.store.put(self.credentials)
        self.credentials.set_store(self.store)
        self.auth_ready = True
        return True

    def remove_task(self, filename):
        self.queue = filter(lambda x: x["filename"] != filename, self.queue)

    def add_task(self, dest, filename, callback=lambda: None):
        if not self.auth_ready:
            raise PermissionError("Google Drive Not Authenticated Yet")
        task = {"filename": filename, "status": "active"}
        self.queue.append(task)
        def _upload():
            service = discovery.build('drive', 'v3', http=self.credentials.authorize(httplib2.Http()))
            media = MediaFileUpload(os.path.join(dest, filename), mimetype=mime.guess_type(filename)[0],
                                    chunksize=CHUNKSIZE, resumable=True)
            request = service.files().create(body={'name': filename}, media_body=media)
            response = None
            succeed = False
            while True:
                try:
                    while response is None:
                        start_time = time.time()
                        status, response = request.next_chunk()
                        time_elapsed = time.time() - start_time
                        speed = int(CHUNKSIZE / time_elapsed)
                        if status:
                            completedLength = int(status.resumable_progress)
                            totalLength = int(status.total_size)
                            task["completedLength"] = utils.sizeof_human(completedLength)
                            task["totalLength"] = utils.sizeof_human(totalLength)
                            task["speed"] = "%s/s" % utils.sizeof_human(speed)
                            task["progress"] = completedLength / totalLength,
                            task["eta"] = utils.time_human(int((totalLength - completedLength) / speed))
                    succeed = True
                    break
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        continue
                    else:
                        task["status"] = "error %d" % e.resp.status
                        break
                except Exception as e:
                    task["status"] = "error %s" % str(e)
                    break
            if succeed:
                self.queue.remove(task)
                callback()
        threading.Thread(target=_upload).start()

    def get_status(self, filename=None):
        return [x for x in self.queue if ((x['filename'] == filename) if filename is not None else True)]

#
# if __name__ == "__main__":
#     man = GoogleDriveMan()
#     man.put_auth_code(input(man.get_auth_url() + '\n'))
#     man.add_task(dest="/Users/hht/Downloads",
#                  filename="512MB.zip",
#                  callback=lambda: print("yes1"))
#     time.sleep(4)
#     man.add_task(dest="/Users/hht/Downloads",
#                  filename="100MB.zip",
#                  callback=lambda: print("yes2"))
#     while True:
#         print(man.get_status())
#         time.sleep(1)