import bcrypt as bcrypt

from blog.config import db, login_manager
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
# By inheriting the UserMixin we get access to a lot of built-in attributes
# which we will be able to call in our views!
# is_authenticated()
# is_active()
# is_anonymous()
# get_id()


# The user_loader decorator allows flask-login to load the current user
# and grab their id.

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def create_admin():
    db.session.add(User(
        email="ad@min.com",
        password="admin",
        admin=True,
        confirmed=True,
        confirmed_on=datetime.utcnow())
    )
    db.session.commit()


class User(db.Model, UserMixin):

    # Create a table in the db
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    profile_image = db.Column(db.String(20), nullable=False, default='default_profile.png')
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    # password = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String(128))
    registered_on = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    # This connects BlogPosts to a User Author.
    posts = db.relationship('BlogPost', backref='author', lazy=True)

    def __init__(self, email, username, password, confirmed,
                 paid=False, admin=False, confirmed_on=None):
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)
        # self.password = bcrypt.generate_password_hash(password)
        self.registered_on = datetime.utcnow()
        self.admin = admin
        self.confirmed = confirmed
        self.confirmed_on = confirmed_on

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"UserName: {self.username}"


class BlogPost(db.Model):
    # Setup the relationship to the User table
    users = db.relationship(User)

    # Model for the Blog Posts on Website
    id = db.Column(db.Integer, primary_key=True)
    # To connect the BlogPost to a particular author
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    title = db.Column(db.String(140), nullable=False)
    text = db.Column(db.Text, nullable=False)

    def __init__(self, title, text, user_id):
        self.title = title
        self.text = text
        self.user_id =user_id


    def __repr__(self):
        return f"Post Id: {self.id} --- Date: {self.date} --- Title: {self.title}"

db.create_all()