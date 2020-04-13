# 標準ライブラリ
import os
import logging
import secrets
import ssl

# 外部ライブラリ
import bcrypt

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.escape
import tornado.options
from tornado.options import define, options

# 自作モジュール
from module.password_hash import hash_password, check_password

# 最初に以下のモジュールを読みこまないとその他のモジュールでオプションが見つからずにエラーが発生する
from tornado_options import *
from module.tables import create_tables
from module.root_handler import RootHandler
from module.controller_handler import ControllerHandler
from module.account_handler import AccountHandler
from module.token_handler import TokenHandler
from module.relay_handler import RelayHandler
from module.ws_relay_handler import WsRelayHandler


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", RootHandler),
            (r"/controller", ControllerHandler),
            (r"/api/v1/accounts", AccountHandler),
            (r"/api/v1/tokens", TokenHandler),
            (r"/api/v1/relays", RelayHandler),
            (r"/ws/v1/relays/([0-9a-zA-Z]+\-[0-9a-zA-Z]+)", WsRelayHandler),
        ]

        settings = dict(
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            autoescape="xhtml_escape",
            debug=options.debug
        )

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    # 設定ファイルや、コマンドラインからハッシュ化されたパスワードが渡されていない場合
    if options.hashed_admin_password == None:
        options.hashed_admin_password = hash_password(options.admin_password)
    options.admin_password = None

    # テーブルを作成する
    create_tables()

    app = Application()
    # NOTE: HTTPServerではAutoreloadモードが使えない
    #       Ref: https://www.tornadoweb.org/en/stable/guide/running.html
    #       > Autoreload mode is not compatible with the multi-process mode of HTTPServer.
    if options.debug:
        app.listen(options.port)
    else:
        if options.use_ssl:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(options.ssl_crt_file_path, options.ssl_key_file_path)
            server = tornado.httpserver.HTTPServer(app, ssl_options=ssl_ctx)
        else:
            server = tornado.httpserver.HTTPServer(app)
        server.bind(options.port)
        # NOTE: マルチプロセスにすると、同一のリレー(WebSocket)が別々のプロセスで生成されてしまい、
        #       上手く転送をすることができなくなってしまう。
        server.start(1)  # プロセス数を設定する
    tornado.ioloop.IOLoop.instance().start()
