# 標準ライブラリ
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
from module.tables import User, Token

# HACK: エラーメッセージの作成をスマートにする
#       現在のままではタイプミスによる間違ったキーによるデータを送信してしまう可能性がある
#
# NOTE: トークンは一意なID部とパスワード部から成り、ハイフンで区切る
#       パスワード部はハッシュ化した後にDBへ登録する


class TokenHandler(tornado.web.RequestHandler):
    engine = create_engine(
        options.db_uri_type + options.db_path, echo=options.sql_echo)
    token_nbytes = 32
    token_passwd_nbytes = 36
    token_registration_try_time = 10  # トークンに重複が起きた際、トークンを再生成する回数

    def get(self):
        self.write("Token Hundler")

    def post(self):
        errors = []

        # 未入力フィールドの確認
        try:
            user_email = self.get_argument("userEmail")
        except tornado.web.MissingArgumentError as e:
            errors.append(
                dict(
                    field="userEmail",
                    code="missing_argument",
                    message=e.log_message
                )
            )
        try:
            raw_user_password = self.get_argument("userPassword")
        except tornado.web.MissingArgumentError as e:
            errors.append(
                dict(
                    field="userPassword",
                    code="missing_argument",
                    message=e.log_message
                )
            )
        if len(errors) != 0:
            del raw_user_password
            self.write(json.dumps(
                dict(
                    message="Missing argument",
                    errors=errors
                )
            ))
            return

        # DBからユーザ情報を照会、取得
        session = sessionmaker(bind=self.engine)()
        try:
            result = session.query(User.hashed_user_password, User.user_id).filter(
                User.email == user_email).one_or_none()
        except sqlalchemy.exc.IntegrityError as e:
            del raw_user_password
            msg = dict(
                message="Database error occured",
                errors=[(
                    dict(
                        field="userEmail",
                        code="db_error",
                        message=str(e)
                    )
                )]
            )
            self.write(json.dumps(msg))
            return

        # ユーザが存在しなかった場合
        if result == None:
            del raw_user_password
            msg = dict(
                message="%s is not exist" % user_email,
                errors=[
                    dict(
                        field="userEmail",
                        code="invalid_user",
                        message="user email is not correct or have no enough authorization"
                    )
                ]
            )
            self.write(json.dumps(msg))
            return
        hashed_user_password = result[0]
        user_id = result[1]

        # 入力されたユーザの有効性パスワードの有効性を確認
        if not self.__check_password(raw_user_password, hashed_user_password):
            del raw_user_password
            msg = dict(
                message="User passward is not correct",
                errors=[
                    dict(
                        field="userPassword",
                        code="invalid_password",
                        message="password is not correct"
                    )
                ]
            )
            self.write(json.dumps(msg))
            return
        del raw_user_password

        # トークンのパスワード部を生成
        raw_token_passwd = secrets.token_hex(nbytes=self.token_passwd_nbytes)
        hashed_token_passwd = self.__hash_password(raw_token_passwd)

        # トークンを生成
        # 重複が生じる可能性を考慮し、複数回トークンの生成を試みる
        db_token = Token()
        is_registration_succeed = False
        for _ in range(self.token_registration_try_time):
            token_id = secrets.token_hex(nbytes=self.token_nbytes)
            db_token.token_id = token_id
            db_token.hashed_token_password = hashed_token_passwd
            db_token.user_id = user_id
            try:
                session.add(instance=db_token)
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
            del token_id, raw_token_passwd
            msg = dict(
                message="Database error occurred",
                errors=errors
            )
            self.write(json.dumps(msg))
            return

        # ユニークなトークンを生成できなかった場合のエラー（必ずしもそうとは限らない）
        if not is_registration_succeed:
            del token_id, raw_token_passwd
            msg = dict(
                message="Token generator failed, please try again",
                errors=[
                    dict(
                        code="token_generator_error",
                        message="Could not generate unique token, please try again"
                    )
                ]
            )
            self.write(json.dumps(msg))
            return

        # ユーザが扱いやすいようにID部とパスワード部を結合し、送信
        combined_token = "%s-%s" % (token_id, raw_token_passwd)
        msg = dict(
            message="Success",
            token=combined_token
        )
        self.write(json.dumps(msg))

        del token_id, raw_token_passwd, combined_token
        session.close()

    @staticmethod
    def __hash_password(password, rounds=12):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()

    @staticmethod
    def __check_password(user_password, hashed_password):
        return bcrypt.checkpw(user_password.encode(), hashed_password.encode())
