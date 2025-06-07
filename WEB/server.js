const express = require('express');
const http = require('http');
const path = require('path');
const fs = require('fs');
const bodyParser = require('body-parser');
const querystring = require('querystring');
const ejs = require('ejs');
const jsonfile = require('jsonfile');
const multer = require('multer');
const session = require('express-session');
let varchar, security, hex, compiler;
try{
    varchar = require('./config/env-variables');
    security = require('./config/security');
    hex = require('./config/hex');
    compiler = require('./config/compiler');
}catch(e){
    varchar = require('./config/env-variables.ts');
    security = require('./config/security.ts');
    hex = require('./config/hex.ts');
    compiler = require('./config/compiler.ts');
}
require('./public/App.test.js');
require('dotenv').config();

class WEB{
    constructor(port){
        this.active = true;
        this.port = port;
        this.filename = path.basename(__filename);
        this.appInfo = jsonfile.readFileSync('./public/manifest.json');
        this.isVerified = false;
        this.originalUrl = false;
    }
}

const app = express();
let server = http.createServer(app);
const PORT = process.env.PORT || 5000;
const AppName = "DEEP FAKE DETECTION";
let web = new WEB(PORT);
let memory;
let API_LINK = '';
let single_img_bin = [];
let multiple_img_bin = [];

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use('/assets',express.static(path.join(__dirname,'assets')));
app.use('/config',express.static(path.join(__dirname,'config')));
app.use('/images',express.static(path.join(__dirname,'images')));
app.use('/public',express.static(path.join(__dirname,'public')));

