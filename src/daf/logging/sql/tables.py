from datetime import datetime
from typing import List


from sqlalchemy import (
    SmallInteger, Integer, BigInteger, DateTime,
    Sequence, String, JSON, select, ForeignKey, func, case
)
from sqlalchemy.orm import (
    mapped_column,
    column_property,
    relationship,
    Mapped,
    DeclarativeBase
)

from ...misc.instance_track import track_id


class ORMBase(DeclarativeBase):
    "Base for all of ORM classes"
    pass


class MessageTYPE(ORMBase):
    """
    Lookup table for storing xMESSAGE types

    Parameters
    -----------
    name: str
        Name of the xMESSAGE class.
    """
    __tablename__ = "MessageTYPE"

    id = mapped_column(
        SmallInteger().with_variant(Integer, "sqlite"),
        Sequence("msg_tp_seq", 0, 1, minvalue=0, maxvalue=32767, cycle=True),
        primary_key=True
    )
    name = mapped_column(String(3072), unique=True)

    def __init__(self, name: str = None):
        self.name = name

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, MessageTYPE) and self.id == __value.id

    def __hash__(self):
        return hash(self.id)


class MessageMODE(ORMBase):
    """
    Lookup table for storing message sending modes.

    Parameters
    -----------
    name: str
        Name of the xMESSAGE class.
    """

    __tablename__ = "MessageMODE"

    id = mapped_column(
        SmallInteger().with_variant(Integer, "sqlite"),
        Sequence("msg_mode_seq", 0, 1, minvalue=0, maxvalue=32767, cycle=True),
        primary_key=True
    )
    name = mapped_column(String(3072), unique=True)

    def __init__(self, name: str = None):
        self.name = name

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, MessageMODE) and self.id == __value.id

    def __hash__(self):
        return self.id


class GuildTYPE(ORMBase):
    """
    Lookup table for storing xGUILD types

    Parameters
    -----------
    name: str
        Name of the xMESSAGE class.
    """

    __tablename__ = "GuildTYPE"

    id: Mapped[int] = mapped_column(
        SmallInteger().with_variant(Integer, "sqlite"),
        Sequence("guild_tp_seq", 0, 1, minvalue=0, maxvalue=32767, cycle=True),
        primary_key=True
    )
    name = mapped_column(String(3072), unique=True)

    def __init__(self, name: str = None):
        self.name = name

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, GuildTYPE) and self.id == __value.id

    def __hash__(self):
        return self.id


class GuildUSER(ORMBase):
    """
    Table for storing different guilds and users.

    Parameters
    -----------
    guild_type: int
        Foreign key pointing to GuildTYPE.id.
    snowflake: int
        Discord's snowflake ID of the guild.
    name: str
        The name of the guild.
    """
    __tablename__ = "GuildUSER"

    id = mapped_column(
        Integer,
        Sequence("guild_user_seq", 0, 1, minvalue=0, maxvalue=2147483647, cycle=True),
        primary_key=True
    )
    snowflake_id = mapped_column(BigInteger, index=True)
    name = mapped_column(String(3072))
    guild_type_id: Mapped[int] = mapped_column(ForeignKey("GuildTYPE.id"))
    guild_type: Mapped["GuildTYPE"] = relationship(lazy="joined")

    def __init__(self, guild_type: GuildTYPE, snowflake: int, name: str):
        self.snowflake_id = snowflake
        self.name = name
        self.guild_type = guild_type

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, GuildUSER) and self.id == __value.id

    def __hash__(self):
        return self.id


class CHANNEL(ORMBase):
    """
    Table for storing different channels.

    Parameters
    -----------
    snowflake: int
        Discord's snowflake ID of the channel.
    name: str
        The name of the channel.
    guild_id: int
        Foreign key pointing to GuildUSER.id.
    """
    __tablename__ = "CHANNEL"
    id = mapped_column(
        Integer,
        Sequence("channel_seq", 0, 1, minvalue=0, maxvalue=2147483647, cycle=True),
        primary_key=True
    )
    snowflake_id = mapped_column(BigInteger)
    name = mapped_column(String(3072))
    guild_id: Mapped[int] = mapped_column(ForeignKey("GuildUSER.id"))
    guild: Mapped["GuildUSER"] = relationship(lazy="joined")

    def __init__(self, snowflake: int, name: str, guild: GuildUSER):
        self.snowflake_id = snowflake
        self.name = name
        self.guild = guild

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, CHANNEL) and self.id == __value.id

    def __hash__(self):
        return self.id


class DataHISTORY(ORMBase):
    """
    Table used for storing all the different data(JSON) that was ever sent (to reduce redundancy
    and file size in the MessageLOG).

    Parameters
    -----------
    content: str
        The JSON string representing sent data.
    """
    __tablename__ = "DataHISTORY"

    id = mapped_column(
        Integer,
        Sequence("dhist_seq", 0, 1, minvalue=0, maxvalue=2147483647, cycle=True),
        primary_key=True
    )

    content = mapped_column(JSON())

    def __init__(self, content: dict):
        self.content = content

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, DataHISTORY) and self.id == __value.id

    def __hash__(self):
        return self.id


