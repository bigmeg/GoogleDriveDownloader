var express = require('express');
var router = express.Router();

/* GET home page. */

let authLink = null;
let authCallback = null;
let incorrect = false;

router.get('/', function(req, res, next) {
  res.render('auth', { incorrect: incorrect, link: authLink });
});

router.post('/', function (req, res, next) {
  if (authCallback == null) return;
  authCallback(req.body.code, (success) => {
    if (success) {
        incorrect = false;
        authLink = null;
        res.redirect('/');
    } else {
        incorrect = true;
        res.redirect(req.baseURI);
    }
  });
});

router.registerAuthCallback = (link, callback) => {
    authLink = link;
    authCallback = callback;
};

module.exports = router;
