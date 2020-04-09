# 標準ライブラリ

# 外部ライブラリ
import tornado.web
from tornado.options import define, options

# 自作ライブラリ


class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')
