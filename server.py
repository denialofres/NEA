# flask --app server run


from flask import Flask, redirect, url_for, request, render_template, make_response, session
import time
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
import sqlite3
import json
import backend
import random
import string

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SECRET_KEY"] = "Unicorns"

login_history = []

global boatmanager
boatmanager = backend.BoatManager("options.json")

#get dbfile
optionsFile = "options.json"
with open(optionsFile, "r") as optionsFileObject:
	options = json.load(optionsFileObject)

DBFILE = options["dbfile"]

#check dbfile exists
try:
	with open(DBFILE) as DB:
		pass
except FileNotFoundError:
	print(f"dbfile ({DBFILE}) not found")
	quit()


def generateSalt():
	chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
	salt = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
	return salt

def hash(Password, Salt):
	hash = 14
	for i in list(Salt)+list(Password):
		hash = (hash * 65599) + ord(i)
	return str(hash)

def getSalt(Username):
	conn = sqlite3.connect(DBFILE)
	cursor = conn.cursor() 

	cursor.execute(f"SELECT Salt FROM Users WHERE Username = '{Username}'")
	for item in cursor:
		salt = item[0]
	conn.close()
	return salt

def checkUsernameExists(Username):
	conn = sqlite3.connect(DBFILE)
	cursor = conn.cursor() 

	UserHashData = cursor.execute(f"SELECT Username FROM Users WHERE Username = '{Username}'")
	numUsers = len(cursor.fetchall())

	conn.close()

	if numUsers > 0:
		return True
	return False

def validatePassword(password, passwordConfirm):
	if password != passwordConfirm:
		print(password, passwordConfirm)
		return "Passwords don't match"
	if len(password) < 6:
		return "Password is too short"
	return True



class LoginForm(FlaskForm):
	Username = StringField("Username")
	password = StringField("Password")
	LoginSubmit = SubmitField("Log In")

class RegisterForm(FlaskForm):
	Username = StringField("Username")
	name = StringField("name")
	email = StringField("Email")
	password = StringField("Password")
	passwordConfirm = StringField("password_confirmation")
	RegisterSubmit = SubmitField("Log In")

class EditUserDetailsForm(FlaskForm):
	Username = StringField("Username")
	Name = StringField("Name")
	Email = StringField("Email")
	Apply = SubmitField("Apply")

class EditUserPasswordForm(FlaskForm):
	oldPassword = StringField("oldPassword")
	password = StringField("Password")
	passwordConfirm = StringField("password_confirmation")
	Apply = SubmitField("Apply")

class boatDetailsForm(FlaskForm):
	boatName = StringField("BoatName")
	boatType = StringField("BoatType")
	owner = SelectField()
	comments = StringField("Comments")
	LoginSubmit = SubmitField("createBoat")

class issueDetailsForm(FlaskForm):
	boat = SelectField()
	severity = SelectField(choices=[(0,"0"), (1,"1"), (2,"2"), (3,"3"), (4,"4"), (5,"5")])
	details = StringField()
	fixDate = StringField()

class buttonForm(FlaskForm):
	submit = SubmitField("submit")

