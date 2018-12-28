const fs = require('fs');
const path = require('path');

var misc = module.exports = {};

misc.config = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json')));

misc.config.transport.downloadPath = misc.config.transport.downloadPath.startsWith('~') ? (require('os').homedir() + misc.config.transport.downloadPath.substr(1)) : misc.config.transport.downloadPath;

misc.saveConfig = () => {
    fs.writeFileSync(path.join(__dirname, 'config.json'), JSON.stringify(misc.config, null, 2));
    console.info('config.json saved.');
};


misc.arrayRemove = (array, options, func) => {
    if (!options || Object.keys(options).length === 0) return;
    for (let i = array.length - 1; i >= 0; i--) {
        let task = array[i];
        if (Object.keys(options).every((key) => task.hasOwnProperty(key) && task[key] == options[key])) {
            array.splice(i, 1);
            if (func) func(task);
        }
    }
};