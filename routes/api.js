const express = require('express');
const router = express.Router();
const aria2manager = require('../aria2manager.js');
const gdrive = require('../gdrive.js');
const fs = require('fs');
const misc = require('../misc.js')

const downloadQueue = aria2manager.queue;
const uploadQueue = gdrive.queue;
const completedQueue = [];

router.post('/addUri', function (req, res, next) {
    let form = req.body;
    console.info(form);
    if (form.name == null || form.link == null || form.upload == null || form.delete == null) {
        res.status(422).json({'message': "missing parameters"});
        return;
    }

    aria2manager.addUri(form.link, form.name).then((dobj) => {
        if (form.upload) {
            gdrive.upload(dobj.name, dobj.path, dobj).then((uobj) => {
                completedQueue.push(uobj);
                if (form.delete) {
                    fs.unlink(uobj.path, (err) => err ? console.error(err) : null);
                }
            }).catch(console.error);
        }
    }).catch(console.error);

    res.status(201).end();
});

router.get('/status', function (req, res, next) {
    res.json({downloadQueue, uploadQueue, completedQueue});
});

router.delete('/task', function (req, res, next) {
    aria2manager.scheduleRemove(req.body);
    gdrive.remove(req.body);
    misc.arrayRemove(completedQueue, req.body);
    res.status(200).end();
});


module.exports = router;
