const cp = require('child_process')
const ip = require('ip')
const url = require('url');
const {docker} = require("./docker.js")

const checkip = function (value) {
    let pattern = /^\d{1,3}(\.\d{1,3}){3}$/;
    if (!pattern.exec(value))
        return false;
    let ary = value.split('.');
    for(let key in ary)
    {
        if (parseInt(ary[key]) > 255)
            return false;
    }
    return true ;
}

const dnslookup = function(s) {
    if (typeof(s) == 'string' && !s.match(/[^\w-.]/)) {
        let query = '';
        try {
            query = JSON.parse(cp.execSync(`curl http://ip-api.com/json/${s}`)).query
        } catch (e) {
            return 'wrong'
        }
        return checkip(query) ? query : 'wrong'
    } else return 'wrong'
}

const check = function(s) {
    if (!typeof (s) == 'string' || !s.match(/^http\:\/\//))
        return false

    let blacklist = ['wrong', '127.', 'local', '@', 'flag']
    let host, port, dns;

    host = url.parse(s).hostname
    port = url.parse(s).port
    if ( host == null || port == null)
        return false

    dns = dnslookup(host);
    if ( ip.isPrivate(dns) || dns != docker.ip || ['80','8080'].includes(port) )
        return false

    for (let i = 0; i < blacklist.length; i++)
    {
        let regex = new RegExp(blacklist[i], 'i');
        try {
            if (ip.fromLong(s.replace(/[^\d]/g,'').substr(0,10)).match(regex))
                return false
        } catch (e) {}
        if (s.match(regex))
            return false
    }
    return true
}

exports.check = check