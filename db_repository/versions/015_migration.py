from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
readings = Table('readings', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('timestamp', DATETIME),
    Column('internal_temp', VARCHAR),
    Column('internal_humidity', VARCHAR),
    Column('pic_dir', VARCHAR),
    Column('grow_id', INTEGER),
)

reading = Table('reading', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('timestamp', DateTime),
    Column('internal_temp', String),
    Column('internal_humidity', String),
    Column('pic_dir', String),
    Column('grow_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['readings'].drop()
    post_meta.tables['reading'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['readings'].create()
    post_meta.tables['reading'].drop()
