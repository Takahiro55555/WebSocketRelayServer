import bcrypt

from tornado.options import define, options

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from module.tables import Relay


class RelayPair:
    """
    通信を中継するWebSocketコネクションのペアを保持する。
    """

    def __init__(self, relay_id, raw_relay_password, ws_con):

        self.__db_engine = create_engine(
            options.db_uri_type + options.db_path, echo=options.sql_echo)
        sessinon = sessionmaker(bind=self.__db_engine)()

        try:
            token = sessinon.query(Relay).filter_by(
                relay_id=relay_id).one_or_none()
        except NoResultFound:
            pass
        except:
            pass

        self.__hashed_relay_password = token.hashed_relay_password

    def __del__(self):
        pass
