from app import app
from flask import render_template, flash, redirect
from .forms import LoginForm

@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'Austin'}  # fake user
    posts = [#fake array of posts
		{
			'author': {'nickname':'John'},
			'body': 'this thing I says'
		},
		{
			'author':{'nickname': 'Sydney'},
			'body':'I have a huge crush on Austin'
		},
		{
			'author':{'nickname':'Sarah'},
			'body':'OMG, me too!!'
		}
	]
    return render_template('index.html', 
							user = user,
							title = 'hoe',
							posts = posts)


@app.route('/login', methods =['GET','POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		flash('Login requested for OpenID="%s", remember_me =%s' %(form.openid.data,str(form.remember_me.data)))
		return redirect('/index')
	return render_template('login.html', title = 'Sign in', form=form, providers = app.config['OPENID_PROVIDERS'])