app.use(bodyParser.json({ limit: '1mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '1mb' }));
app.use(
    session({
        secret: security.sessionKey(),
        resave: false,
        saveUninitialized: true,
    })
);

const storage = multer.memoryStorage();
const upload = multer({storage: storage});

app.use((req, res, next) => {
    try{
        const url = req.originalUrl;
        const query = url.split('?')[1];
        const baseURL = req.protocol + '://' + req.get('host');
        const params = new URL(url, baseURL).searchParams;
        const public_key = varchar.duplex;
        // if(params.has('encode')){
        //     if(query!=undefined){
        //         const decodedUrl = security.decodedURI(query.replace('encode=',''), public_key);
        //         req.url = `${url.split('?')[0]}?${decodedUrl}`;
        //         req.query = querystring.parse(decodedUrl);
        //     }
        // }else{
        //     if(query!=undefined){
        //         const encodedUrl = security.encodedURI(query, public_key);
        //         req.url = `${url}?encode=${encodedUrl}`;
        //         req.query = querystring.parse(encodedUrl);
        //     }
        // }
        if(security.secure_access(req.originalUrl)) return next();
        const my_browser = security.browser(req.headers);
        if(!security.validBrowser([my_browser[0], my_browser[1].split('.')[0]*1], varchar.browser_data) && hex.isHosted(req)){
            res.status(422).render('notfound',{error: 422, message: "Your browser is outdated and may not support certain features. Please upgrade to a modern browser."});
        }
        if(!hex.isHosted(req)){
            API_LINK = 'http://127.0.0.1:8000'
        }else{
            API_LINK = 'https://chsapi.vercel.app';
        }
        if(security.nonAuthPage(req.path) || !hex.isHosted(req)){
            return next();
        }
        next(); // for remove security check point
        setTimeout(()=>{
            if(memory!=undefined){
                if(params.has('autherize')){
                    if(security.decodedURI(params.get('autherize'), public_key) < 30*60*1000){
                        return next();
                    }
                }
                try{
                    const last_verified = (new Date().getTime()) - memory.find(function (element){return element.id == 0})==undefined?0:memory.find(function (element){return element.id == 0}).time;
                    if(last_verified >= 30*60*1000){
                        web.originalUrl = req.originalUrl;
                        return res.redirect('/auth?=0');
                    }
                }catch(e){
                    return next();
                }
            }else{
                web.originalUrl = req.originalUrl;
                return res.redirect('/auth');
            }
            next();
        },1500);
    }catch(e){
        res.status(401).render('notfound',{error: 401, message: "Unauthorize entry not allow, check the source or report it", statement: e});
    }
});

const promises = [
    ejs.renderFile('./views/header.ejs')
];


app.get('/', (req, res) => {
    Promise.all(promises).then(([header]) => {
        res.status(200).render('index',{header});
    });
});

app.get('/varchar', async (req, res) => {
    const navi = req.headers;
    res.status(200).json({varchar, navi, hex: {
        vaildFiles: hex.vaildFiles.toString(),
        dragAndSort: hex.dragAndSort.toString(),
        trafficAnalyser: hex.trafficAnalyser.toString(),
        popularityTest: hex.popularityTest.toString(),
        singlePartsAPI: hex.singlePartsAPI.toString(),
        MultiPartsAPI: hex.MultiPartsAPI.toString(),
        alphaCall: hex.alphaCall.toString(),
        alphaLink: API_LINK
    }, security: {
        getCaptcha: security.getCaptcha.toString(),
        generateImageCaptcha: security.generateImageCaptcha.toString(),
        generateCaptcha: security.generateCaptcha.toString()
    }});
});


app.get('/nonAPIHost', (req, res) => {
    const error_log = web.appInfo['error_log'];
    const error = hex.pyerrorinfo(error_log, 23);
    res.status(200).json({error});
});


app.post('/memory', (req, res) => {
    const { dbdata } = req.body;
    memory = dbdata;
    res.status(200).json({'ack': 'Remember user, Permit to route'});
});


app.post('/load/single', (req, res) => {
    if(req.body.index <= req.body.limit && req.body.index > 0){
        single_img_bin.push(req.body.img);
        res.status(200).json({"ack": req.body.index, "time": (new Date).getTime()});
    }else{
        res.status(200).json({"error": 400, "message": "UploadException: Upload failed due to wrong argument value pass from frontend side"});
    }
});

app.post('/load/multiple', (req, res) => {
    if(req.body.no <= req.body.total_no && req.body.no >= 0){
        if(req.body.index <= req.body.limit && req.body.index >= 0){
            if(!multiple_img_bin[req.body.no*1]){
                multiple_img_bin[req.body.no*1] = [];
            }
            multiple_img_bin[req.body.no*1][req.body.index*1] = req.body.img;
            res.status(200).json({"ack": [req.body.no, req.body.index], "time": (new Date).getTime()});
        }else{
            res.status(200).json({"error": 400, "message": "UploadException: Upload failed due to wrong argument value pass from frontend side"});
        }
    }
});


app.get('/index', (req, res) => {
    res.redirect('/');
});

app.post('/index/process', upload.single('file'), async (req, res) => {
    try{
        const extension = req.body.extension;
        let mediaData;
        let limit, heatmap='false';
        if(req.body.load!='true'){
            mediaData = req.body.imageData;
            limit = 2;
        }else{
            mediaData = hex.mergeListToString(single_img_bin);
            limit = single_img_bin.length;
        }
        if(req.body?.heatmap){
            if(req.body.heatmap!='true'){
                heatmap = 'false';
            }else{
                heatmap = req.body.heatmap;
            }
        }
        await hex.singlePartsAPI(`${API_LINK}/load/single`, mediaData, limit).then((connection) => {
            if(web.noise_detect(connection)) return web.handle_error(res, connection);
            hex.chsAPI(`${API_LINK}/api/dfdScanner`, {
                ext: extension,
                media: '',
                load: 'true',
                key: varchar.API_KEY,
                heatmap: heatmap
            }).then((result) => {
                single_img_bin = [];
                console.log(result);
                res.status(200).json(result);
            });
        }).catch((error) => {
            console.log("Error sending parts:", error);
        });
    }catch(e){
        console.log(e);
        res.status(403).render('notfound',{error: 403, message: "Failed to process most recent task, Try again later"});
    }
});

WEB.prototype.noise_detect = function(data){
    try{
        return hex.pyerrorscanner(data);
    }catch(e){
        console.log("Error found to detect noise\n",e);
    }
}
WEB.prototype.handle_error = function(res, code){
    try{
        const error_log = web.appInfo['error_log'];
        const error = hex.pyerrorinfo(error_log, code);
        res.status(200).json({error});
        return;
    }catch(e){
        console.log("Error found to handle error\n",e);
    }
}
WEB.prototype.encryptMedia = async function(media){
    try{
        let encrypted_body = await security.substitutionEncoder(media, varchar.API_KEY);
        let encrypted_media = 'encrypted::'+encrypted_body;
        console.log("server side:  "+encrypted_media.slice(0, 40));
        return encrypted_media;
    }catch(e){
        console.log("Error to encrypt the provided media!\n",e);
        return media;
    }
}

WEB.prototype.decryptMedia = async function(media){
    try{
        let data = media.split('encrypted::')[1];
        let plain_body = await security.substitutionDecoder(data, varchar.API_KEY);
        let plain_media = plain_body;
        console.log("server side:  "+plain_media.slice(0, 40));
        return plain_media;
    }catch(e){
        console.log("Error to encrypt the provided media!\n",e);
        return media;
    }
}

app.get('*', (req, res) => {
    res.status(404).render('notfound',{error: 404, message: "Sorry an error has occured, Requested page not found, check the source or report it!"});
});

server.listen(PORT, (err) => {
    if(err) console.log("Oops an error occure:  "+err);
    console.log(`Compiled successfully!\n\nYou can now view \x1b[33m./${path.basename(__filename)}\x1b[0m in the browser.`);
    console.info(`\thttp://localhost:${PORT}`);
    console.log("\n\x1b[32mNode web compiled!\x1b[0m \n");
});

