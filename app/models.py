from app import db, app
from hashlib import md5
import sys
import re

if sys.version_info >= (3,0):
	enable_search = False
else:
	enable_search = True
	import flask_whooshalchemy as whooshalchemy

followers = db.Table('followers',
	db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	social_id = db.Column(db.String(64), nullable=False, unique=True)
	nickname = db.Column(db.String(64), index = True, unique = True)
	email = db.Column(db.String(64), nullable=True)
	profile_pic = db.Column(db.String(200), nullable = True)
	posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')
	grows = db.relationship('Grow', backref = 'grower', lazy = 'dynamic')
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime)
	followed = db.relationship('User',
								secondary = followers,
								primaryjoin = (followers.c.follower_id == id),
								secondaryjoin = (followers.c.followed_id == id),
								backref = db.backref('followers', lazy = 'dynamic'),
								lazy = 'dynamic')

	@staticmethod
	def make_unique_nickname(nickname):
		if User.query.filter_by(nickname=nickname).first() is None:
			return nickname
		version = 2
		while True:
			new_nickname = nickname + str(version)
			if User.query.filter_by(nickname=new_nickname).first() is None:
				break
			version += 1
		return new_nickname

	@staticmethod
	def make_valid_nickname(nickname):
		return re.sub('[^a-zA-Z0-9_\.]', '', nickname)

	@property
	def is_authenticated(self):
		return True

	@property
	def is_active(self):
		return True

	@property
	def is_anonymous(self):
		return False

	def follow(self, user):
		if not self.is_following(user):
			self.followed.append(user)
			return self

	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)
			return self

	def is_following(self, user):
		return self.followed.filter(followers.c.followed_id == user.id).count() > 0

	def followed_posts(self):
		return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id).order_by(Post.timestamp.desc())

	def get_id(self):
		try:
			return unicode(self.id) #python 2
		except NameError:
			return str(self.id)	#python 3
	def avatar(self,size):
		if self.profile_pic:
			return self.profile_pic
		try:
			return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (md5(self.email.encode('utf-8')).hexdigest(), size)
		except:
			return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (md5('default_avatar@google.com').hexdigest(), size)

	def __repr__(self):
		return '<Usr %r>' % (self.nickname)


class Post(db.Model):
	__searchable__ = ['body']

	id = db.Column(db.Integer, primary_key = True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<Post %r>' % (self.body)

class Grow(db.Model):

	id = db.Column(db.Integer, primary_key = True)
	is_active = db.Column(db.Integer)
	title = db.Column(db.String(140))
	variety = db.Column(db.String(140))
	startdate = db.Column(db.DateTime)
	settings = db.Column(db.String)
	thumb = db.Column(db.String)
	readings = db.relationship('Reading', backref='grower', lazy='dynamic')
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	#need some sort of function to json.dump befor I convert to a better database that can handle JSON/pickle objects

	def __repr__(self):
		return '<Grow %r>' % (self.title)

class Reading(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	timestamp = db.Column(db.DateTime)
	lights = db.Column(db.Integer)
	fanspeed = db.Column(db.String)
	heatsink_temps = db.Column(db.String)
	internal_temp = db.Column(db.String)
	internal_humidity = db.Column(db.String)
	external_temp = db.Column(db.String)
	external_humidity = db.Column(db.String)
	pic_dir = db.Column(db.String)
	grow_id = db.Column(db.Integer, db.ForeignKey('grow.id'))

if enable_search:
	whooshalchemy.whoosh_index(app, Post)



# class Reading(db.Model):
# 	id = db.Column(db.Integer, primary_key = True)
# 	timestamp = db.Column(db.DateTime)
# 	lights = db.Column(db.Integer)
# 	fanspeed = db.Column(db.Float)
# 	heatsink_temps = db.Column(db.String)
# 	internal_temp = db.Column(db.Float)
# 	internal_humidity = db.Column(db.Float)
# 	external_temp = db.Column(db.Float)
# 	external_humidity = db.Column(db.Float)
# 	pic_dir = db.Column(db.String)
# 	grow_id = db.Column(db.Integer, db.ForeignKey('grow.id'))
#
# if enable_search:
# 	whooshalchemy.whoosh_index(app, Post)