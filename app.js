var createError = require('http-errors');
var express = require('express');
var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');
var gdrive = require('./gdrive')

var indexRouter = require('./routes/index');
var usersRouter = require('./routes/users');
var authRouter = require('./routes/auth');
var apiRouter = require('./routes/api');

var app = express();
const misc = require('./misc.js');

app.use((req, res, next) => {
    const auth = {login: misc.config.server.username, password: misc.config.server.password};
    const b64auth = (req.headers.authorization || '').split(' ')[1] || '';
    const strauth = Buffer.from(b64auth, 'base64').toString();
    const splitIndex = strauth.indexOf(':');
    const login = strauth.substring(0, splitIndex);
    const password = strauth.substring(splitIndex + 1);

    if (!login || !password || login !== auth.login || password !== auth.password) {
        res.set('WWW-Authenticate', 'Basic realm="401"'); // change this
        res.status(401).send('Authentication required.'); // custom message
        return
    }

    next();
});

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'pug');

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));




app.use('/', indexRouter);
app.use('/users', usersRouter);
app.use('/auth', authRouter);
app.use('/api', apiRouter);

if (gdrive.authRequired) {
    console.info("Google Drive login required.");
    let authProcedure = gdrive.getAuthProcedure();
    indexRouter.loginRequired(true);
    authRouter.registerAuthCallback(authProcedure.authLink, (code, successCallback) => {
        authProcedure.authenticator(code, (success) => {
            successCallback(success);
            indexRouter.loginRequired(!success);
        });
    })
}


// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;