@app.route('/', methods=["GET", "POST"])
@app.route('/login', methods=["GET", "POST"])
def login():
	login_form = LoginForm()
	register_form = RegisterForm()
	if login_form.is_submitted():
		if request.form["submit"] == "Login":
			print("Login form submitted")
			Username = login_form.Username.data
			if checkUsernameExists(Username):
				passwordHash = hash(login_form.password.data, getSalt(Username))
				User = boatmanager.getUser(Username)
				if User.getPasswordHash() == passwordHash:
					print("Succesful login\n")
					session["Username"] = Username
					return redirect("/myAccount")
				else:
					print("Incorrect Password\n")
					return render_template("login.html", Loginform=login_form, Registerform=register_form, Login_error="Incorrect password, please try again")
			else:
				print("Username not found\n")
				return render_template("login.html", Loginform=login_form, Registerform=register_form, Login_error="Username not found")

		elif request.form["submit"] == "Register":
			print("Register form submitted")
			Username = register_form.Username.data
			name = register_form.name.data
			name = name.split()
			email = register_form.email.data
			password = register_form.password.data
			passwordConfirm = register_form.passwordConfirm.data

			validation = validatePassword(password, passwordConfirm)

			salt = generateSalt()
			pwHash = hash(password, salt)

			if validation != True:
				return render_template("login.html", Loginform=login_form, Registerform=register_form, Registration_error=validation)
			userCreation = boatmanager.newUser(Username, name, email, pwHash, salt)
			if userCreation != 1:
				return render_template("login.html", Loginform=login_form, Registerform=register_form, Registration_error=userCreation)

			session["Username"] = Username
			return redirect("/myAccount")

	#for the first call, when it's the browser getting the webpage
	return render_template("login.html",  Loginform=login_form, Registerform=register_form)

@app.route("/users", methods=["GET", "POST"])
def users():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	if boatmanager.findAdminIndex(Username) == -1:
		return redirect("/forbidden")

	collectionItems = []

	for admin in boatmanager.getAdmins():
		collectionItems.append(["grade", admin.getUsername(), " ".join(admin.getName()), admin.getEmail(), "downgrade", "remove"])


	for user in boatmanager.getUsers():
		collectionItems.append(["person", user.getUsername(), " ".join(user.getName()), user.getEmail(), "upgrade", "add"])

	return render_template("users.html", collectionItems=collectionItems)

@app.route("/editUser", methods=["GET", "POST"])
def editUser():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	account = request.args.get("account")

	if boatmanager.findAdminIndex(Username) == -1 and Username != account:
		return redirect("/forbidden")

	DetailsForm = EditUserDetailsForm()
	PwordForm = EditUserPasswordForm()
	if DetailsForm.is_submitted():
		if request.form["Apply"] == "ChangeDetails":
			print("New user details submitted")
			user = boatmanager.getUser(account)
			attributes = user.getAllAttributes() # [Username, Name, Email, PasswordHash, Salt]
			[account, Name, Email, PasswordHash, Salt] = attributes
			newEmail = DetailsForm.Email.data
			newName = DetailsForm.Name.data.split(" ")
			validation = boatmanager.editUser(attributes[0], newName, newEmail, attributes[3], attributes[4])
			if validation != 1:
				return render_template('editUser.html', Username=account, Name=" ".join(Name), Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error=validation, Password_error="")
			else:
				return render_template('editUser.html', Username=account, Name=" ".join(newName), Email=newEmail, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="Succesfully updated values", Password_error="")

		elif request.form["Apply"] == "ChangePassword":
			print("user attempt to change password submitted")
			attributes = boatmanager.getUser(account).getAllAttributes() # [Username, Name, Email, PasswordHash, Salt]
			[account, Name, Email, PasswordHash, Salt] = attributes

			oldPassword = PwordForm.oldPassword.data
			newpassword = PwordForm.password.data
			newpasswordConfirm = PwordForm.passwordConfirm.data

			if hash(oldPassword, Salt) != PasswordHash and boatmanager.findAdminIndex(Username) == -1:
				return render_template('editUser.html', Username=account, Name=" ".join(Name), Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error="Incorrect old password")

			if newpassword != newpasswordConfirm:
				return render_template('editUser.html', Username=account, Name=" ".join(Name), Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error="passwords don't match")
			
			newPasswordHash = hash(newpassword, Salt)
			validation = boatmanager.editUser(account, Name, Email, newPasswordHash, Salt)

			if validation != 1:
				return render_template('editUser.html', Username=account, Name=" ".join(Name), Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error=validation)
			else:
				return render_template('editUser.html', Username=account, Name=" ".join(Name), Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error="Succesfully updated values")

	User = boatmanager.getUser(account)
	Name = User.getName()
	Email = User.getEmail()
	return render_template('editUser.html', Username=account, Name=" ".join(Name), Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error="")

