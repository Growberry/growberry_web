from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
grow = Table('grow', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('variety', VARCHAR(length=140)),
    Column('startdate', DATETIME),
    Column('user_id', INTEGER),
)

grow = Table('grow', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=140)),
    Column('plant', String(length=140)),
    Column('startdate', DateTime),
    Column('settings', String),
    Column('user_id', Integer),
)

user = Table('user', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('nickname', VARCHAR(length=64)),
    Column('email', VARCHAR(length=120)),
    Column('about_me', VARCHAR(length=140)),
    Column('last_seen', DATETIME),
    Column('variety', VARCHAR(length=140)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['grow'].columns['variety'].drop()
    post_meta.tables['grow'].columns['name'].create()
    post_meta.tables['grow'].columns['plant'].create()
    post_meta.tables['grow'].columns['settings'].create()
    pre_meta.tables['user'].columns['variety'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['grow'].columns['variety'].create()
    post_meta.tables['grow'].columns['name'].drop()
    post_meta.tables['grow'].columns['plant'].drop()
    post_meta.tables['grow'].columns['settings'].drop()
    pre_meta.tables['user'].columns['variety'].create()
