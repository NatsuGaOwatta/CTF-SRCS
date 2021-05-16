const env = require('dotenv').config();
const docker = {
    'ip' : env.parsed.ip || '121.37.175.154',
    'port' : env.parsed.port || '8000',
    'host' : env.parsed.host || 'cloudstorage.xctf.org.cn'
}

exports.docker = docker