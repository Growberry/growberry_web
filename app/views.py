from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask_login import login_user, logout_user, current_user, login_required, abort
from app import app, db, lm, oid
from .forms import LoginForm, EditForm, PostForm, SearchForm, CreateGrow
from .models import User, Post, Grow, Reading
from .emails import follower_notification
from datetime import datetime
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS
import json


@lm.user_loader
def load_user(id):
	return User.query.get(int(id))

@app.before_request
def before_request():
	g.user = current_user
	if g.user.is_authenticated:
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit()
		g.search_form = SearchForm()

@app.errorhandler(404)
def not_found_error(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('500.html'), 500

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/index/<int:page>', methods = ['GET', 'POST'])
@login_required
def index(page = 1):
	form = PostForm()
	if form.validate_on_submit():
		post = Post(body = form.post.data, timestamp = datetime.utcnow(), author = g.user)
		db.session.add(post)
		db.session.commit()
		flash('Your post is now live!')
		return redirect(url_for('index'))
	posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
	return render_template('index.html', 
							title = 'hoe',
							form = form,
							posts = posts)

@app.route('/login', methods = ['GET','POST'])
@oid.loginhandler
def login():
	if g.user is not None and g.user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		session['remember_me']= form.remember_me.data
		return oid.try_login(form.openid.data, ask_for = ['nickname', 'email'])
	return render_template('login.html', title = "Sign In", form = form, providers = app.config['OPENID_PROVIDERS'])

@oid.after_login
def after_login(resp):
	if resp.email is None or resp.email == "":
		flash('Invalid login. Please try again.')
		return redirect(url_for('login'))
	user = User.query.filter_by(email=resp.email).first()
	if user is None:
		nickname = resp.nickname
		if nickname is None or nickname == "":
			nickname = resp.email.split('@')[0]
		nickname = User.make_valid_nickname(nickname)
		nickname=User.make_unique_nickname(nickname)
		user = User(nickname=nickname, email=resp.email)
		db.session.add(user)
		db.session.commit()
		# have the user follow him/herself
		db.session.add(user.follow(user))
		db.session.commit()
		remember_me = False
	if 'remember_me' in session:
		remember_me = session['remember_me']
		session.pop('remember_me', None)
	login_user(user, remember = remember_me)
	return redirect(request.args.get('next') or url_for('index'))

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
	user =User.query.filter_by(nickname=nickname).first()
	if user == None:
		flash('User %s not found.' % nickname)
		return redirect(url_for('index'))
	posts = g.user.posts.order_by(Post.timestamp.desc()).paginate(page, POSTS_PER_PAGE, False)
	return render_template('user.html',
							user=user,
							posts = posts)

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
	form = EditForm(g.user.nickname)
	if form.validate_on_submit():
		g.user.nickname = form.nickname.data
		g.user.about_me = form.about_me.data
		db.session.add(g.user)
		db.session.commit()
		flash('Your changes have been saved')
		return redirect(url_for('index'))
	else:
		flash('something went wrong.  Try again')
		form.nickname.data = g.user.nickname
		form.about_me.data = g.user.about_me
	return render_template('edit.html', form =form)

@app.route('/addgrow', methods=['GET', 'POST'])
@login_required
def addgrow():
	form = CreateGrow()
	if form.validate_on_submit():
		active = 0
		if form.is_active.data:
			active = 1
		grow = Grow(title = form.title.data,
					startdate = datetime.utcnow(),
					grower = g.user,
					thumb =form.thumb.data,
					variety = form.variety.data,
					settings = form.settings.data,
					is_active = active)
		db.session.add(grow)
		db.session.commit()
		flash('Your Grow has begun!')
		return redirect(url_for('garden', nickname = g.user.nickname ))
	else:
		flash('Something isnt right.  Try that again.')
	return render_template('addgrow.html', form =form)

@app.route('/garden/<nickname>')
@app.route('/garden/<nickname>/<int:page>')
@login_required
def garden(nickname, page =1):
	user = User.query.filter_by(nickname=nickname).first()
	if user == None:
		flash('User %s not found.' %nickname)
		return redirect(url_for('index'))
	grows = g.user.grows.order_by(Grow.startdate.desc()).paginate(page, POSTS_PER_PAGE,False)
	return render_template('garden.html', user=user,grows =grows)

@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
	user = User.query.filter_by(nickname = nickname).first()
	if user is None:
		flash('User %s not found' %nickname)
		return redirect(url_for('index'))
	if user == g.user:
		flash('You cannot follow yourself!')
		return redirect(url_for('user', nickname = nickname))
	u = g.user.follow(user)
	if u is None:
		flash('Cannot follow ' + nickname + '.')
		return redirect(url_for('user', nickname = nickname))
	db.session.add(u)
	db.session.commit()
	flash('You are now following %s!' %nickname)
	follower_notification(user, g.user)
	return redirect(url_for('user', nickname = nickname))

@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
	user = User.query.filter_by(nickname = nickname).first()
	if user is None:
		flash('User %s not found.' % nickname)
		return redirect(url_for('index'))
	if user == g.user:
		flash('You cant unfollow yourself!')
		return redirect(url_for('user', nickname = nickname))
	u = g.user.unfollow(user)
	if u is None:
		flash('Cannot unfollow ' + nickname + '.')
		return redirect(url_for('user', nickname = nickname))
	db.session.add(u)
	db.session.commit()
	flash ('You are no longer following %s.' %nickname)
	return redirect(url_for('user', nickname = nickname))
	
@app.route('/search', methods = ['POST'])
@login_required
def search():
	if not g.search_form.validate_on_submit():
		return redirect(url_for('index'))
	return redirect(url_for('search_results', query = g.search_form.search.data))

@app.route('/search_results/<query>')
@login_required
def search_results(query):
	results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
	return render_template('search_results.html',
							query = query,
							results = results)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
	post = Post.query.get(id)
	if post == None:
		flash('Post not found.')
		return redirect(url_for('index'))
	if post.author.id != g.user.id:
		flash('You can not delete a post by another user.')
		return redirect(url_for('index'))
	db.session.delete(post)
	db.session.commit()
	flash('Your post has been deleted.')
	return redirect(url_for('index'))
	


fake_settings = [{'sunrise': '0600', 'daylength': 12, 'set_temp':25}]

@app.route('/get_settings/<grow_id>', methods =['GET'])
def get_settings(grow_id):
	"""returns the settings for the specified grow"""
	sttgs = Grow.query.get(int(grow_id)).settings
	#seems that it doesn't matter at all if you just return the string/unicode or jsonify it first.
	#only difference is the requests.header content type changes from application/json to text/html
	return jsonify(json.loads(sttgs))
	#return sttgs


@app.route('/autopost/<user_id>', methods =['POST'])
def autopost(user_id):
	if not request.json or not 'post' in request.json:
		abort(400)
	user = User.query.get(int(user_id))
	body = request.json['post']
	post = Post(body = body, timestamp = datetime.utcnow(), author = user)
	db.session.add(post)
	db.session.commit()
	return jsonify({'body' : str(post.body),'author' : str(user.nickname)}), 201


@app.route('/todo/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': 1111,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }

    return jsonify({'task': task}), 201

@app.route('/echo', methods = ['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def api_echo():
    if request.method == 'GET':
        return "ECHO: GET\n"

    elif request.method == 'POST':
        return "ECHO: POST\n"

    elif request.method == 'PATCH':
        return "ECHO: PACTH\n"

    elif request.method == 'PUT':
        return "ECHO: PUT\n"

    elif request.method == 'DELETE':
        return "ECHO: DELETE"

@app.route('/reading/<grow_id>', methods =['POST'])
def reading(grow_id):
	if not request.json:
		abort(400)
	reading = Reading(timestamp = datetime.utcnow(),
					  internal_temp = request.json['internal_temp'],
					  internal_humidity = request.json['internal_humidity'],
					  pic_dir = request.json['pic_dir'],
					  grow_id = int(grow_id))
	db.session.add(reading)
	db.session.commit()
	return str(reading.id), 201