class MessageChannelLOG(ORMBase):
    """
    This is a table that contains a log of channels that are linked to a certain message log.

    Parameters
    ------------
    message_log: MessageLOG
        Foreign key pointing to MessageLOG.id.
    channel: CHANNEL
        Foreign key pointing to CHANNEL.id.
    reason: str
        Stringified description of Exception that caused the send attempt to be successful for a certain channel.
    """

    __tablename__ = "MessageChannelLOG"

    log_id: Mapped[int] = mapped_column(Integer, ForeignKey("MessageLOG.id", ondelete="cascade"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(Integer, ForeignKey("CHANNEL.id"), primary_key=True)
    reason = mapped_column(String(3072))

    log: Mapped["MessageLOG"] = relationship(back_populates="channels", uselist=False, lazy="joined")
    channel: Mapped["CHANNEL"] = relationship(lazy="joined")

    def __init__(self, channel: CHANNEL, reason: str = None):
        self.channel = channel
        self.reason = reason

    def __eq__(self, value: object) -> bool:
        return self is value  # Can't compare by ID due to circular links, which ORM ignores.

    def __hash__(self):
        return id(MessageChannelLOG)


class MessageLOG(ORMBase):
    """
    Table containing information for each message send attempt.

    NOTE: This table is missing successful and failed channels (or DM success status).
    That is because those are a separate table.

    Parameters
    ------------
    sent_data: DataHISTORY
        DataHISTORY object containing JSON data.
    message_type: MessageTYPE
        MessageTYPE object representing type of the message.
    message_mode: MessageMODE | None
        MessageMODE object representing mode of the message. (TextMESSAGE and DirectMESSAGE only)
    dm_reason: str | None
        The reason why sending to the USER failed. (DirectMESSAGE only)
    guild: GuildUSER
        The guild / user message was sent to.
    author: GuildUSER
        The author of the message.
    channels: List["MessageChannelLOG"]
        List of MessageChannelLOG representing channel the message was sent into and the fail reason.
    """

    __tablename__ = "MessageLOG"

    id = mapped_column(
        Integer,
        Sequence("ml_seq", 0, 1, minvalue=0, maxvalue=2147483647, cycle=True),
        primary_key=True
    )
    sent_data_id: Mapped[int] = mapped_column(ForeignKey("DataHISTORY.id"))
    message_type_id: Mapped[int] = mapped_column(ForeignKey("MessageTYPE.id"))
    guild_id: Mapped[int] = mapped_column(ForeignKey("GuildUSER.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("GuildUSER.id"))
    # [TextMESSAGE, DirectMESSAGE]
    message_mode_id: Mapped[int] = mapped_column(ForeignKey("MessageMODE.id"), nullable=True)
    dm_reason = mapped_column(String(3072))  # [DirectMESSAGE]
    timestamp = mapped_column(DateTime)

    sent_data: Mapped["DataHISTORY"] = relationship(lazy="joined")
    message_type: Mapped["MessageTYPE"] = relationship(lazy="joined")
    guild: Mapped["GuildUSER"] = relationship(foreign_keys=[guild_id], lazy="joined")
    author: Mapped["GuildUSER"] = relationship(foreign_keys=[author_id], lazy="joined")
    message_mode: Mapped["MessageMODE"] = relationship(lazy="joined")
    channels: Mapped[List["MessageChannelLOG"]] = relationship(back_populates="log", lazy="joined")
    success_rate = column_property(
        case(
            (
                select(MessageTYPE.name).where(MessageTYPE.id == message_type_id).scalar_subquery() != "DirectMESSAGE",
                100 * select(func.count()).where(MessageChannelLOG.reason.is_(None), MessageChannelLOG.log_id == id)
                .select_from(MessageChannelLOG)
                .scalar_subquery() /
                select(func.count()).where(MessageChannelLOG.log_id == id).select_from(MessageChannelLOG)
                .scalar_subquery()
            ),
            else_=case((dm_reason.is_(None), 100), else_=0)
        )
    )

    def __init__(
        self,
        sent_data: DataHISTORY = None,
        message_type: MessageTYPE = None,
        message_mode: MessageMODE = None,
        dm_reason: str = None,
        guild: GuildUSER = None,
        author: GuildUSER = None,
        channels: List["MessageChannelLOG"] = None
    ):
        self.sent_data = sent_data
        self.message_type = message_type
        self.message_mode = message_mode
        self.dm_reason = dm_reason
        self.guild = guild
        self.author = author
        self.timestamp = datetime.now()
        self.channels = channels

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, MessageLOG) and self.id == __value.id

    def __hash__(self):
        return self.id


class Invite(ORMBase):
    __tablename__ = "Invite"

    id = mapped_column(
        Integer,
        Sequence("invite_seq", 0, 1, minvalue=0, maxvalue=2147483647, cycle=True),
        primary_key=True
    )
    guild_id: Mapped[int] = mapped_column(ForeignKey("GuildUSER.id"))
    discord_id: Mapped[str] = mapped_column(String, unique=True)

    guild: Mapped[GuildUSER] = relationship(lazy="joined")

    def __init__(self, discord_id: str, guild: GuildUSER):
        self.discord_id = discord_id
        self.guild = guild

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Invite) and self.id == __value.id

    def __hash__(self):
        return self.id


class InviteLOG(ORMBase):
    __tablename__ = "InviteLOG"

    id = mapped_column(
        Integer,
        Sequence("invite_log_seq", 0, 1, minvalue=0, maxvalue=2147483647, cycle=True),
        primary_key=True
    )

    invite_id = mapped_column(ForeignKey("Invite.id"))
    member_id = mapped_column(ForeignKey("GuildUSER.id"))
    timestamp = mapped_column(DateTime)

    invite: Mapped[Invite] = relationship(lazy="joined")
    member: Mapped[GuildUSER] = relationship(lazy="joined")

    def __init__(self, invite: Invite, member: GuildUSER):
        self.invite = invite
        self.member = member
        self.timestamp = datetime.now()

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, InviteLOG) and self.id == __value.id

    def __hash__(self):
        return self.id
