var express = require('express');
var router = express.Router();

/* GET home page. */
let loginObj = {required: false};

router.get('/', function(req, res, next) {
  res.render('index', { login: loginObj});
});

router.loginRequired = (required) => loginObj = {required: required};

module.exports = router;
