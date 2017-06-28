"""
Database models for sample collection
"""
import peewee as pw
from playhouse.sqlite_ext import SqliteExtDatabase

from app import config

db = SqliteExtDatabase(config.DATA_CSV_FOLDER + 'sample_database.sqlite')


class BaseModel(pw.Model):
    class Meta:
        database = db


class Sample(BaseModel):
    """
    Sample model for sqlite database to manage uploads
    """
    primary_key = pw.PrimaryKeyField(primary_key=True)
    timestamp = pw.DateTimeField()
    level = pw.FloatField()
    volts = pw.FloatField()
    amps = pw.FloatField()
    uploaded = pw.BooleanField(default=False)
    result = pw.TextField(null=True)

db.connect()
