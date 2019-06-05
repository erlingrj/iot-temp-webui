import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tabledef import *

engine = create_engine('sqlite:///users.db', echo=True)

# create a Session
Session = sessionmaker(bind=engine)
session = Session()

user = User("user","user")
session.add(user)

user = User("test","pass")
session.add(user)

user = User("", "")
session.add(user)

# commit the record the database
session.commit()

session.commit()