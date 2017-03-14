from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask_login import login_user, logout_user, current_user, login_required, abort
from flask_uploads import UploadSet, IMAGES, configure_uploads
from app import app, db, lm
from .forms import EditForm, PostForm, SearchForm, CreateGrow, GrowSettings, GrowNoteForm
from .models import User, Post, Grow, Reading, GrowNote
from .emails import follower_notification
from datetime import datetime
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, UPLOAD_PIC_PATH
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
def index(page=1):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body = form.post.data, timestamp = datetime.utcnow(), author = g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    return render_template('index.html',
                            title='growberry_web',
                            form=form,
                            posts=posts)


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
                            posts=posts)

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
        grow = Grow(title=form.title.data,
                    startdate=datetime.utcnow(),
                    grower=g.user,
                    variety=form.variety.data,
                    settings=form.settings.data,
                    is_active=active)
        db.session.add(grow)
        db.session.commit()
        flash('Your Grow has begun!')
        return redirect(url_for('garden', nickname=g.user.nickname))
    else:
        flash('Something isnt right.  Try that again.')
    return render_template('addgrow.html', form=form)

@app.route('/garden/<nickname>')
@app.route('/garden/<nickname>/<int:page>')
@login_required
def garden(nickname, page =1):
    user = User.query.filter_by(nickname=nickname).first()
    if user == None:
        flash('User %s not found.' %nickname)
        return redirect(url_for('index'))
    grows = g.user.grows.order_by(Grow.is_active.desc(),Grow.startdate.desc()).paginate(page, POSTS_PER_PAGE,False)
    return render_template('garden.html', user=user,grows=grows)



@app.route('/grow/<int:grow_id>', methods = ['GET', 'POST'])
@app.route('/grow/<int:grow_id>/<int:page>',methods=['GET', 'POST'])
@login_required
def grow(grow_id, page =1):
    grow = Grow.query.get(int(grow_id))
    form = GrowNoteForm()
    if form.validate_on_submit():
        grownote = GrowNote(body=form.grownote.data, timestamp=datetime.utcnow(), grow_id=grow.id)
        db.session.add(grownote)
        db.session.commit()
        flash('Your note has been added!')
        return redirect(url_for('grow', grow_id=grow.id))
    grower = User.query.get(grow.user_id)
    readingspast24 = grow.readings.order_by(Reading.timestamp.desc()).paginate(page, 24, False)
    return render_template('grow.html',
                           title=grow.title,
                           user=g.user,
                           grow=grow,
                           grower=grower,
                           readings=readingspast24,
                           lastpic=grow.most_recent_reading().photo_path,
                           form=form,
                           grownotes=grow.notes.order_by(GrowNote.timestamp.desc()).paginate(page, POSTS_PER_PAGE,False)
                           )


@app.route('/end_grow/<int:grow_id>')
@login_required
def end_grow(grow_id):
    grow = Grow.query.get(int(grow_id))
    grow.is_active = 0
    db.session.add(grow)
    db.session.commit()
    flash("Your grow has ended!  Don't forget to add your final yield!")
    return redirect(url_for('grow', grow_id=grow_id))

class Settings(object):
    def __init__(self, settingsdict):
        self.sunrise = settingsdict['sunrise']
        self.daylength = settingsdict['daylength']
        self.settemp = settingsdict['settemp']

@app.route('/settings/<int:grow_id>',methods=['GET', 'POST'])
@login_required
def settings(grow_id):
    grow = Grow.query.get(int(grow_id))
    print grow.settings
    try:
        settings = json.loads(grow.settings)
    except:
        settings = {'sunrise': '0420', 'daylength':18, 'settemp':'25'}

    growsettings = Settings(settings)
    form = GrowSettings(obj=growsettings)
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
    return render_template('settings.html', form=form, settings=settings)

@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found' %nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following %s!' %nickname)
    follower_notification(user, g.user)
    return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You cant unfollow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash ('You are no longer following %s.' %nickname)
    return redirect(url_for('user', nickname=nickname))


@app.route('/search', methods=['POST'])
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
                            query=query,
                            results=results)


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


@app.route('/get_settings/<grow_id>', methods =['GET'])
def get_settings(grow_id):
    """returns the settings for the specified grow - need to change this to the specified barrel.
    will need to find all grows with barrel_id to the one in the URL, sort them by is_active. Will also need to add a barrel
    table in the database, and an foreign key for barrel_id in each grow."""
    grow = Grow.query.get(int(grow_id))
    sttgs = grow.settings
    settings_dict = json.loads(sttgs)
    settings_dict['startdate'] = grow.startdate.strftime('%m%d%y')
    settings_dict['is_active'] = grow.is_active
    #seems that it doesn't matter at all if you just return the string/unicode or jsonify it first.
    #only difference is the requests.header content type changes from application/json to text/html
    #return jsonify(json.loads(sttgs))  #works
    return jsonify(settings_dict)


@app.route('/autopost/<user_id>', methods=['POST'])
def autopost(user_id):
    if not request.json or 'post' not in request.json:
        abort(400)
    user = User.query.get(int(user_id))
    body = request.json['post']
    post = Post(body=body, timestamp = datetime.utcnow(), author=user)
    db.session.add(post)
    db.session.commit()
    return jsonify({'body' : str(post.body),'author' : str(user.nickname)}), 201


photos = UploadSet('photos',IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'app/static/img/growpics/'
configure_uploads(app, photos)


@app.route('/multi/<grow_id>', methods =['POST'])
def multi(grow_id):
    results = {}
    print request.files
    if 'metadata' in request.files:
        subjson = request.files['metadata'].read()
        submitted_data = json.loads(subjson)
        submitted_sensors = submitted_data['sensors']
        maxsinktemp = None
        try:
            maxsinktemp = max(submitted_data['sinktemps'])
        except ValueError:
            maxsinktemp = 'NA'

        reading = Reading(timestamp=datetime.strptime(submitted_data['timestamp'], "%Y-%m-%dT%H:%M:%S.%f"),
                          lights=submitted_data['lights'],
                          fanspeed=str(submitted_data['fanspeed']),
                          internal_temp=str(submitted_sensors.get('internal', {'temp':"NA"})['temp']),
                          internal_humidity=str(submitted_sensors.get('internal', {'humidity':"NA"})['humidity']),
                          external_temp=str(submitted_sensors.get('external', {'temp':"NA"})['temp']),
                          external_humidity=str(submitted_sensors.get('external', {'humidity':"NA"})['humidity']),
                          heatsink_temps='|'.join([str(x) for x in submitted_data['sinktemps']]),
                          max_sinktemp=str(maxsinktemp),
                          photo_path='/static/img/no_photo_assoc.png',
                          grow_id=int(grow_id)
                          )

        db.session.add(reading)
        db.session.commit()
        results.update({'reading_id': reading.id})

        if 'photo' in request.files:
            grow = Grow.query.get(int(grow_id))
            photo_name = str(reading.id) + '.jpg'
            photo_loc = str(grow.user_id) + '/' + str(grow_id)
            filename = photos.save(request.files['photo'], folder=photo_loc, name=photo_name)
            reading.photo_path = '/static/img/growpics/{}'.format(filename)
            results.update({'photo_loc': filename})

        db.session.commit()
    else:
        results.update({'error': 'No metadata detected in request.'})

    return jsonify(results), 201