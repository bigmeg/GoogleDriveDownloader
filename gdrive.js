const {google} = require('googleapis');
const misc = require('./misc');
const mime = require('mime-types');
const fs = require('fs');
const axios = require('axios');

const gdrive = module.exports = {};

const SCOPES = misc.config.transport.scope;
const {client_secret, client_id, redirect_uris} = misc.config.credential.installed;
const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

gdrive.queue = [];

if (misc.config.token == null) {
    gdrive.authRequired = true;
} else {
    try {
        oAuth2Client.setCredentials(misc.config.token);
        gdrive.authRequired = false;
    } catch (err) {
        delete misc.config.token;
        gdrive.authRequired = true;
    }
}


gdrive.getAuthProcedure = () => {
    let authLink = oAuth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: SCOPES,
        prompt: 'consent'
    });

    function authenticator(code, successCallback) {
        oAuth2Client.getToken(code, (err, token) => {
            if (err) {
                console.error('Error retrieving access token', err);
                successCallback(false);
            } else {
                oAuth2Client.setCredentials(token);
                console.info("Google Drive login complete.")
                // Store the token to disk for later program executions
                misc.config.token = token;
                misc.saveConfig();
                successCallback(true);
                gdrive.authRequired = false;
            }
        });
    }

    return {authLink: authLink, authenticator: authenticator};
};


gdrive.upload = async (filename, filepath, obj) => {
    const drive = google.drive({version: 'v3', auth: oAuth2Client});
    // const fileSize = fs.statSync(filepath).size;
    gdrive.queue.push(obj = obj ? obj : {name: filename, path: filepath});
    obj.status = 'active';
    try {
        const res = await drive.files.create(
            {
                requestBody: {
                    'name': filename,
                    'mimeType': mime.lookup(filename)
                },
                media: {
                    mimeType: mime.lookup(filename),
                    body: fs.createReadStream(filepath),
                }
            }, {
                maxRedirects: 0,
                onUploadProgress: (evt) => obj.completedLength = `${evt.bytesRead}`,
                cancelToken: new axios.CancelToken((c) => {obj.cancel = () => {obj.status === 'active' ? c() : null}})
            });
        obj.status = 'complete';
        misc.arrayRemove(gdrive.queue, obj);
        obj.result = res.data;
        console.info('gdrive upload complete', obj);
        return obj;
    } catch (err) {
        if (axios.isCancel(err)) {
            console.info(`upload ${obj.name} canceled`);
            misc.arrayRemove(gdrive.queue, obj);
            obj.status = 'canceled';
            throw obj;
        } else {
            obj.status = 'error';
            throw err;
        }

    }
};

gdrive.remove = (options) => misc.arrayRemove(gdrive.queue, options, (task) => task.cancel());


// testing
if (require.main === module) {
    // console.log('called directly');
    if (!gdrive.authRequired) {
        gdrive.upload("5MB.zip", misc.config.transport.downloadPath + '/5MB.zip').then(console.log).catch(console.error);
        // setTimeout(() => gdrive.remove({name: "100MB.zip"}), 3000);
    }
}