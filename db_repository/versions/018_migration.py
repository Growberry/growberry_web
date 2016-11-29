from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
reading = Table('reading', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('timestamp', DateTime),
    Column('lights', Integer),
    Column('fanspeed', String),
    Column('heatsink_temps', String),
    Column('internal_temp', String),
    Column('internal_humidity', String),
    Column('external_temp', String),
    Column('external_humidity', String),
    Column('pic_dir', String),
    Column('grow_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['reading'].columns['external_humidity'].create()
    post_meta.tables['reading'].columns['external_temp'].create()
    post_meta.tables['reading'].columns['fanspeed'].create()
    post_meta.tables['reading'].columns['heatsink_temps'].create()
    post_meta.tables['reading'].columns['lights'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['reading'].columns['external_humidity'].drop()
    post_meta.tables['reading'].columns['external_temp'].drop()
    post_meta.tables['reading'].columns['fanspeed'].drop()
    post_meta.tables['reading'].columns['heatsink_temps'].drop()
    post_meta.tables['reading'].columns['lights'].drop()
