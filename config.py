import os

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

OAUTH_CREDENTIALS = {
    'facebook': {
        'id': '1194113453996121',
        'secret': '08790eb0f7a9f25a63d3398cb0c05bf0'
    },
    'twitter': {
        'id': 'jndxr1EBBIcfv9uAFpA0zCFix',
        'secret': 'HLH67KY0WMd6MLbYhSVT78XOxILsuCIYC3KeChIPlPuCYjIiIl'
    },
	'google': {
		'id': '380265496418-eiemo6m3qcc50s4pagipm0qk8viv6uaf.apps.googleusercontent.com',
		'secret': 'MrrbSx2O3fFWxxyyckBJtokF'
	}
}




OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
	{'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
	{'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
	{'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
	{'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}
					]

# mail server settings
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

# admin list
ADMINS = ['growberry.py@gmail.com']

# pagination
POSTS_PER_PAGE = 4

# search database
WHOOSH_BASE = os.path.join(basedir, 'search.db')

MAX_SEARCH_RESULTS = 50
