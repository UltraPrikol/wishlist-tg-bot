from typing import List, Optional
from sqlalchemy import String, ForeignKey, Table, Column, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,\
    relationship, backref


class Base(DeclarativeBase):
    pass


friendship = Table(
    'friendship', Base.metadata,
    Column('friend_a_id', Integer, ForeignKey('bot_user.id')),
    Column('friend_b_id', Integer, ForeignKey('bot_user.id'))
)


user_requests = Table(
    'user_requests', Base.metadata,
    Column('user_inc_req_id', Integer, ForeignKey('bot_user.id')),
    Column('requester_id', Integer, ForeignKey('bot_user.id'))
)


class User(Base):
    __tablename__ = "bot_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    user_id: Mapped[int] = mapped_column()
    wishlists: Mapped[List["Wishlist"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    friends = relationship(
        'User', secondary=friendship,
        primaryjoin=(friendship.c.friend_a_id == id),
        secondaryjoin=(friendship.c.friend_b_id == id),
        backref=backref('friendship', lazy='dynamic'), lazy='dynamic'
    )
    requests = relationship(
        'User', secondary=user_requests,
        primaryjoin=(user_requests.c.user_inc_req_id == id),
        secondaryjoin=(user_requests.c.requester_id == id),
        backref=backref('user_requests', lazy='dynamic'), lazy='dynamic'
    )

    def get_incoming_requests(self, session):
        incoming_requests = session.query(User).join(
            user_requests, user_requests.c.requester_id == User.id
        ).filter(
            user_requests.c.user_inc_req_id == self.id
        ).all()
        return incoming_requests

    def get_friends(self, session):
        friends = session.query(User).join(
            friendship, friendship.c.friend_a_id == User.id
        ).filter(
            friendship.c.friend_b_id == self.id
        ).all()
        if len(friends) > 0:
            return friends
        else:
            friends = session.query(User).join(
                friendship, friendship.c.friend_b_id == User.id
            ).filter(
                friendship.c.friend_a_id == self.id
            ).all()
            return friends

    def cancel_friend_request(self, user):
        if not self.is_friend(user) and self.is_request(user):
            self.friends.remove(user)
            user.friends.remove(self)

    def is_friend(self, user):
        return self.friends.filter(
            friendship.c.friend_b_id == user.id
        ).count() > 0

    def is_request(self, user):
        return self.requests.filter(
            user_requests.c.requester_id == user.id
        ).count() > 0

    def send_friend_request(self, user):
        if not user.is_friend(self) and not user.is_request(self) and not self.is_request(user):
            user.requests.append(self)
            return self

    def delete_friend(self, user):
        if self.is_friend(user):
            self.friends.remove(user)
            user.friends.remove(self)

    def can_accept_request(self, user):
        if not user.is_friend(self) and self.is_request(user):
            return True
        else:
            return False


class Wishlist(Base):
    __tablename__ = "wishlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), index=True)
    price: Mapped[Optional[int]]
    photo_id: Mapped[Optional[str]]
    url: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    user_id: Mapped[int] = mapped_column(ForeignKey("bot_user.id"))

    user: Mapped["User"] = relationship(back_populates="wishlists")

    def __repr__(self) -> str:
        return "Wishlist(id={!r}, name={!r})".format(self.id, self.name)
