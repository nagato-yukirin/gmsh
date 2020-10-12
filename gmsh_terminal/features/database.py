import logging

from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.engine import ResultProxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from gmsh_terminal.features import discord_handler
from gmsh_terminal.features.commands import parse_command, codify

log = logging.getLogger(__name__)

Base = declarative_base()

default_engine = create_engine('sqlite:///gmsh.sqlite')
sqlol_engine = create_engine('sqlite:///playground.sqlite')


class ReactionMessage(Base):
    __tablename__ = 'tutor_reactmsg'

    id = Column(Integer, primary_key=True)
    subject_id = Column(None, ForeignKey('tutor_subjects.id'))

    subject = relationship("Subject", back_populates="reactmsg", uselist=False)


class Subject(Base):
    __tablename__ = 'tutor_subjects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    reactmsg = relationship("ReactionMessage", back_populates="subject", cascade="all, delete, delete-orphan")
    roles = relationship("TutorRoles", back_populates="subject", cascade="all, delete, delete-orphan")


class TutorRoles(Base):
    __tablename__ = 'tutor_roles'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    subject_id = Column(Integer, ForeignKey('tutor_subjects.id'))
    proficiency = Column(Integer)

    subject = relationship("Subject", back_populates="roles", uselist=False)


class BreakoutRoom(Base):
    __tablename__ = 'tutor_br'

    id = Column(Integer, primary_key=True)
    vc_id = Column(Integer)
    role_id = Column(Integer)
    name = Column(String)
    private = Column(Boolean)


try:
    Base.metadata.create_all(default_engine)
    log.info("Tables created")
except Exception as e:
    log.error("Error occurred during Table creation!", exc_info=e)

DefaultSession = sessionmaker()
DefaultSession.configure(bind=default_engine)


@discord_handler('on_message')
async def sqlol_handler(client, message):
    expr, lang = parse_command(message.content.strip())

    if expr is None or not lang.lower() == 'sql':
        return False

    with sqlol_engine.connect() as con:
        try:
            rs: ResultProxy = con.execute(expr)
            if rs.returns_rows:
                rows = rs.fetchall()
                result = f'{len(rows)} rows matched ('+', '.join(rs.keys())+')\n'+'\n'.join(str(r) for r in rows)
            else:
                result = 'Operation completed successfully'
            await message.channel.send(codify(result))
        except Exception as e2:
            await message.channel.send(codify(f'Could not execute command:\n{e2}'))
        return True
