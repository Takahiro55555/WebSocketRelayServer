# TODO: クラス名とファイル名を一致させる
#       コネクション切断時のステータスコードをきちんと考える

import datetime
import secrets

# 外部ライブラリ
from tornado.options import define, options


class RelayPaire:
    """中継のために必要なデータ及びオブジェクト、関数を持つ

    Returns
    -------
    None
    """

    def __init__(self, connection_limit=2, client_id_nbytes=32, log_func=print):
        self.__connection_limit = connection_limit
        self.__client_id_nbytes = client_id_nbytes
        self.__ws_clients = dict()
        self.__log_func = log_func
        self.__log_func("New realay paire created")

    def relay(self, ws_con, public_msg={}, echo=False):
        for key in self.__ws_clients:
            ws_con_tmp = self.__ws_clients[key]["ws_con"]
            if (not echo) and (ws_con == ws_con_tmp):
                continue
            if ws_con_tmp == None:
                continue
            ws_con_tmp.write_message(public_msg)

    def connect_client(self, ws_con, msg={}):
        # 接続上限数の確認
        valid_clients_num = 0
        is_duplicate = False
        for _,v in self.__ws_clients.items():
            if not v["is_exited"]:
                if v['ws_con'] == ws_con:
                    is_duplicate = True
                    break
                valid_clients_num += 1
        if is_duplicate:
            response = dict()
            response["header"] = dict(
                client_id = None
            )
            response["errors"] = [dict(
                field="header.cmd",
                code="duplicate_connection",
                message="Already connected"
            )]
            ws_con.write_message(response)
            return
        if valid_clients_num >= self.__connection_limit:
            ws_con.close(code=5000, reason="This relay has already reached its connection limit")
            return
        # クライアントIDを生成し、クライアントIDをキーにしてWebSocket接続オブジェクトを格納する
        # NOTE: RelayPairオブジェクト内でのクライアントIDの重複の可能性を排除するためにプレフィックスを付加
        client_id = "%d-%s" % (len(self.__ws_clients), secrets.token_urlsafe(nbytes=self.__client_id_nbytes))
        self.__ws_clients[client_id] = dict(ws_con=ws_con, is_exited=False)
        ws_con.client_id = client_id  # WebSocketオブジェクトにクライアントIDを設定
        # レスポンスの作成
        response_header = dict(
            client_id = client_id
        )
        response = dict(
            header = response_header,
            contents = None
        )
        ws_con.write_message(response)

    def reconnect_client(self, ws_con, client_id):
        """
        何らかの原因によりWebSocketが切断された際に再接続するための関数
        """
        # 送られてきたクライアントIDが有効なものかどうかを確認
        if not self.__is_valid_client_id(client_id):
            ws_con.close(code=5000, reason="This client id is not valid")
            return
        if self.is_autholized_connecton(ws_con):
            response = dict()
            response["header"] = dict(
                client_id = None
            )
            response["errors"] = [dict(
                field="header.cmd",
                code="duplicate_connection",
                message="Already connected by this connection"
            )]
            ws_con.write_message(response)
            return
        if self.__is_connectiong_client_id(client_id):
            ws_con.close(code=5000, reason='Connection already exists by this client_id')
            return
        self.__ws_clients[client_id]["ws_con"] = ws_con
        ws_con.client_id = client_id
        response = dict(
            header = dict(
                status = 'ok'
            ),
            contents = None
        )
        ws_con.write_message(response)

    def ws_con_close(self, ws_con):
        """
        当該WebSocketを閉じる際に実行するべき関数。
        割り当てられたクライアントIDで認証することによって再接続することはできる。
        """
        for key in self.__ws_clients:
            ws_con_tmp = self.__ws_clients[key]["ws_con"]
            if ws_con_tmp == ws_con:
                self.__ws_clients[key]["ws_con"] = None
                return

        # そもそも登録されていなかった場合
        ws_con.close(code=5000, reason="Not registered to this relay")

    def exit(self, ws_con, private_msg={}):
        """
        当該WebSocketを閉じ、退出フラグを立てる
        割り当てられたクライアントIDを使用しての再接続も不可能
        """
        for key in self.__ws_clients:
            ws_con_tmp = self.__ws_clients[key]["ws_con"]
            if ws_con_tmp == ws_con:
                ws_con_tmp.write_message(private_msg)
                ws_con_tmp.close()
                self.__ws_clients[key]["ws_con"] = None
                self.__ws_clients[key]["is_exited"] = True
                break

    def is_autholized_connecton(self, ws_con):
        for _,v in self.__ws_clients.items():
            if v['ws_con'] is ws_con:
                return True
        return False
    
    def is_host_connection(self, ws_con):
        """
        将来的にホストを識別するようになった時のための関数
        """
        return self.is_autholized_connecton(ws_con)

    def __is_valid_client_id(self, client_id):
        """
        クライアントIDがリレー中に存在し、退出フラグが立っていないことを確認
        """
        if not client_id in self.__ws_clients:
            return False
        if self.__ws_clients[client_id]["is_exited"]:
            return False
        return True

    def __is_connectiong_client_id(self, client_id):
        """
        当該クライアントIDのクライアントが接続中であることを確認
        """
        if not self.__is_valid_client_id(client_id):
            return False
        if self.__ws_clients[client_id]["ws_con"] == None:
            return False
        return True

    def __del__(self):
        print('deleting')
        for key in self.__ws_clients:
            ws_con_tmp = self.__ws_clients[key]["ws_con"]
            if ws_con_tmp == None:
                continue
            ws_con_tmp.close(code=5000, reason="This relay is deleted")
