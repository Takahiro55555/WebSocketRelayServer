# 標準ライブラリ
import datetime
import json
import logging
import secrets

# 外部ライブラリ
import bcrypt

import tornado.web
from tornado.options import define, options

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc

# 自作モジュール
from module.tables import User, Token, Relay

# HACK: エラーメッセージの作成をスマートにする
#       現在のままではタイプミスによる間違ったキーによるデータを送信してしまう可能性がある


class RelayHandler(tornado.web.RequestHandler):
    engine = create_engine(
        options.db_uri_type + options.db_path, echo=options.sql_echo)
    relay_id_nbytes = 32
    relay_passwd_nbytes = 36
    relay_registration_try_time = 10  # トークンに重複が起きた際、トークンを再生成する回数

    def get(self):
        self.set_status(501, reason="Not Implemented")

    def post(self):
        errors = []

        # 未入力フィールドの確認
        combined_token = ""
        try:
            combined_token = self.get_argument("token")
        except tornado.web.MissingArgumentError as e:
            errors.append(
                dict(
                    field="token",
                    code="missing_argument",
                    message=e.log_message
                )
            )

        if len(errors) != 0:
            del combined_token
            self.write(json.dumps(
                dict(
                    message="Argument error",
                    errors=errors
                )
            ))
            return

        try:
            token_id, raw_token_passwd = combined_token.split('-')
        except ValueError as e:
            del combined_token
            msg = dict(
                message="Toekn error",
                errors=[
                dict(
                    field="token",
                    code="invalid_token",
                    message="Invalid token format"
                )]
            )
            self.write(json.dumps(msg))
            return
        del combined_token

        # DBからトークン情報を照会、取得
        session = sessionmaker(bind=self.engine)()
        try:
            result = session.query(Token.expire_time, Token.hashed_token_password).filter(
                Token.token_id == token_id).one_or_none()
        except sqlalchemy.exc.IntegrityError as e:
            del raw_token_passwd, token_id
            msg = dict(
                message="Database error occured",
                errors=[
                    dict(
                        field="token",
                        code="db_error",
                        message=str(e)
                    )
                ]
            )
            self.write(json.dumps(msg))
            return

        # トークンが存在しなかった場合
        if result == None:
            msg = dict(
                message="%s is not exist" % token_id,
                errors=[
                    dict(
                        field="token",
                        code="invalid_token",
                        message="invalid token id"
                    )
                ]
            )
            del raw_token_passwd, token_id
            self.write(json.dumps(msg))
            return
        token_expire_time = result[0]
        hashed_token_password = result[1]

        print(token_expire_time)

        # トークンの有効期限を確認
        if token_expire_time < datetime.datetime.now():
            del raw_token_passwd
            msg = dict(
                message="Token is expired",
                errors=[
                    dict(
                        field="token",
                        code="expired_token",
                        message="This token was expired at %s" % token_expire_time
                    )
                ]
            )
            self.write(json.dumps(msg))
            return

        # 入力されたトークンパスワードの有効性を確認
        if not self.__check_password(raw_token_passwd, hashed_token_password):
            del raw_token_passwd
            msg = dict(
                message="Token passward is not correct",
                errors=[
                    dict(
                        field="token",
                        code="invalid_password",
                        message="password is not correct"
                    )
                ]
            )
            self.write(json.dumps(msg))
            return
        del raw_token_passwd

        # リレーのパスワード部を生成
        raw_relay_passwd = secrets.token_hex(nbytes=self.relay_passwd_nbytes)
        hashed_relay_passwd = self.__hash_password(raw_relay_passwd)

        # トークンを生成
        # 重複が生じる可能性を考慮し、複数回トークンの生成を試みる
        db_relay = Relay()
        is_registration_succeed = False
        for _ in range(self.relay_registration_try_time):
            relay_id = secrets.token_hex(nbytes=self.relay_passwd_nbytes)
            db_relay.relay_id = relay_id
            db_relay.hashed_relay_password = hashed_relay_passwd
            db_relay.token_id = token_id
            try:
                session.add(instance=db_relay)
                session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                continue
            except Exception as e:
                errors.append(dict(
                    code="db_error",
                    message=str(e)
                ))
                break
            is_registration_succeed = True
            break

        if len(errors) != 0:
            del relay_id, raw_relay_passwd
            msg = dict(
                message="Database error occurred",
                errors=errors
            )
            self.write(json.dumps(msg))
            return

        # ユニークなトークンを生成できなかった場合のエラー（必ずしもそうとは限らない）
        if not is_registration_succeed:
            del relay_id, raw_relay_passwd
            msg = dict(
                message="Relay generator failed, please try again",
                errors=[
                    dict(
                        code="relay_generator_error",
                        message="Could not generate unique relay id, please try again"
                    )
                ]
            )
            self.write(json.dumps(msg))
            return

        # ユーザが扱いやすいようにID部とパスワード部を結合し、送信
        combined_relay = "%s-%s" % (relay_id, raw_relay_passwd)
        msg = dict(
            message="Success",
            relay=combined_relay
        )
        self.write(json.dumps(msg))

        del relay_id, raw_relay_passwd, combined_relay
        session.close()

    @staticmethod
    def __hash_password(password, rounds=12):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()

    @staticmethod
    def __check_password(user_password, hashed_password):
        return bcrypt.checkpw(user_password.encode(), hashed_password.encode())
