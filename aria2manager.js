const aria2_subprocess = require('child_process').spawn('aria2c', ['--enable-rpc']);
process.on('exit', () => aria2_subprocess.kill());

const aria2 = new (require("aria2"))();
const fs = require('fs');
const path = require('path');
const misc = require('./misc.js');

const aria2manager = module.exports = {};

aria2manager.queue = [];


aria2manager.addUri = (uri, name) => {
    return new Promise((resolve, reject) => {
        aria2.call("addUri", [uri], {dir: misc.config.transport.downloadPath, out: name})
            .then((gid) => {
                let obj = {gid: gid, name: name, uri: uri};
                aria2manager.queue.push(obj);
                let interval = setInterval(() => {
                    if (obj.scheduleForRemove) {  // check for delete request
                        clearInterval(interval);
                        console.info(`deleting task from aria2 for gid: ${gid} , name: ${name}`);
                        aria2.call('forceRemove', gid)
                            .catch(console.error)
                            .finally(() => {
                                aria2.call('removeDownloadResult', gid)
                                    .catch(console.error)
                                    .finally(() => {
                                        misc.arrayRemove(aria2manager.queue, {gid});
                                        console.info(`deleting task from file system for gid: ${gid} , name: ${name}`);
                                        let filepath = obj.path ? obj.path : path.join(downloadPath, name);
                                        fs.unlink(filepath, (err) => err ? console.error(err) : null);
                                        fs.unlink(filepath + '.aria2', (err) => err ? console.error(err) : null);
                                        reject(obj);
                                    });
                            });
                        return;
                    }
                    aria2.call('tellStatus', gid)  // check for status
                        .then((res) => {
                            obj.path = res.files[0].path;
                            obj.status = res.status;
                            obj.totalLength = res.totalLength;
                            obj.completedLength = res.completedLength;
                            obj.speed = res.downloadSpeed;
                            obj.status = res.status;
                            if (obj.status === 'complete') {
                                misc.arrayRemove(aria2manager.queue, {gid});
                                clearInterval(interval);
                                resolve(obj);
                            }
                        }).catch(console.error);
                }, 500);
            }).catch(reject);
    });
};


aria2manager.scheduleRemove = (options) => {
    if (!options || Object.keys(options).length === 0) return;
    aria2manager.queue.forEach((task) => task.scheduleForRemove = Object.keys(options).every((key) => task.hasOwnProperty(key) && task[key] == options[key]));
};




// test
if (require.main === module) {
    aria2manager.addUri('http://ipv4.download.thinkbroadband.com/5MB.zip', '5MB.zip')
        .then(console.log)
        .catch(console.error);
    // aria2manager.addUri(uri = 'http://ipv4.download.thinkbroadband.com/100MB.zip', name = '100MB2.zip').then(console.log);
    // aria2manager.addUri(uri = 'http://ipv4.download.thinkbroadband.com/100MB.zip', name = '100MB3.zip').then(console.log);
    setInterval(() => console.log(aria2manager.queue), 1000);
    // setTimeout(() => aria2manager.scheduleRemove({name: '100MB1.zip'}), 3000);
}