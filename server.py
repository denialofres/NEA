from flask import Flask, redirect, url_for, request, render_template
import time
from time import datetime
app = Flask(__name__)

def hash(Password, Salt):
    return Password + Salt # Create/implement hashing algorithm

def getSalt(username):
    return "9ol.PL" # query database

def checkPasswordHash(username, passwordHash):
    return True # query database


class LoginForm(FlaskForm):
    username = StringField("Username")
    password = StringField("Password")
    submit = SubmitField("Log In")

@app.route('/', methods=["GET", "POST"])
def login():
    entry_form = LoginForm()
    
    if entry_form.is_submitted():
        username = entry_form.username.data
        password = entry_form.password.data
        if username =='':
            return render_template('login.html', form=entry_form)
        elif username != "admin":
            login_history.append((username, datetime.now().strftime("%H:%M:%S")))
            return render_template("user.html", username=username, count=len(login_history))
        else:
            return render_template("admin.html", history=login_history)
    else:
        print("Form was not submitted.")
        return render_template("login.html", form=entry_form)

    return render_template("login.html", form=entry_form)