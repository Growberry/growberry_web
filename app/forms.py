from flask_wtf import Form
from wtforms import StringField, BooleanField, TextAreaField, IntegerField, FloatField
from wtforms.validators import DataRequired, Length, NumberRange
from app.models import User


class EditForm(Form):
	nickname = StringField('nickname', validators = [DataRequired()])
	about_me = TextAreaField('about_me', validators = [Length(min=0,max=140)])

	def __init__(self, original_nickname, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.original_nickname = original_nickname

	def validate(self):
		if not Form.validate(self):
			return False
		if self.nickname.data == self.original_nickname:
			return True
		if self.nickname.data != User.make_valid_nickname(self.nickname.data):
			self.nickname.errors.append('This nickname has invalid characters. Please use letters, numbers, dots and underscores only.')
		user = User.query.filter_by(nickname=self.nickname.data).first()
		if user != None:
			self.nickname.errors.append('This nickname is already in use.  Please choose another one.')
			return False
		return True

class CreateGrow(Form):

	title = StringField('title', validators = [Length(min=0,max=140)])
	is_active = BooleanField('is_active', default = True)
	thumb = TextAreaField('thumb', validators = [Length(min=0,max=140)])
	variety = TextAreaField('variety', validators = [Length(min=0,max=140)])
	settings = TextAreaField('settings', validators = [Length(min=0)])
	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)

class GrowSettings(Form):
	sunrise = StringField('sunrise', validators=[Length(min=4,max=4,message = '(HHMM) use only 4 numbers. No spaces or slashes')])
	daylength = IntegerField('daylength', validators = [NumberRange(min=0, max=24, message='enter only numbers between 0-24')])
	settemp = StringField('settemp', default= "25")
	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)

class PostForm(Form):
	post = StringField('post', validators = [DataRequired()])

class SearchForm(Form):
	search = StringField('search', validators = [DataRequired()])
