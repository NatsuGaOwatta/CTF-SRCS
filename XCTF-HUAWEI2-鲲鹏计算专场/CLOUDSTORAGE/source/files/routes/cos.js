module.exports = function(app, md5, docker) {

    const multer  = require('multer');
    const fs = require('fs');
    const path = require('path')
    const upload = multer({dest: '/tmp/upload_tmp/'});

    app.get('/', function(req, res){
        res.render("upload")
    });

    app.post('/upload', upload.any(), function(req, res){
        if (!req.files[0]) {
            res.send( JSON.stringify({"code" : "-1", "message" : "you are not allowed"}) )
            return;
        }

        let filename = md5(req.files[0].originalname + req.files[0].size + req.ip)
        let des_file = "static/upload/" + filename;
        if (fs.existsSync(des_file)) {
            res.end( JSON.stringify( {"code" : "-1", "message" : "already existed!"} ) )
            return
        }

        fs.readFile( req.files[0].path, function (err, data) {
            fs.writeFile(des_file, data, function (err) {
                let response;
                if (err) {
                    response = {"code" : "-1", "message" : "err!"}
                } else {
                    response = {
                        code: '0',
                        filepath: des_file,
                        message: `http://${docker.host}:${docker.port}/download/${filename}`
                    };
                    req.session.files.push(filename)
                }
                res.end( JSON.stringify( response ) );
            });
        });
    });

    app.get('/download/:file', (req, res) => {
        let filename = req.url.split("/download/").slice(1,req.url.split("/download/").length).join("")
        if (filename.indexOf('..') !== -1) {
            res.end( JSON.stringify( {"code" : "-1", "message" : "my dear dalao pls stop hacking me"} ) )
            return
        }
        let file = path.join(__dirname, `../static/upload/${filename}`)
        if (!fs.existsSync(file)) {
            res.status(404).end( JSON.stringify( {"code" : "-1", "message" : "404 not found"} ) )
            return
        }
        res.download(file)
    })

}