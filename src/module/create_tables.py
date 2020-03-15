from datetime import datetime, timedelta

from tornado.options import define, options

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Text, DateTime, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


define("sql_echo", default=False,
       help="If True, the SQLAlchemy Engine will log all statements")
define("tokens_lifespan_sec", default=7776000, help="default lifespan: 90days")
define("db_uri_type", default="sqlite:///",
       help="DB name, such as 'sqlite' and 'mysql'. This option using as 'sqlite://<file_path>'")

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(Text, unique=True, nullable=False)
    hashed_user_password = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # NOTE: SQLAlchemyのリレーションについての解説
    #       https://poyo.hatenablog.jp/entry/2017/01/08/212227
    token = relationship("Token")


class Token(Base):
    __tablename__ = "tokens"
    token_id = Column(Text, primary_key=True)
    hashed_token_password = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey(
        "users.user_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    expire_time = Column(DateTime, default=lambda: datetime.now(
    ) + timedelta(seconds=options.token_lifespan_sec))
    created_at = Column(DateTime, default=datetime.now)


class Relay(Base):
    __tablename__ = "relays"
    relay_id = Column(Text, primary_key=True)
    hashed_relay_password = Column(Text, nullable=False)
    token_id = Column(Text, ForeignKey("tokens.token_id",
                                       onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


def create_tables():
    """
    テーブルが作成されていない場合、新たにテーブルが作成される。
    既にテーブルが存在する場合は、何も起きない
    """
    engine = create_engine(options.db_uri_type +
                           options.db_path, echo=options.sql_echo)
    Base.metadata.create_all(bind=engine)
