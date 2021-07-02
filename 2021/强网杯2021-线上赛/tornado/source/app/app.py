import tornado.ioloop
import tornado.web
import tornado.options
import pymysql
import os
import re

settings = {
    "static_path": os.path.join(os.getcwd(), "static"),
    "cookie_secret": "b93a9960-bfc0-11eb-b600-002b677144e0",
}

db_username = 'qwb'
db_password = 'qwb123456'


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        if user and user == b'admin':
            self.redirect("/admin.php", permanent=True)
            return
        self.render("index.html")


class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        if not username or not password:
            if not self.get_secure_cookie("user"):
                self.finish("<script>alert(`please input your password and username`);history.go(-1);</script>")
                return
            elif self.get_secure_cookie("user") == b'admin':
                self.redirect("/admin.php", permanent=True)
            else :
                self.redirect("/", permanent=True)
        else:
            conn=pymysql.connect('localhost',db_username,db_password,'qwb')
            cursor = conn.cursor()
            cursor.execute("SELECT * from qwbtttaaab111e where qwbqwbqwbuser=%s and qwbqwbqwbpass=%s" , [username, password])
            results = cursor.fetchall()
            if len(results) != 0 :
                if results[0][1] == 'admin' : 
                    self.set_secure_cookie('user','admin')
                    cursor.close()
                    conn.commit()
                    conn.close()
                    self.redirect("/admin.php", permanent=True)
                    return
                else :
                    cursor.close()
                    conn.commit()
                    conn.close()
                    self.finish("<script>alert(`login success, but only admin can get flag`);history.go(-1);</script>")
                    return
            else:
                cursor.close()
                conn.commit()
                conn.close()
                self.finish("<script>alert(`your username or password is error`);history.go(-1);</script>")
                return


class RegisterHandler(tornado.web.RequestHandler):
    def get(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        word_bans = ['table', 'col', "sys", 'union', 'inno', 'like', 'regexp']
        bans = ["\"", "#", "%", "&", ";", "<", "=", ">", "\\", "^", "`", "|" , "*", '--', '+']
        for ban in word_bans:
            if re.search(ban, username, re.IGNORECASE):
                self.finish("<script>alert(`error`);history.go(-1);</script>")
                return
        for ban in bans:
            if ban in username:
                self.finish("<script>alert(`error`);history.go(-1);</script>")
                return
        if not username or not password:
            self.render('register.html')
            return
        else:
            if username == 'admin':
                self.render('register.html')
                return
            conn=pymysql.connect('localhost',db_username,db_password,'qwb')
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT qwbqwbqwbuser,qwbqwbqwbpass from qwbtttaaab111e where qwbqwbqwbuser='%s'" % (username))
                results = cursor.fetchall()
                if len(results) != 0:
                    self.finish("<script>alert(`this username had been used`);history.go(-1);</script>")
                    conn.commit()
                    conn.close()
                    return
            except:
                conn.commit()
                conn.close()
                self.finish("<script>alert(`error`);history.go(-1);</script>")
                return
            try:
                cursor.execute("insert into qwbtttaaab111e (qwbqwbqwbuser, qwbqwbqwbpass) values(%s, %s)", [username, password])
                conn.commit()
                conn.close()
                self.finish("<script>alert(`success`);location.href='/index.php';</script>")
                return
            except:
                conn.rollback()
                conn.close()
                self.finish("<script>alert(`error`);history.go(-1);</script>")
                return


class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect("/", permanent=True)


class AdminHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        if not user or user != b'admin':
            self.redirect("/index.php", permanent=True)
            return
        self.render("admin.html")

class ImageHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        image_name = self.get_argument('qwb_image_name', 'header.jpeg')
        if not image_name:
            self.redirect("/", permanent=True)
            return
        elif not user or user != b'admin':
            self.redirect("/", permanent=True)
            return
        else:
            if image_name.endswith(".py") or 'flag' in image_name or '..' in image_name:
                self.finish("nonono, you can't read it.")
                return
            image_name = os.path.join("/qwb/app/" + "/image", image_name)
            with open(image_name, 'rb') as f:
                img = f.read()
            self.set_header("Content-Type","image/jpeg")
            self.finish(img)
            return


class SecretHandler(tornado.web.RequestHandler):
    def get(self):
        if(len(tornado.web.RequestHandler._template_loaders)):
            for i in tornado.web.RequestHandler._template_loaders:
                tornado.web.RequestHandler._template_loaders[i].reset()
            #tornado.web.RequestHandler._template_loaders[''].reset()   #清除静态页面缓存
        msg = self.get_argument('congratulations', 'oh! you find it')
        black_func = ['eval', 'os', 'chr', 'class', 'compile', 'dir', 'exec', 'filter', 'attr', 'globals', 'help', 'input', 'local', 'memoryview', 'open', 'print', 'property', 'reload', 'object', 'reduce', 'repr', 'method', 'super', 'vars']
        black_symbol = ["__", "'", '"', "$", "*", '{{']
        black_keyword = ['or', 'and', 'while']
        black_rce = ['render', 'module', 'include', 'raw']
        bans = black_func + black_symbol + black_keyword + black_rce
        for ban in bans:
            if ban in msg:
                self.finish("bad hack,go out!")
                return
        with open("/qwb/app/congratulations.html", 'w') as f:
            f.write("""<html><head><title>congratulations</title></head><body><script type="text/javascript">alert("%s");location.href='/admin.php';</script></body></html>\n""" % msg)
            f.flush()
        self.render("congratulations.html")
        if(tornado.web.RequestHandler._template_loaders):
            for i in tornado.web.RequestHandler._template_loaders:
                tornado.web.RequestHandler._template_loaders[i].reset()
            #tornado.web.RequestHandler._template_loaders[''].reset()   #清除静态页面缓存

def make_app():
    return tornado.web.Application([
        (r"/index.php", MainHandler),
        (r"/login.php", LoginHandler),
        (r"/logout.php", LogoutHandler),
        (r"/register.php", RegisterHandler),
        (r"/admin.php", AdminHandler),
        (r"/qwbimage.php", ImageHandler),
        (r"/good_job_my_ctfer.php", SecretHandler),
        (r"/", MainHandler),
    ], **settings)


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
    print('start')