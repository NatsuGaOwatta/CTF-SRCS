module.exports = function(app, md5, docker) {

    const request = require('request');
    const cp = require('child_process')
    const { check } = require("./utils")

    app.get('/admin',  async (req, res) => {
        let host = `http://${docker.host}:${docker.port}/`
        let html = ""
        await req.session.files.forEach((file) => {
            html += `<a href ='javascript:doPost("/admin", {"fileurl":"${host}download/${file}"})' target=''>${file}</a><br>` + "\n\n"
        })
        res.render("admin", {"files" : html})
    })

    app.post('/admin', (req, res) => {
        if ( !req.body.fileurl || !check(req.body.fileurl) ) {
            res.end("Invalid file link")
            return
        }
        let file = req.body.fileurl;

        //dont DOS attack, i will sleep before request
        cp.execSync('sleep 5')

        let options = {url : file, timeout : 3000}
        request.get(options ,(error, httpResponse, body) => {
            if (!error) {
                res.set({"Content-Type" : "text/html; charset=utf-8"})
                res.render("check", {"body" : body})
            } else {
                res.end( JSON.stringify({"code" : "-1", "message" : error.toString()}) )
            }
        });
    })

}