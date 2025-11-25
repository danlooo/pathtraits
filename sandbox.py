#
# pony orm: does not work, does not allow creasting cnew classes
#

import os
from pony.orm import *

db = Database("sqlite", os.path.abspath("estore.sqlite"), create_db=True)


class Path(db.Entity):
    id = PrimaryKey(int, auto=True)
    path = Required(str, unique=True)
    users = Set("User")


class User(db.Entity):
    path = Required(Path)
    username = Required(str)


class Foo(db.Entity):
    path = Required(Path)
    foo = Required(bool)


sql_debug(True)
db.generate_mapping(create_tables=True)

p1 = Path(path="/foo.txt")
u1 = User(path=p1, username="dloos")
commit()


#
# SQLModel
# does not work see https://github.com/fastapi/sqlmodel/pull/43
#

from sqlmodel import *


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: int | None = None


hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)

engine = create_engine("sqlite:///database.db")
SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    session.add(hero_1)
    session.add(hero_2)
    session.add(hero_3)
    session.commit()


class Location(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str


SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    location_1 = Location(name="Atlantis")
    session.add(location_1)
    location_2 = Location(name="Jena")
    session.add(location_2)
