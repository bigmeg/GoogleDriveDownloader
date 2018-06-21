from Aria2Manager import Aria2Man
from GoogleDriveManager import GoogleDriveMan
import os


class TransloadMan:
    def __init__(self):
        self.aria2man = Aria2Man()
        self.GDman = GoogleDriveMan()
        self.ready = self.GDman.auth_ready

    def add_task(self, url, filename, upload=True, delete=True):
        dest = os.path.expanduser('~/Downloads/')
        if upload:
            def up():
                if delete:
                    self.GDman.add_task(dest=dest, filename=filename, callback=lambda: os.remove(dest + filename))
                else:
                    self.GDman.add_task(dest, filename)
            self.aria2man.add_task(url=url, dest=dest, filename=filename, callback=up)
        else:
            self.aria2man.add_task(url=url, dest=dest, filename=filename)

    def get_auth_url(self):
        return self.GDman.get_auth_url()

    def put_auth_code(self, code):
        return self.GDman.put_auth_code(code)

    def get_status(self):
        return {'download': self.aria2man.get_status(), 'upload': self.GDman.get_status()}

    def remove_dl_task(self, filename):
        self.aria2man.remove_task(filename=filename)

    def remove_up_task(self, filename):
        self.GDman.remove_task(filename)


# if __name__ == "__main__":
#     man = TransloadMan()
#     if not man.ready:
#         man.put_auth_code(input(man.get_auth_url() + '\n'))
#     man.add_task(url="http://ipv4.download.thinkbroadband.com/100MB.zip",
#                  filename="100MB.zip",
#                  upload=True, delete=False)
#     import time
#     time.sleep(7)
#     man.add_task(url="http://ipv4.download.thinkbroadband.com/100MB.zip",
#                  filename="100MB2.zip",
#                  upload=True, delete=True)
#
#
#     while True:
#         print(man.get_status())
#         time.sleep(1)
