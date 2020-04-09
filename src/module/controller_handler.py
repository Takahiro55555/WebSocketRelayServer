# 標準ライブラリ

# 外部ライブラリ
import tornado.web
from tornado.options import define, options

# 自作ライブラリ


class ControllerHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('controller.html')
