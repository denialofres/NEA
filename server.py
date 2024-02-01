# flask --app server run


from flask import Flask, redirect, url_for, request, render_template
import time
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import sqlite3
import json

app = Flask(__name__)
login_history = []


#get dbfile
optionsFile = "options.json"
with open(optionsFile, "r") as optionsFileObject:
	options = json.load(optionsFileObject)
app.config['SECRET_KEY']=options["secret"]
DBFILE = options["dbfile"]

#check dbfile exists
try:
	with open(DBFILE) as DB:
		pass
except FileNotFoundError:
	print(f"dbfile ({DBFILE}) not found")
	quit()


def hash(Password, Salt):
	hash = 14
	for i in list(Salt)+list(Password):
		hash = (hash * 65599) + ord(i)
	return hash

def getSalt(username):
	conn = sqlite3.connect(DBFILE)
	cursor = conn.cursor() 

	Salt = cursor.execute(f"SELECT Salt FROM Users WHERE UserName = '{username}'")

	conn.close()
	return "?A.Cs3" # query database

def checkPasswordHash(username, attemptHash):
	conn = sqlite3.connect(DBFILE)
	cursor = conn.cursor() 

	PasswordHashData = cursor.execute(f"SELECT PasswordHash FROM Users WHERE UserName = '{username}'")
	for item in PasswordHashData:
		PasswordHash = item

	conn.close()

	if int(PasswordHash[0]) == attemptHash:
		return True

def checkUsernameExists(username):
	conn = sqlite3.connect(DBFILE)
	cursor = conn.cursor() 

	UserHashData = cursor.execute(f"SELECT UserName FROM Users WHERE UserName = '{username}'")
	numUsers = len(cursor.fetchall())

	conn.close()

	if numUsers > 0:
		return True
	return False


class LoginForm(FlaskForm):
	username = StringField("Username")
	password = StringField("Password")
	LoginSubmit = SubmitField("Log In")

class RegisterForm(FlaskForm):
	username = StringField("Username")
	fullname = StringField("name")
	email = StringField("Email")
	password = StringField("Password")
	passwordConfirm = StringField("password_confirmation")
	RegisterSubmit = SubmitField("Log In")

@app.route('/login', methods=["GET", "POST"])
def login():
	login_form = LoginForm()
	register_form = RegisterForm()
	if login_form.is_submitted():
		if request.form["submit"] == "Login":
			print("Login form submitted")
			username = login_form.username.data
			passwordHash = hash(login_form.password.data, getSalt(username))
			if checkUsernameExists(username):
				if checkPasswordHash(username, passwordHash):
					print("Succesful login\n")
					resp = make_response(redirect('/'))
					resp.set_cookie('username', username, secure=True)
					return resp
				else:
					print("Incorrect Password\n")
					return render_template("login.html", Loginform=login_form, Registerform=register_form, Login_error="Incorrect password, please try again")
			else:
				print("Username not found\n")
				return render_template("login.html", Loginform=login_form, Registerform=register_form, Login_error="Username not found")

		elif request.form["submit"] == "Register":
			print("Register form submitted")
			return render_template("login.html",  Loginform=login_form, Registerform=register_form, Registration_error="beesdff")

	#for the first call, when it's the browser getting the webpage
	return render_template("login.html",  Loginform=login_form, Registerform=register_form)


@app.route("/", methods=["GET", "POST"])
def home():
	username = request.cookies.get('username')
	if username:
		return render_template('home.html', username=username)
	return render_template('home.html')