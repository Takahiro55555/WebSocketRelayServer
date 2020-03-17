import re
import json

import bcrypt

import tornado.web
from tornado.options import define, options

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc

from module.tables import User

# HACK: エラーメッセージの作成をスマートにする
#       現在のままではタイプミスによる間違ったキーによるデータを送信してしまう可能性がある


class AccountHundler(tornado.web.RequestHandler):
    engine = create_engine(options.db_uri_type +
                           options.db_path, echo=options.sql_echo)

    def get(self):
        self.set_status(501, reason="Not Implemented")

    def post(self):
        errors = []

        # 未入力フィールドの確認
        try:
            admin_email = self.get_argument("adminEmail")
        except tornado.web.MissingArgumentError as e:
            errors.append(
                dict(
                    field="adminEmail",
                    code="missing_argument",
                    message=e.log_message
                )
            )
        try:
            raw_admin_password = self.get_argument("adminPassword")
        except tornado.web.MissingArgumentError as e:
            errors.append(
                dict(
                    field="adminPassword",
                    code="missing_argument",
                    message=e.log_message
                )
            )
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
            self.write(json.dumps(
                dict(
                    message="Missing argument",
                    errors=errors
                )
            ))
            return

        # メールアドレスの確認（正規表現）
        reg = r"^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$"
        if re.fullmatch(reg, user_email) == None:
            msg = dict(
                message="Email addres is not valid.",
                errors=[
                    dict(
                        field="userEmail",
                        code="invalid_email",
                        message="user email addres does not match the regular expression(`%s`). " % reg
                    )
                ]
            )
            self.write(json.dumps(msg))
            return

        # 管理者名の有効性を確認
        if admin_email != options.admin_email:
            msg = dict(
                message="%s is not admin or not exists",
                errors=[
                    dict(
                        field="adminEmail",
                        code="invalid_user",
                        message="admin email is not correct or have no enough authorization"
                    )
                ]
            )
            self.write(json.dumps(msg))
            return

        # 管理者パスワードの有効性を確認
        if not self.__check_password(raw_admin_password, options.hashed_admin_password):
            msg = dict(
                message="Admin passward is not correct",
                errors=[
                    dict(
                        field="adminPassword",
                        code="invalid_password",
                        message="password is not correct"
                    )
                ]
            )
            self.write(json.dumps(msg))
            return

        # パスワードのハッシュ化
        hashed_user_password = self.__hash_password(raw_user_password)
        del raw_user_password

        # DBへの登録
        session = sessionmaker(bind=self.engine)()
        user = User()
        user.hashed_user_password = hashed_user_password
        user.email = user_email
        try:
            session.add(instance=user)
            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            errors.append(
                dict(
                    field="userEmail",
                    code="db_error",
                    message=str(e)
                )
            )
        if len(errors) != 0:
            msg = dict(
                message="Database error occurred",
                errors=errors
            )
            self.write(json.dumps(msg))
            return

        msg = dict(
            message="Success"
        )
        self.write(json.dumps(msg))

    @staticmethod
    def __hash_password(password, rounds=12):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()

    @staticmethod
    def __check_password(user_password, hashed_password):
        return bcrypt.checkpw(user_password.encode(), hashed_password.encode())
