from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
grow = Table('grow', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('is_active', Integer),
    Column('title', String(length=140)),
    Column('variety', String(length=140)),
    Column('startdate', DateTime),
    Column('settings', String),
    Column('thumb', String),
    Column('user_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['grow'].columns['thumb'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['grow'].columns['thumb'].drop()