@app.route("/deleteAccount", methods=["GET", "POST"])
def deleteAccount():
	pass

@app.route("/confirmedDeleteAccount", methods=["GET", "POST"])
def confirmedDeleteAccount():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	account = request.args.get("account")
	if account == Username:
		boatmanager.deleteUser(account)
		return redirect("/login")
	elif boatmanager.findAdminIndex(Username) != -1:
		boatmanager.deleteUser(account)
		return redirect("/users")
	else:
		return redirect("/forbidden")

@app.route("/upgradeUser", methods=["GET", "POST"])
def upgradeUser():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	account = request.args.get("account")
	if boatmanager.findAdminIndex(Username) != -1:
		boatmanager.giveAdminPerms(account)
		return redirect("/users")
	else:
		return redirect("/forbidden")

@app.route("/downgradeUser", methods=["GET", "POST"])
def downgradeUser():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	account = request.args.get("account")
	if boatmanager.findAdminIndex(Username) == -1 or Username == account:
		return redirect("/forbidden")

	else:
		boatmanager.removeAdminPerms(account)
		return redirect("/users")

@app.route("/myAccount", methods=["GET", "POST"])
def myAccount():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	logout_form = buttonForm()
	delAcc_form = buttonForm()

	if logout_form.is_submitted():
		if request.form["submit"] == "logout":
			session.pop("Username")
			return redirect("/login")
		elif request.form["submit"] == "delAcc":
			return render_template('myAccount.html', user=Username, Email=UserObject.getEmail(), Name=" ".join(UserObject.getName()), logoutForm=logout_form, delAccForm=delAcc_form)
	UserObject = boatmanager.getUser(Username)
	return render_template('myAccount.html', user=Username, Email=UserObject.getEmail(), Name=" ".join(UserObject.getName()), logoutForm=logout_form, delAccForm=delAcc_form)



@app.route("/boats", methods=["GET", "POST"])
def boats():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	collectionItems = []

	for boat in boatmanager.getBoats():
		collectionItems.append([boat.getID(), boat.getName(), boat.getType(), boat.getComments(), boat.getOwner()])

	message=""
	if "msg" in request.args:
		if request.args["msg"] == "boatCreationSuccess":
			message = "Succesfully created boat"

	return render_template('boats.html', user=Username, message=message, collectionItems=collectionItems)

@app.route("/newBoat", methods=["GET", "POST"])
def newBoat():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	if boatmanager.findAdminIndex(Username) == -1 and not boatmanager.getOptions()["UniversalBoatEditing"]:
		return redirect("/forbidden")

	accountsList = []

	for account in boatmanager.getUsers():
		accountsList.append([account.getUsername(), (account.getUsername() + " (" + ' '.join(account.getName()) + ")")])

	for account in boatmanager.getAdmins():
		accountsList.append([account.getUsername(), (account.getUsername() + " (" + ' '.join(account.getName()) + ")")])

	newBoatForm = boatDetailsForm()
	newBoatForm.owner.choices=accountsList

	if newBoatForm.is_submitted():
		print("New boat being created")
		boatName = newBoatForm.boatName.data
		boatType = newBoatForm.boatType.data
		owner = newBoatForm.owner.data
		comments = newBoatForm.comments.data
		BoatID = boatmanager.getNewBoatID()

		boatCreation = boatmanager.newBoat(BoatID, boatName, boatType, owner, comments)
		if boatCreation != 1:
			return render_template("newBoat.html", newBoatForm=newBoatForm, boatCreation_error=boatCreation)
		return redirect("/boats?msg=boatCreationSuccess")		

	return render_template("newBoat.html", newBoatForm=newBoatForm)

@app.route("/deleteBoat", methods=["GET", "POST"])
def deleteBoat():
	pass

@app.route("/confirmedDeleteBoat", methods=["GET", "POST"])
def confirmedDeleteBoat():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	BoatID = request.args.get("BoatID")
	if boatmanager.getOptions()["UniversalBoatEditing"] or boatmanager.getAdmin(Username) != -1:
		boatmanager.deleteBoat(BoatID)
		return redirect("/boats")
	else:
		return redirect("/forbidden")

