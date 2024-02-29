from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

engine = create_engine("sqlite:///database.db", echo=True)
async_session_maker = sessionmaker(engine, expire_on_commit=False)


def get_async_session():
    with async_session_maker() as session:
        yield session


def create_db():
    Base.metadata.create_all(engine)


class Topic(Base):
    __tablename__ = "topic"

    id = Column(Integer, primary_key=True)
    message_thread_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    icon_color = Column(Integer, nullable=True)
    icon_custom_emoji_id = Column(Integer, nullable=True)
