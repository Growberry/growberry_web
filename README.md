# growberry_web

This repo holds a version of the flask mega-tutorial by  Miguel Grinberg.  (http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

It will be modified as I move on to work more specifically for the control, and data collection of growbery_pi devices.



To start in development pi-server:

cd /home/nimrod337/growberry_web/
flask/bin/gunicorn --bind 0.0.0.0:8000 wsgi:app