@app.route("/editBoat", methods=["GET", "POST"])
def editBoat():
	if "Username" not in session:
		return redirect("/login")

	Username = session["Username"]
	BoatID = request.args.get("BoatID")

	if not boatmanager.getOptions()["UniversalBoatEditing"] and boatmanager.getAdmin(Username) == -1:
		return redirect("/forbidden")

	accountsList = []
	for account in boatmanager.getUsers():
		accountsList.append([account.getUsername(), (account.getUsername() + " (" + ' '.join(account.getName()) + ")")])
	for account in boatmanager.getAdmins():
		accountsList.append([account.getUsername(), (account.getUsername() + " (" + ' '.join(account.getName()) + ")")])

	editBoatForm = boatDetailsForm()
	editBoatForm.owner.choices = accountsList

	if editBoatForm.is_submitted():
		newBoatName = editBoatForm.boatName.data
		newBoatType = editBoatForm.boatType.data
		newOwner = editBoatForm.owner.data
		newComments = editBoatForm.comments.data

		boatEdit = boatmanager.editBoat(BoatID, newBoatName, newBoatType, newOwner, newComments)
		if boatEdit != 1:
			return render_template("editBoat.html", message=boatEdit, editBoatForm=editBoatForm, boatID=BoatID, boatName=boatName, boatType=boatType, owner=owner, comments=comments)
		return render_template("editBoat.html", message="Successfully upated values", editBoatForm=editBoatForm, boatID=BoatID, boatName=newBoatName, boatType=newBoatType, owner=newOwner, comments=newComments)

	boat = boatmanager.getBoat(BoatID)
	boatName = boat.getName()
	boatType = boat.getType()
	owner = boat.getOwner()
	comments = boat.getComments()

	return render_template("editBoat.html", editBoatForm=editBoatForm, BoatID=BoatID, boatName=boatName, boatType=boatType, owner=owner, comments=comments)



@app.route("/bookings", methods=["GET", "POST"])
def bookings():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	print(Username)
	if Username:
		return render_template('home.html', user=Username)



@app.route("/issues", methods=["GET", "POST"])
def issues():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	collectionItems = []

	boatmanager.sortIssues()
	for issue in boatmanager.getIssues():
		# Issue number, BoatID, BoatName, Creator, creationdate, severity, details, fixdate, resolved
		if issue.getResolved() == 0:
			icon = "check_box_outline_blank"
			resolved = "Resolved"
		else:
			icon = "check_box"
			resolved = "Unresolved"

		if issue.getFixDate() == None:
			fixDate = "Not set"
		else:
			fixDate = issue.getFixDate()
		readableCreationDate = str(datetime.fromtimestamp(issue.getCreationDate()).replace(microsecond=0).isoformat(" "))
		collectionItems.append( [issue.getIssueID(), issue.getBoatID(), boatmanager.getBoat(issue.getBoatID()).getName(), issue.getCreator(), 
			readableCreationDate, str(issue.getSeverity()), issue.getDetails(), fixDate, str(issue.getResolved()), icon, resolved])


	message=""
	if "msg" in request.args:
		if request.args["msg"] == "boatCreationSuccess":
			message = "Succesfully created boat"

	return render_template('issues.html', message=message, collectionItems=collectionItems)

@app.route("/newIssue", methods=["GET", "POST"])
def newIssue():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	boatsList = []

	for boat in boatmanager.getBoats():
		boatsList.append([boat.getID(), (boat.getID() + " (" + boat.getName() + ")")])

	newIssueForm = issueDetailsForm()
	newIssueForm.boat.choices=boatsList

	if newIssueForm.is_submitted():
		print("New boat being created")
		boatID = newIssueForm.boat.data
		severity = newIssueForm.severity.data
		details = newIssueForm.details.data
		fixDate = newIssueForm.fixDate.data
		issueID = boatmanager.getNewIssueID()

		issueCreation = boatmanager.newIssue(issueID, Username, boatID, Details=details, FixDate=fixDate, Severity=severity, Resolved=False)
		if issueCreation != 1:
			return render_template("newIssue.html", newIssueForm=newIssueForm, issueCreation_error=issueCreation)
		return redirect("/issues?msg=issueCreationSuccess")

	return render_template("newIssue.html", newIssueForm=newIssueForm)

