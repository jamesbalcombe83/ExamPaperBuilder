from flask import Flask, render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app import db
from app.auth import bp
from flask_login import current_user, login_user, logout_user
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.auth.email import send_password_reset_email

#handle login
@bp.route('/login', methods=['GET', 'POST'])
def login():
    #if already logged in, just return to index
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    #load the form
    form = LoginForm()
    if form.validate_on_submit():
        #get the user by checking in the User table for the matching username from the form
        user = User.query.filter_by(username=form.username.data).first()
        #if incorrect
        if user is None or not user.check_password(form.password.data) or user.deleted is not None:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        #when correct, use flask-login function login_user
        login_user(user, remember=form.remember_me.data)
        #this comes from the page that redirected to the login, so the user can go back
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

#handle logout
@bp.route('/logout')
def logout():
    #using the flask-login functions
    logout_user()
    return redirect(url_for('main.index'))

#handle registration
@bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        #add all values to the database and commit
        user = User(
            username=form.username.data, 
            email=form.email.data, 
            name=form.name.data,
            school_name=form.school_name.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.index', user=current_user))
    return render_template('auth/register.html', title='Register', form=form)

#Requesting a password reset
@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title='Reset Password', form=form)

#Resetting the password
@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    #verify the token for that user
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)