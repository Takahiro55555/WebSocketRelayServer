# 標準ライブラリ

# 外部ライブラリ
import tornado.web
from tornado.options import define, options

# 自作ライブラリ

# TODO: このクラスと、HTMLテンプレートは削除
#       今後このサーバでは、Webページの提供は行わない予定のため

class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')
