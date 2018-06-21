import xmlrpc.client
import threading, time, utils, os


class Aria2Man:
    def __init__(self, host='localhost', port=6800, refresh_interval=0.5):
        self.server = xmlrpc.client.ServerProxy('http://%s:%d/rpc' % (host, port))
        self.wait_queue = list()
        self.work_queue = list()
        self.remove_queue = list()
        self.refresh_interval = refresh_interval
        threading.Thread(target=self.loop).start()

    def loop(self):
        while True:
            while len(self.remove_queue) > 0:
                item = self.remove_queue.pop()
                self.server.aria2.remove(item["gid"])
                self.server.aria2.removeDownloadResult(item["gid"])
                self.work_queue.remove(item)
                os.remove(item["dir"] + item["filename"])
                os.remove(item["dir"] + item["filename"] + ".aria2")
            while len(self.wait_queue) > 0:
                task = self.wait_queue.pop()
                gid = self.server.aria2.addUri([task["url"]],
                                               {'dir': task["dest"],
                                                'out': task["filename"],
                                                'auto-file-renaming': 'false',
                                                'allow-overwrite': 'true'})
                self.work_queue.append({"gid": gid,
                                        'dir': task["dest"],
                                        "callback": task["callback"],
                                        "filename": task["filename"],
                                        "url": task["url"]})

            for task in self.work_queue:
                response = self.server.aria2.tellStatus(task["gid"])
                task["response"] = response
                if response["status"] == "complete":
                    task["callback"]()
                    self.work_queue.remove(task)

            time.sleep(self.refresh_interval)

    def add_task(self, url, dest, filename, callback=lambda: None):
        self.wait_queue.append({"url": url,
                                "dest": dest,
                                "filename": filename,
                                "callback": threading.Thread(target=callback).start})

    def _look_up(self, gid=None, filename=None):
        return next(filter(lambda x: x["gid"] == gid or x["filename"] == filename, self.work_queue), None)

    def remove_task(self, gid=None, filename=None):
        item = self._look_up(gid, filename)
        if item is not None:
            self.remove_queue.append(item)

    def get_task(self, gid=None, filename=None):
        task = self._look_up(gid, filename)
        return task if task is not None else self.work_queue

    def get_status(self, filename=None):
        queue = [x for x in self.work_queue if ((x['filename'] == filename) if filename is not None else True)]
        result = []
        for task in queue:
            response = task["response"]
            speed = int(response["downloadSpeed"])
            completedLength = int(response["completedLength"])
            totalLength = int(response["totalLength"])
            result.append({"filename": task["filename"],
                           "status": response["status"],
                           "completedLength": utils.sizeof_human(completedLength),
                           "totalLength": utils.sizeof_human(totalLength),
                           "speed": "%s/s" % utils.sizeof_human(speed),
                           "progress": completedLength / (totalLength if totalLength > 0 else float("inf")),
                           "eta": utils.time_human(int((totalLength-completedLength)/(speed if speed > 0 else 0.1)))})
        return result


# if __name__ == "__main__":
#     man = Aria2Man(refresh_interval=0.1)
#     man.add_task(url="http://ipv4.download.thinkbroadband.com/512MB.zip",
#                  dest="/Users/hht/Downloads",
#                  filename="512MB.zip",
#                  callback=lambda: print("yes1"))
#     time.sleep(1)
#     man.add_task(url="http://ipv4.download.thinkbroadband.com/100MB.zip",
#                  dest="/Users/hht/Downloads",
#                  filename="100MB.zip",
#                  callback=lambda: print("yes2"))
#     while True:
#         print(man.get_status())
#         time.sleep(1)
