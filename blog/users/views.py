from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from blog.config import db
from blog.config import app
from werkzeug.security import generate_password_hash, check_password_hash

from blog.decorators import check_confirmed
from blog.email import send_email, generate_confirmation_token, confirm_token
from blog.models import User, BlogPost
from blog.users.forms import RegistrationForm, LoginForm, UpdateUserForm
from blog.users.picture_handler import add_profile_pic
import datetime

users = Blueprint('users', __name__)



@users.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data,
                    confirmed=False)

        db.session.add(user)
        db.session.commit()
        token = generate_confirmation_token(user.email)
        confirm_url = url_for('users.confirm_email', token=token, _external=True)
        html = render_template('user_confirm_mail.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(user.email, subject, html)

        flash('Thanks for registering! Now you can login!')
        return redirect(url_for('users.unconfirmed'))
    return render_template('register.html', form=form)


@users.route('/confirm/<token>')
@login_required
def confirm_email(token):
    try:
        email = confirm_token(token)

    except:
        flash(u'The confirmation link is invalid or has expired.', 'danger')
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash(u'Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        flash(u'You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('core.index'))


@users.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect('index.html')
    flash(u'Please confirm your account!', 'warning')
    return render_template('user_unconfirmed.html')


@users.route('/resend')
@login_required
def resend_confirmation():
    token = generate_confirmation_token(current_user.email)
    confirm_url = url_for('users.confirm_email', token=token, _external=True)
    html = render_template('user_confirm_mail.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash(u'A new confirmation email has been sent.', 'success')
    return redirect(url_for('users.unconfirmed'))


@users.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Grab the user from our User Models table
        user = User.query.filter_by(email=form.email.data).first()

        # Check that the user was supplied and the password is right
        # The verify_password method comes from the User object
        # https://stackoverflow.com/questions/2209755/python-operation-vs-is-not

        if user.check_password(form.password.data) and user is not None:
            # Log in the user

            login_user(user)
            flash(u'Logged in successfully.', 'success')

            # If a user was trying to visit a page that requires a login
            # flask saves that URL as 'next'.
            next = request.args.get('next')

            # So let's now check if that next exists, otherwise we'll go to
            # the welcome page.
            if next == None or not next[0] == '/':
                next = url_for('core.index')

            return redirect(next)
    return render_template('login.html', form=form)


@users.route("/logout")
def logout():
    logout_user()
    flash('Logged Out Successfully')
    return redirect(url_for('core.index'))


@users.route("/account", methods=['GET', 'POST'])
@login_required
@check_confirmed
def account():
    form = UpdateUserForm()

    if request.method == 'POST':
        print(form)
        if form.picture.data:
            username = current_user.username
            pic = add_profile_pic(form.picture.data, username)
            current_user.profile_image = pic

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('User Account Updated')
        return redirect(url_for('users.account'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    profile_image = url_for('static', filename='profile_pics/' + current_user.profile_image)
    return render_template('account.html', profile_image=profile_image, form=form)


@users.route("/<username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    blog_posts = BlogPost.query.filter_by(author=user).order_by(BlogPost.date.desc()).paginate(page=page, per_page=5)
    return render_template('user_blog_posts.html', blog_posts=blog_posts, user=user)
