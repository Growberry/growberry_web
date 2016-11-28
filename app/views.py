from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask_login import login_user, logout_user, current_user, login_required, abort
from flask_uploads import UploadSet, IMAGES, configure_uploads
from app import app, db, lm
from .forms import EditForm, PostForm, SearchForm, CreateGrow, GrowSettings, SettingsForm
from .models import User, Post, Grow, Reading
from .emails import follower_notification
from datetime import datetime
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS
from .oauth import OAuthSignIn
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


@app.route('/login')
def login():
    return render_template('login.html')



@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email, picture = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email, profile_pic=picture)
        db.session.add(user)
#make users follow themselves
        db.session.add(user.follow(user))
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


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
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, POSTS_PER_PAGE, False)
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

@app.route('/grow/<int:grow_id>')
@app.route('/grow/<int:grow_id>/<int:page>')
@login_required
def grow(grow_id, page =1):
    grow = Grow.query.get(int(grow_id))
    grower = User.query.get(grow.user_id)
    # grow_title = Grow.query.get(int(grow_id)).title
    # grow_settings = json.loads(Grow.query.get(int(grow_id)).settings)
    readingspast24 = grow.readings.order_by(Reading.timestamp.desc()).paginate(page, 24, False)
    # print readingspast24
    # for reading in readingspast24.items():
    #     print reading.heatsink_temps
    return render_template('grow.html',
                           title=grow.title,
                           user = g.user,
                           grow=grow,
                           grower =grower,
                           readings = readingspast24)





@app.route("/testsettings/", methods= ['GET', 'POST'])
def testsettings():
    saved_settings = Settings()
    form = SettingsForm(obj=saved_settings)

    if form.validate_on_submit():
        form.populate_obj(saved_settings)
        flash(saved_settings.message)

    return render_template("fakegrow.html", form=form)

class Settings(object):
    def __init__(self, settingsdict):
        message = "original message"
        sunrise = settingsdict['sunrise']
        daylength = settingsdict['daylength']
        settemp = settingsdict['settemp']

@app.route('/settings/<int:grow_id>',methods=['GET', 'POST'])
@login_required
def settings(grow_id):
    form = GrowSettings()
    # myForm.display.default = 'ONE'
    # myForm.process()  # process choices & default
    grow = Grow.query.get(int(grow_id))

    try:
        settings = json.loads(grow.settings)
        growsettings = Settings(settings)
    except:
        settings = {}
    if form.validate_on_submit():
        form.populate_obj(growsettings)
        settings['sunrise'] = form.sunrise.data
        settings['daylength'] = form.daylength.data
        settings['settemp'] = form.settemp.data
        grow.settings = json.dumps(settings)
        db.session.add(grow)
        db.session.commit()
        flash('Settings have been updated')
        return redirect(url_for('garden', nickname=g.user.nickname))
    else:
        flash('Something isnt right.  Try that again.')
    return render_template('settings.html', form = form, settings = settings)

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
    """returns the settings for the specified grow - need to change this to the specified barrel.
    will need to find all grows with barrel_id to the one in the URL, sort them by is_active. Will also need to add a barrel
    table in the database, and an foreign key for barrel_id in each grow."""
    sttgs = Grow.query.get(int(grow_id)).settings
    settings_dict = json.loads(sttgs)
    settings_dict['startdate'] = Grow.query.get(int(grow_id)).startdate.strftime('%m%d%y')
    #seems that it doesn't matter at all if you just return the string/unicode or jsonify it first.
    #only difference is the requests.header content type changes from application/json to text/html
    #return jsonify(json.loads(sttgs))  #works
    return jsonify(settings_dict)
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
    """
    Normally you would not have to str() everything,
    but for some reason sqlite doesn't like anything but string and int
    """
    if not request.json:
        abort(400)

    # will need more robust dynamic error checking
    stand_in_sensor = {"timestamp": "2016-04-20T04:20:00.000000", "temp": 99.9, "humidity": 99.9}
    if 'internal' not in request.json['sensors']:
        request.json['sensors']['internal'] = stand_in_sensor
    elif 'external' not in request.json['sensors']:
        request.json['sensors']['external'] = stand_in_sensor

    #
    # internal_check = request.json['sensors'].get('internal', stand_in_sensor)
    # external_check = request.json['sensors'].get('external', stand_in_sensor)

    try:
        max(request.json['sinktemps'])
    except ValueError:
        request.json['sinktemps'].append(30.0001)


    # internal_temp = ""
    # internal_humidity = ""
    # external_temp = ""
    # external_humidity = ""
    # if 'internal' in request.json['sensors']:
    #     internal_temp = str(request.json['sensors']['internal']['temp'])
    #     internal_humidity = str(request.json['sensors']['internal']['humidity'])
    # elif ''request.json['sensors']
    # external_temp = str(request.json['sensors']['external']['temp']),
    # external_humidity = str(request.json['sensors']['external']['humidity']),
    # heatsink_temps = '|'.join([str(x) for x in request.json['sinktemps']]),
    # max_sinktemp = str(max(request.json['sinktemps'])),
    # pic_dir = request.json['pic_dir'],
    # grow_id = int(grow_id)

    reading = Reading(timestamp=datetime.strptime(request.json['timestamp'], "%Y-%m-%dT%H:%M:%S.%f"),
                      lights=request.json['lights'],
                      fanspeed=str(request.json['fanspeed']),
                      internal_temp=str(request.json['sensors']['internal']['temp']),
                      internal_humidity=str(request.json['sensors']['internal']['humidity']),
                      external_temp=str(request.json['sensors']['external']['temp']),
                      external_humidity=str(request.json['sensors']['external']['humidity']),
                      heatsink_temps='|'.join([str(x) for x in request.json['sinktemps']]),
                      max_sinktemp=str(max(request.json['sinktemps'])),
                      pic_dir=request.json['pic_dir'],
                      grow_id=int(grow_id)
                      )
    db.session.add(reading)
    db.session.commit()
    return str(reading.id), 201


# photos = UploadSet('photos', IMAGES)
#
# @app.route('/upload', methods=['POST'])
# def upload():
#     if request.method == 'POST' and 'photo' in request.files:
#         filename = photos.save(request.files['photo'])
#         rec = Photo(filename=filename)
#         rec.store()
#         flash("Photo saved.")
#         return redirect(url_for('show', id=rec.id))
#     return jsonify({'error': 'you messed up'})
#
# @app.route('/photo/<id>')
# def show(id):
#     photo = Photo.load(id)
#     if photo is None:
#         abort(404)
#     url = photos.url(photo.filename)
#     return render_template('show.html', url=url, photo=photo)


###############  this works for now ####################
# photos = UploadSet('photos',IMAGES)
#
# app.config['UPLOADED_PHOTOS_DEST'] = 'app/static/img/newfolder'
# configure_uploads(app, photos)
#
# @app.route('/upload', methods=['GET','POST'])
# def upload():
#     if request.method == 'POST' and 'photo' in request.files:
#         filename = photos.save(request.files['photo'])
#         return filename
#     return render_template('upload.html')
#########################################################

photos = UploadSet('photos',IMAGES)

app.config['UPLOADED_PHOTOS_DEST'] = 'app/static/img/newfolder'
configure_uploads(app, photos)
#
# @app.route('/upload', methods=['GET','POST'])
# def upload():
#     if request.method == 'POST':
#         if 'photo' in request.files:
#
#         arguments = '|'.join([str(x) for x in request.files])
#         return str(request.args)
#
#         # print arguments
#     return render_template('upload.html')
