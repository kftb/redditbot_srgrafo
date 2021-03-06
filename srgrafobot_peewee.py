from peewee import *
from settings import *

db = SqliteDatabase(DB)

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)

class Submission(BaseModel):
    user = ForeignKeyField(User)
    thread_id = CharField(unique=True)
    title = CharField()
    date = DateTimeField()
    thread = BooleanField()
    comment = BooleanField()
    post_created = BooleanField()

def create_table():
    db.connect()
    db.create_tables([User, Submission])
    user = User(username='/u/SrGrafo')
    user.save()
    db.close()

