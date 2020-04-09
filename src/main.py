# 標準ライブラリ
import os
import logging
import secrets

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
    salt = bcrypt.gensalt(rounds=10, prefix=b"2a")
    options.hashed_admin_password = bcrypt.hashpw(
        options.admin_password.encode(), salt).decode()
    options.admin_password = None

    # テーブルを作成する
    create_tables()

    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
