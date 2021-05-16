const express = require('express');
const env = require('dotenv').config();
const session = require('express-session');
const FileStore = require('session-file-store')(session);
const cookieParser = require("cookie-parser");
const path = require('path');
const crypto = require("crypto");
const bodyParser = require('body-parser');
const hbs = require('hbs');
const {docker} = require("./routes/docker.js")

const app = express();

app.use(express.static('public'));
app.use(cookieParser());
app.use(express.urlencoded({extended: false}));
app.use(express.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());
app.use(session({
    name: "auth",
    secret: env.parsed.session,
    resave: false,
    saveUninitialized: true,
    store: new FileStore({path: __dirname+'/sessions/'})
}));
app.set('views', path.join(__dirname, "views/"))
app.engine('html', hbs.__express)
app.set('view engine', 'html')
app.use((req, res, next) => {
    if (!req.session.files )
        req.session.files = [];
    if (!req.session.name)
        req.session.name = md5(req.ip);
    next();
})

const md5 = function (s) { return crypto.createHash('md5').update(s).digest('hex') }
require('./routes/cos.js')(app, md5, docker)
require("./routes/panel.js")(app, md5, docker)

app.get('/flag', function(req, res){
    if (req.ip === '127.0.0.1') {
        res.status(200).send(env.parsed.flag)
    } else res.status(403).end('not so simple');
});

app.listen(80, "0.0.0.0");