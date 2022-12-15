### Startup

```bash
bash run.sh
# open 127.0.0.1:12001
```

From: https://github.com/tonghuaroot/My-CTF-Web-Challenges/tree/main/LINE%20CTF%202021

Thanks @童话 for backup source code.

> If the default python bin of your system is **python2**, when you run the above command will get the error: "SyntaxError: invalid syntax", change the **python** to **python3** to solve it.

### Changed

为了适配国内网络环境修改了 `public/Dockerfile` 和 `internal/Dockerfile` 中的如下内容:

```dockerfile
# RUN sed -i 's/archive.ubuntu.com/ftp.daumkakao.com/g' /etc/apt/sources.list
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list
```

因为在 `internal/Dockerfile` 中新建了一个用户组 web 并添加了一个用户来跑 node 服务，在最后 `npm start` 的时候，我这里的环境有如下问题：

```text
linectf_babyweb_internal | > start
linectf_babyweb_internal | > nodemon --exec babel-node server.js
linectf_babyweb_internal | 
linectf_babyweb_internal | [nodemon] 2.0.7
linectf_babyweb_internal | [nodemon] to restart at any time, enter `rs`
linectf_babyweb_internal | [nodemon] watching path(s): *.*
linectf_babyweb_internal | [nodemon] watching extensions: js,mjs,json
linectf_babyweb_internal | [nodemon] starting `babel-node server.js`
linectf_babyweb_internal | Browserslist: caniuse-lite is outdated. Please run:
linectf_babyweb_internal | npx browserslist@latest --update-db
linectf_babyweb_internal | 
linectf_babyweb_internal | Why you should do it regularly:
linectf_babyweb_internal | https://github.com/browserslist/browserslist#browsers-data-updating
linectf_babyweb_internal | npm ERR! code EACCES
linectf_babyweb_internal | npm ERR! syscall mkdir
linectf_babyweb_internal | npm ERR! path /home/web
linectf_babyweb_internal | npm ERR! errno -13
linectf_babyweb_internal | npm ERR! Error: EACCES: permission denied, mkdir '/home/web'
linectf_babyweb_internal | npm ERR!  [Error: EACCES: permission denied, mkdir '/home/web'] {
linectf_babyweb_internal | npm ERR!   errno: -13,
linectf_babyweb_internal | npm ERR!   code: 'EACCES',
linectf_babyweb_internal | npm ERR!   syscall: 'mkdir',
linectf_babyweb_internal | npm ERR!   path: '/home/web'
linectf_babyweb_internal | npm ERR! }
linectf_babyweb_internal | npm ERR! 
linectf_babyweb_internal | npm ERR! The operation was rejected by your operating system.
linectf_babyweb_internal | npm ERR! It is likely you do not have the permissions to access this file as the current user
linectf_babyweb_internal | npm ERR! 
linectf_babyweb_internal | npm ERR! If you believe this might be a permissions issue, please double-check the
linectf_babyweb_internal | npm ERR! permissions of the file and its containing directories, or try running
linectf_babyweb_internal | npm ERR! the command again as root/Administrator.
linectf_babyweb_internal | 
linectf_babyweb_internal | npm ERR! Log files were not written due to an error writing to the directory: /home/web/.npm/_logs
linectf_babyweb_internal | npm ERR! You can rerun the command with `--loglevel=verbose` to see the logs in your terminal
linectf_babyweb_internal exited with code 243
```

权限好像出了点问题，我也懒得排查问题了，直接在 Dockerfile 中把 `USER web` 这行命令注释掉就能运行了。

另外如果要自己生成证书用于测试，注意一个小坑：https://bugs.python.org/issue34440。然后如果 python 版本高了的话，运行 public 服务 import hyper 时还要注意另一个小坑：https://stackoverflow.com/questions/72032032/importerror-cannot-import-name-iterable-from-collections-in-python
