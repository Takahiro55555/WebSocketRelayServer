"""
Tornadoのオプション設定をまとめておくファイル

NOTE: このファイルは 'main.py' と同じ階層のディレクトリに置くこと
"""

import os
import secrets

import tornado.options
from tornado.options import define, options


define("port", default=80, type=int, help="port to listen on")
define("debug", default=False, type=bool, help="enable debug mode")
define("admin_email", secrets.token_urlsafe()+"@example.com",
       help="Default email is random string, so you must set 'admin_email' by hand when you use admin functions.")
define("admin_password", secrets.token_urlsafe(),
       help="Default password is random string, so you must set 'admin_password' by hand when you use admin functions.")
define("hashed_admin_password", secrets.token_urlsafe(),
       help="hashed admin passowrd")

# DBファイル名とパスの設定
define("db_name", "RelayServer.sqlite3", help="sqlite file name")
define("db_path", os.path.join(
    os.path.dirname(__file__), options.db_name), help="sqlite file path")

# 設定ファイル名とパスの設定
define("config_file_name", "server.conf", help="config file name")
define("config_file_path", os.path.join(
    os.path.dirname(__file__), options.config_file_name), help="config file path")

define("sql_echo", default=False,
       help="If True, the SQLAlchemy Engine will log all statements")
define("tokens_lifespan_sec", default=7776000,
       help="default lifespan: 7776000sec (90days)")
define("db_uri_type", default="sqlite:///",
       help="DB name, such as 'sqlite:///' and 'mysql:///'. This option using as 'sqlite:///<file_path>'")
define("relays_lifespan_sec", default=7776000,
       help="default lifespan: 7776000sec (90days)")

# NOTE: 設定ファイル名やパスをコマンドラインから受け取ることがあるため、はじめにコマンドラインのオプションを読み込む
tornado.options.parse_command_line(final=False)
options.config_file_path = os.path.join(
    os.path.dirname(__file__), options.config_file_name)
# NOTE: 設定ファイルのオプションを読み込む
tornado.options.parse_config_file(options.config_file_path, final=False)
# NOTE: コマンドラインの設定を優先するため再度コマンドラインのオプションを読み込む
tornado.options.parse_command_line()
options.db_path = os.path.join(os.path.dirname(__file__), options.db_name)