@app.route("/deleteIssue", methods=["GET", "POST"])
def deleteIssue():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	IssueID = request.args.get("issue")
	if boatmanager.getOptions()["UniversalIssueEditing"] or boatmanager.getAdmin(Username) != -1:
		boatmanager.deleteIssue(IssueID)
		return redirect("/issues")
	else:
		return redirect("/forbidden")

@app.route("/markIssueResolved", methods=["GET", "POST"])
def markIssueResolved():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	IssueID = request.args.get("issue")
	issue = boatmanager.getIssue(IssueID)
	boatmanager.editIssue(IssueID, issue.getCreator(), issue.getBoatID(), 
		issue.getCreationDate(), issue.getDetails(), issue.getFixDate(), issue.getSeverity(), 1)
	return redirect("/issues")

@app.route("/markIssueUnresolved", methods=["GET", "POST"])
def markIssueUnresolved():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	IssueID = request.args.get("issue")
	issue = boatmanager.getIssue(IssueID)
	boatmanager.editIssue(IssueID, issue.getCreator(), issue.getBoatID(), 
		issue.getCreationDate(), issue.getDetails(), issue.getFixDate(), issue.getSeverity(), 0)
	return redirect("/issues")

@app.route("/editIssue", methods=["GET", "POST"])
def editIssue():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	IssueID = request.args.get("issue")

	boatsList = []

	for boat in boatmanager.getBoats():
		boatsList.append([boat.getID(), (boat.getID() + " (" + boat.getName() + ")")])

	editIssueForm = issueDetailsForm()
	editIssueForm.boat.choices=boatsList

	if editIssueForm.is_submitted():
		issue = boatmanager.getIssue(IssueID)
		newBoatID = editIssueForm.BoatID.data
		newBoatName = boatmanager.getBoat(BoatID).getName()
		newDetails = issue.getDetails()
		newFixDate = issue.getFixDate()
		newSeverity = issue.getSeverity()

		issueEdit = boatmanager.editIssue(IssueID, newBoatID, newCreationDate, newDetails, newFixDate, newSeverity, newResolved)
		if issueEdit != 1:
			return render_template("editIssue.html", message=issueEdit, editIssueForm=editIssueForm, IssueID=IssueID, 
				BoatID=BoatID, BatName=BoatName, CreationDate=CreationDate, Details=Details, FixDate=FixDate, Severity=Severity, Resolved=Resolved)
		return render_template("editIssue.html", message="Successfully upated values", editBoatForm=editIssueForm, IssueID=IssueID, BoatID=newBoatID, 
			BatName=newBoatName, CreationDate=CreationDate, Details=newDetails, FixDate=newFixDate, Severity=newSeverity, Resolved=Resolved)

	issue = boatmanager.getIssue(IssueID)
	BoatID = issue.getBoatID()
	BoatName = boatmanager.getBoat(BoatID).getName()
	CreationDate = issue.getCreationDate()
	Details = issue.getDetails()
	FixDate = issue.getFixDate()
	Severity = issue.getSeverity()
	Resolved = issue.getResolved()

	return render_template("editIssue.html", editIssueForm=editIssueForm, IssueID=IssueID, 
		BoatID=BoatID, BatName=BoatName, CreationDate=CreationDate, Details=Details, FixDate=FixDate, Severity=Severity, Resolved=Resolved)





@app.route("/forbidden", methods=["GET", "POST"])
def forbidden():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	return render_template('forbidden.html', user=Username)

@app.route("/test", methods=["GET", "POST"])
def test():
	return render_template('test.html')