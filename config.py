from app import app
import os

app.config['SECRET_KEY'] = "MY SECRET"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = 'static/profile_pic'
nicheList = ['Fitness', 'Finance', 'Education', 'Tech', 'Esports', 'Travel', 'Food', 'Lifestyle', 'Fashion', 'Health', 'Environment']
categoryList = ['Instagram', 'Facebook', 'Twitter', 'Twitch', 'Youtube', 'Tiktok', 'LinkedIn', 'Blog', 'Telegram']

app.config['FLASK_ENV'] = 'development'
app.config['ADMIN_AUTH_TOKEN'] = "MY_ADMIN_AUTH_TOKEN"



app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False