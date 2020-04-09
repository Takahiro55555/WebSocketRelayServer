# 標準ライブラリ
import json
from datetime import datetime, timedelta

# 外部ライブラリ
import bcrypt

import tornado.websocket
from tornado.options import define, options

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy.orm.exc

# 自作モジュール
from module.tables import Relay
from module.relay_pair import RelayPaire

# TODO: コネクション切断時のエラーコードをきちんと考える
#       現状、すべて5000を返す


class WsRelayHandler(tornado.websocket.WebSocketHandler):
    relay_paires = dict()
    engine = create_engine(
        options.db_uri_type + options.db_path, echo=options.sql_echo)

    def check_origin(self, origin):
        """
        デバッグ用に同一生成元ポリシーを無くす
        """
        return True

    def open(self, relay):
        # TODO: リレーパID及びスワードの検証をすること
        relay_id, raw_relay_password = relay.split('-')
        self.__relay_id = relay_id
        try:
            is_valid_relay = self.__is_valid(relay_id, raw_relay_password)
        except sqlalchemy.orm.exc.NoResultFound:
            self.close(code=5000, reason="Database error occurred")
            del raw_relay_password
            return

        if not is_valid_relay:
            self.close(code=5000, reason="Invalid relay")
            del raw_relay_password
            return
        
        if self.__is_expired(relay_id):
            self.close(code=5000, reason="This relay is already expired")
            del raw_relay_password
            return
        
        if not relay_id in self.relay_paires:
            self.relay_paires[relay_id] = RelayPaire()

    def on_message(self, message):
        try:
            msg = json.loads(message)
        except json.JSONDecodeError:
            self.close(code=5000, reason='Invalid format message')
            return

        if not 'header' in msg:
            # TODO: ここにエラー処理を入れる
            return
        msg_header = msg['header']
        response_contents = None
        if 'contents' in msg:
            # NOTE: 中継するべきデータ
            response_contents = msg['contents']
        
        if not 'cmd' in msg_header:
            # TODO: ここにエラー処理を入れる
            print('Invalid message header')
            return

        command = msg_header['cmd']

        if command == 'connect':
            self.relay_paires[self.__relay_id].connect_client(self)
            return

        if command == 'reconnect':
            if self.relay_paires[self.__relay_id].is_autholized_connecton(self):
                response = dict()
                response["header"] = None
                response["errors"] = [dict(
                    field="header.cmd",
                    code="duplicate_connection",
                    message="Already connected"
                )]
                self.write_message(json.dumps(response))
                return
            if not 'client_id' in msg_header:
                self.close(code=5000, reason="Too few key")
                return
            self.relay_paires[self.__relay_id].reconnect_client(self, msg_header['client_id'])
            return
        
        #### 以下の処理は、認証済みのコネクションでないと実行できない ####
        if not self.relay_paires[self.__relay_id].is_autholized_connecton(self):
            self.close(code=5000, reason="This connection is not authorized, please authorize by using [connect] or [reconnect] command")
            return

        if command == 'relay':
            response = dict(
                header = dict(),
                contents = response_contents
            )
            self.relay_paires[self.__relay_id].relay(self, response)
            return

        if command == 'close':
            self.relay_paires[self.__relay_id].ws_con_close(self)
            return

        if command == 'exit':
            self.relay_paires[self.__relay_id].exit(self)
            return

        if command == 'delete':
            if not self.relay_paires[self.__relay_id].is_host_connection(self):
                response = dict()
                response["header"] = None
                response["errors"] = [dict(
                    field="header.cmd",
                    code="permission_denied",
                    message="This operation is not permitted"
                )]
                self.write_message(json.dumps(response))
                return
            print(self.__relay_id)
            del self.relay_paires[self.__relay_id]
            try:
                session = sessionmaker(bind=self.engine)()
                relay = session.query(Relay).filter(Relay.relay_id == self.__relay_id).one()
                relay.is_valid = False
                session.commit()
                session.close()
            except sqlalchemy.orm.exc.NoResultFound:
                self.close(code=5000, reason="Database error occurred")
                print("Database error occurred")
                return
            print('deleted')
            return

    def on_close(self):
        if self.__relay_id in self.relay_paires:
            self.relay_paires[self.__relay_id].ws_con_close(self)
        print('WebSocket closed')
    
    def __is_valid(self, relay_id, raw_relay_password):
        # DBからリレー情報を照会、取得
        session = sessionmaker(bind=self.engine)()
        result = session.query(Relay.hashed_relay_password, Relay.relay_id).filter(
                Relay.relay_id == relay_id, Relay.is_valid).one_or_none()

        # リレーが存在しなかった場合
        if result == None:
            del raw_relay_password
            return False
        hashed_relay_password = result[0]
        relay_id = result[1]

        # 入力されたリレーの有効性パスワードの有効性を確認
        if not self.__check_password(raw_relay_password, hashed_relay_password):
            del raw_relay_password
            return False
        del raw_relay_password
        return True
    
    def __is_expired(self, relay_id):
        # DBからリレー情報を照会、取得
        session = sessionmaker(bind=self.engine)()
        result = session.query(Relay.created_at).filter(
                Relay.relay_id == relay_id, Relay.is_valid).one_or_none()
        
        # リレーが存在しなかった場合
        if result == None:
            return False
        
        created_at = result[0]
        return not (created_at + timedelta(seconds=options.relays_lifespan_sec)) > datetime.now()

    @staticmethod
    def __check_password(user_password, hashed_password):
        return bcrypt.checkpw(user_password.encode(), hashed_password.encode())