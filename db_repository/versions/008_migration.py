from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
grow = Table('grow', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('startdate', DATETIME),
    Column('user_id', INTEGER),
    Column('name', VARCHAR(length=140)),
    Column('plant', VARCHAR(length=140)),
    Column('settings', VARCHAR),
)

grow = Table('grow', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('title', String(length=140)),
    Column('plant', String(length=140)),
    Column('startdate', DateTime),
    Column('settings', String),
    Column('user_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['grow'].columns['name'].drop()
    post_meta.tables['grow'].columns['title'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['grow'].columns['name'].create()
    post_meta.tables['grow'].columns['title'].drop()
