# flask --app server run


from flask import Flask, redirect, url_for, request, render_template, make_response, session
import time
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import InputRequired
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

#get dbfile
OPTIONSFILE = "options.json"

global boatmanager
boatmanager = backend.BoatManager(OPTIONSFILE)


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

class filterBoatsForm(FlaskForm):
	boatClass = SelectField()
	owner = SelectField()
	LoginSubmit = SubmitField("applyFilters")


class issueDetailsForm(FlaskForm):
	boat = SelectField()
	severity = SelectField(choices=[(0,"0"), (1,"1"), (2,"2"), (3,"3"), (4,"4"), (5,"5")])
	details = StringField()
	fixDate = StringField()

class issuesFilterForm(FlaskForm):
	minSeverity = SelectField(choices=[["0","0"], ["1","1"], ["2","2"], ["3","3"], ["4","4"], ["5","5"]])
	resolved = SelectField(choices=[("0", "Unresolved"), ("1", "Resolved"), ("01", "All")])
	LoginSubmit = SubmitField("applyFilters")


class bookingDetailsForm(FlaskForm):
	boat = SelectField()
	startTime = StringField()
	length = StringField()

class filterBookingsForm(FlaskForm):
	boatClass = SelectField()
	bookingHolder = SelectField()
	date = StringField()


class buttonForm(FlaskForm):
	submit = SubmitField("submit")

@app.route('/', methods=["GET", "POST"])
@app.route('/login', methods=["GET", "POST"])
def login():
	login_form = LoginForm()
	register_form = RegisterForm()

	if login_form.is_submitted(): 
		# This will be True if either form is submitted
		if request.form["submit"] == "Login": 
			# This is only if the login form has been submitted
			print("Login form submitted")
			Username = login_form.Username.data
			if boatmanager.findUserIndex(Username) != -1 or boatmanager.findAdminIndex(Username) != -1:
				passwordHash = boatmanager.hash(login_form.password.data, boatmanager.getUser(Username).getSalt())
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
			# This is only if the registration form has been submitted
			print("Register form submitted")
			Username = register_form.Username.data
			name = register_form.name.data
			email = register_form.email.data
			password = register_form.password.data
			passwordConfirm = register_form.passwordConfirm.data

			validation = boatmanager.validatePasswordInput(password, passwordConfirm)

			salt = boatmanager.generateSalt()
			pwHash = boatmanager.hash(password, salt)

			if validation != True:
				return render_template("login.html", Loginform=login_form, Registerform=register_form, Registration_error=validation)
			userCreation = boatmanager.newUser(Username, name, email, pwHash, salt)
			if userCreation != 1:
				return render_template("login.html", Loginform=login_form, Registerform=register_form, Registration_error=userCreation)

			session["Username"] = Username
			return redirect("/myAccount")

	# For the first call, when it's the browser getting the webpage
	return render_template("login.html",  Loginform=login_form, Registerform=register_form)

@app.route("/users", methods=["GET", "POST"])
def users():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	if boatmanager.findAdminIndex(Username) == -1:
		return redirect("/forbidden")

	collectionItems = [] # This is a list of users to be shown
	if "filter" in request.args:
		# For this page, filters are in the query URL
		if request.args.get("filter") == "Admins":
			for admin in boatmanager.getAdmins():
				collectionItems.append(["grade", admin.getUsername(), admin.getName(), admin.getEmail(), "downgrade", "remove"])
		elif request.args.get("filter") == "Users":
			for user in boatmanager.getUsers():
				collectionItems.append(["person", user.getUsername(), user.getName(), user.getEmail(), "upgrade", "add"])
		else:
			# All Users and Admins are shown
			for admin in boatmanager.getAdmins():
				collectionItems.append(["grade", admin.getUsername(), admin.getName(), admin.getEmail(), "downgrade", "remove"])
			for user in boatmanager.getUsers():
				collectionItems.append(["person", user.getUsername(), user.getName(), user.getEmail(), "upgrade", "add"])
	else:
		# If no filters are specified in the query
		for admin in boatmanager.getAdmins():
			collectionItems.append(["grade", admin.getUsername(), admin.getName(), admin.getEmail(), "downgrade", "remove"])
		for user in boatmanager.getUsers():
			collectionItems.append(["person", user.getUsername(), user.getName(), user.getEmail(), "upgrade", "add"])

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
		# This is if either form is submitted
		if request.form["Apply"] == "ChangeDetails":
			# This is only if the details editing form has been submitted
			print("New user details submitted")
			user = boatmanager.getUser(account)
			attributes = user.getAllAttributes() # [Username, Name, Email, PasswordHash, Salt]
			[account, Name, Email, PasswordHash, Salt] = attributes
			newEmail = DetailsForm.Email.data
			newName = DetailsForm.Name.data

			validation = boatmanager.editUser(attributes[0], newName, newEmail, attributes[3], attributes[4])
			if validation != 1:
				# I.e. An error of some sort has ocurred
				return render_template('editUser.html', Username=account, Name=Name, Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error=validation, Password_error="")
			else:
				return render_template('editUser.html', Username=account, Name=newName, Email=newEmail, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="Succesfully updated values", Password_error="")

		elif request.form["Apply"] == "ChangePassword":
			# This is only if they have attempted to change the password
			print("user attempt to change password submitted")
			attributes = boatmanager.getUser(account).getAllAttributes() # [Username, Name, Email, PasswordHash, Salt]
			[account, Name, Email, PasswordHash, Salt] = attributes

			account = account.replace("'", "")
			Name = Name.replace("'", "")

			oldPassword = PwordForm.oldPassword.data
			newpassword = PwordForm.password.data
			newpasswordConfirm = PwordForm.passwordConfirm.data

			if boatmanager.hash(oldPassword, Salt) != PasswordHash and boatmanager.findAdminIndex(Username) == -1:
				return render_template('editUser.html', Username=account, Name=Name, Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error="Incorrect old password")

			if boatmanager.validatePasswordInput(newpassword, newpasswordConfirm) != True:
				return render_template('editUser.html', Username=account, Name=Name, Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error=boatmanager.validatePasswordInput(newpassword, newpasswordConfirm))

			if newpassword != newpasswordConfirm:
				return render_template('editUser.html', Username=account, Name=Name, Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error="passwords don't match")
			
			newPasswordHash = boatmanager.hash(newpassword, Salt)
			validation = boatmanager.editUser(account, Name, Email, newPasswordHash, Salt)

			if validation != 1:
				# I.e. An error of some sort has ocurred
				return render_template('editUser.html', Username=account, Name=Name, Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error=validation)
			else:
				return render_template('editUser.html', Username=account, Name=Name, Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error="Succesfully updated values")

	User = boatmanager.getUser(account)
	Name = User.getName()
	Email = User.getEmail()
	account = account.replace("'", "")
	Name = Name.replace("'", "")
	return render_template('editUser.html', Username=account, Name=Name, Email=Email, EditDetailsForm=DetailsForm, EditPasswordForm=PwordForm, Details_error="", Password_error="")

@app.route("/confirmedDeleteAccount", methods=["GET", "POST"])
def confirmedDeleteAccount():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	account = request.args.get("account")
	if account == boatmanager.getOptions()["sysAdminUsername"]:
		return redirect("/forbidden")
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
			return render_template('myAccount.html', user=Username, Email=UserObject.getEmail(), Name=UserObject.getName(), logoutForm=logout_form, delAccForm=delAcc_form)
	UserObject = boatmanager.getUser(Username)
	return render_template('myAccount.html', user=Username, Email=UserObject.getEmail(), Name=UserObject.getName(), logoutForm=logout_form, delAccForm=delAcc_form)



@app.route("/boats", methods=["GET", "POST"])
def boats():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	collectionItems = []

	boatmanager.sortBoats()
	userList = ["All"] + [user.getUsername() for user in (boatmanager.getAdmins() + boatmanager.getUsers())]
	classList = ["All"] + [boat.getType() for boat in boatmanager.getBoats()]



	boatFilterForm = filterBoatsForm()
	boatFilterForm.owner.choices = userList
	boatFilterForm.boatClass.choices = classList

	if boatFilterForm.is_submitted():
		potentialBoats = []
		ownerFilter = boatFilterForm.owner.data
		boatClassFilter = boatFilterForm.boatClass.data

		for boat in boatmanager.getBoats():
			Owner = boatmanager.getUser(boat.getOwner())
			potentialBoats.append([boat.getID(), boat.getName(), boat.getType(), boat.getComments(), Owner.getUsername(), Owner.getName()])

		if ownerFilter != "All":
			for item in potentialBoats:
				if item[4] != ownerFilter:
					potentialBoats.remove(item)

		if boatClassFilter != "All":
			for item in potentialBoats:
				if item[2] != boatClassFilter:
					print("l375", item[2], boatClassFilter)
					potentialBoats.remove(item)

		collectionItems = potentialBoats

	else:
		for boat in boatmanager.getBoats():
			Owner = boatmanager.getUser(boat.getOwner())
			collectionItems.append([boat.getID(), boat.getName(), boat.getType(), boat.getComments(), Owner.getUsername(), Owner.getName()])

	message=""
	if "msg" in request.args:
		if request.args["msg"] == "boatCreationSuccess":
			message = "Succesfully created boat"

	return render_template('boats.html', user=Username, message=message, collectionItems=collectionItems, boatFilterForm=boatFilterForm)

@app.route("/newBoat", methods=["GET", "POST"])
def newBoat():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	if boatmanager.findAdminIndex(Username) == -1 and not boatmanager.getOptions()["UniversalBoatEditing"]:
		return redirect("/forbidden")

	accountsList = []

	for account in boatmanager.getUsers():
		accountsList.append([account.getUsername(), (account.getUsername() + " (" + account.getName() + ")")])

	for account in boatmanager.getAdmins():
		accountsList.append([account.getUsername(), (account.getUsername() + " (" + account.getName() + ")")])

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
		accountsList.append([account.getUsername(), (account.getUsername() + " (" + account.getName() + ")")])
	for account in boatmanager.getAdmins():
		accountsList.append([account.getUsername(), (account.getUsername() + " (" + account.getName() + ")")])

	editBoatForm = boatDetailsForm()
	editBoatForm.owner.choices = accountsList

	boat = boatmanager.getBoat(BoatID)
	boatName = boat.getName()
	boatType = boat.getType()
	owner = boat.getOwner()
	comments = boat.getComments()

	if editBoatForm.is_submitted():
		newBoatName = editBoatForm.boatName.data
		newBoatType = editBoatForm.boatType.data
		newOwner = editBoatForm.owner.data
		newComments = editBoatForm.comments.data

		boatEdit = boatmanager.editBoat(BoatID, newBoatName, newBoatType, newOwner, newComments)
		if boatEdit != 1:
			return render_template("editBoat.html", message=boatEdit, editBoatForm=editBoatForm, boatID=BoatID, boatName=boatName, boatType=boatType, owner=owner, comments=comments)
		return render_template("editBoat.html", message="Successfully upated values", editBoatForm=editBoatForm, boatID=BoatID, boatName=newBoatName, boatType=newBoatType, owner=newOwner, comments=newComments)

	return render_template("editBoat.html", editBoatForm=editBoatForm, BoatID=BoatID, boatName=boatName, boatType=boatType, owner=owner, comments=comments)

@app.route("/deleteBoat", methods=["GET", "POST"])
def deleteBoat():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	BoatID = request.args.get("boat")
	if boatmanager.getOptions()["UniversalBoatEditing"] or boatmanager.getAdmin(Username) != -1:
		return redirect("/boats")
	else:
		return redirect("/forbidden")



@app.route("/bookings", methods=["GET", "POST"])
def bookings():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	collectionItems = []

	if not boatmanager.getOptions()["AllowBookings"]:
		return redirect("/forbidden")

	boatmanager.sortBookings()
	for booking in boatmanager.getBookings():
		# BookingID, Username, BoatID, BoatName, Date, startTime, endTime, length
		if int(booking.getStartTime()) + int(booking.getLength())*60 > datetime.now().timestamp():
			boatName = boatmanager.getBoat(booking.getBoatID()).getName()
			boatType = boatmanager.getBoat(booking.getBoatID()).getType()
			startTime = datetime.fromtimestamp(int(booking.getStartTime())).isoformat()
			print("l498", startTime, datetime.fromtimestamp(int(booking.getStartTime())))
			endTime = datetime.fromtimestamp(int(booking.getStartTime())+int(booking.getLength())*60).isoformat()

			User = boatmanager.getUser(booking.getUsername())
			collectionItems.append([booking.getBookingID(), User.getUsername(), User.getName(), booking.getBoatID(), 
				boatName, startTime[:10], startTime[-8:-3], endTime[-8:-3], booking.getLength(), boatType])

	userList = ["All"] + [user.getUsername() for user in (boatmanager.getAdmins() + boatmanager.getUsers())]
	classList = ["All"] + [boat.getType() for boat in boatmanager.getBoats()]
	bookingFilterForm = filterBookingsForm()

	bookingFilterForm.bookingHolder.choices = userList
	bookingFilterForm.boatClass.choices = classList

	if bookingFilterForm.is_submitted():
		if bookingFilterForm.boatClass.data != "All":
			for item in collectionItems:
				if item[9] != bookingFilterForm.boatClass.data:
					collectionItems.remove(item)
		if bookingFilterForm.bookingHolder.data != "All":
			for item in collectionItems:
				if item[1] != bookingFilterForm.bookingHolder.data:
					collectionItems.remove(item)
		if bookingFilterForm.date.data != "":
			for item in collectionItems:
				if item[5] != bookingFilterForm.date.data:
						collectionItems.remove(item)
	

	message=""
	if "msg" in request.args:
		if request.args["msg"] == "bookingCreationSuccess":
			message = "Succesfully created booking"

	return render_template('bookings.html', message=message, collectionItems=collectionItems, bookingFilterForm=bookingFilterForm)

@app.route("/newBooking", methods=["GET", "POST"])
def newBooking():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]

	if not boatmanager.getOptions()["AllowBookings"]:
		return redirect("/forbidden")

	boatsList = []

	for boat in boatmanager.getBoats():
		boatsList.append([boat.getID(), (boat.getID() + " (" + boat.getName() + ")")])

	newBookingForm = bookingDetailsForm()
	newBookingForm.boat.choices=boatsList

	if newBookingForm.is_submitted():
		print("New boat being created")
		boatID = newBookingForm.boat.data
		startTime = newBookingForm.startTime.data
		if startTime == None:
			return render_template("newBooking.html", newBookingForm=newBookingForm, bookingCreation_error="start time is required")
		length = newBookingForm.length.data
		if length == None:
			return render_template("newBooking.html", newBookingForm=newBookingForm, bookingCreation_error="length is required")
		bookingID = boatmanager.getNewBookingID()

		startUnixTime = datetime.fromisoformat(startTime).timestamp()

		bookingCreation = boatmanager.newBooking(bookingID, Username, boatID, startUnixTime, length)
		if bookingCreation != 1:
			return render_template("newBooking.html", newBookingForm=newBookingForm, bookingCreation_error=bookingCreation)
		return redirect("/bookings?msg=bookingCreationSuccess")

	return render_template("newBooking.html", newBookingForm=newBookingForm)

@app.route("/editBooking", methods=["GET", "POST"])
def editBooking():
	if "Username" not in session:
		return redirect("/login")

	Username = session["Username"]
	BookingID = request.args.get("booking")

	if not boatmanager.getOptions()["UniversalBookingEditing"] and boatmanager.getAdmin(Username) == -1 and boatmanager.getBooking(BookingID).getName() != Username:
		return redirect("/forbidden")

	boatsList = []
	for boat in boatmanager.getBoats():
		boatsList.append([boat.getID(), (boat.getID() + " (" + boat.getName() + ")")])

	editBookingForm = bookingDetailsForm()
	editBookingForm.boat.choices = boatsList

	booking = boatmanager.getBooking(BookingID)
	bookingHolder = booking.getUsername()
	creationDate = booking.getCreationDate()
	bookingID = booking.getBookingID()
	boatID = booking.getBoatID()
	startDateTime = datetime.fromtimestamp(int(booking.getStartTime())).isoformat()
	length = booking.getLength()

	if editBookingForm.is_submitted():
		newBoatID = editBookingForm.boat.data
		newStartDateTime = editBookingForm.startTime.data
		newLength = editBookingForm.length.data

		bookingEdit = boatmanager.editBooking(BookingID, bookingHolder, newBoatID, datetime.fromisoformat(newStartDateTime).timestamp(), newLength, creationDate)
		if bookingEdit != 1:
			return render_template("editBooking.html", message=bookingEdit, editBookingForm=editBookingForm, BookingID=BookingID, boatID=boatID, dateTime=startDateTime, length=length)
		return render_template("editBooking.html", message="Successfully upated values", editBookingForm=editBookingForm, BookingID=BookingID, boatID=newBoatID, dateTime=newStartDateTime, length=newLength)

	return render_template("editBooking.html", message="", editBookingForm=editBookingForm, BookingID=BookingID, boatID=boatID, dateTime=startDateTime, length=length)



@app.route("/deleteBooking", methods=["GET", "POST"])
def deleteBooking():
	if not boatmanager.getOptions()["AllowBookings"]:
		return redirect("/forbidden")
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	BookingID = request.args.get("booking")
	boatmanager.deleteBooking(BookingID)
	return redirect("/bookings")
	


@app.route("/issues", methods=["GET", "POST"])
def issues():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	collectionItems = []

	filterIssuesForm = issuesFilterForm()

	boatmanager.sortIssues()
	for issue in boatmanager.getIssues():
		# Issue number, BoatID, BoatName, Creator, creationdate, severity, details, fixdate, resolved
		if issue.getResolved() == 0:
			icon = "check_box_outline_blank"
			resolved = "Resolved"
		else:
			icon = "check_box"
			resolved = "Unresolved"

		if issue.getFixDate() == "":
			fixDate = "Not set"
		else:
			fixDate = issue.getFixDate()
		readableCreationDate = str(datetime.fromtimestamp(issue.getCreationDate()).replace(microsecond=0).isoformat(" "))
		boat = boatmanager.getBoat(issue.getBoatID())
		creator = boatmanager.getUser(issue.getCreator())
		collectionItems.append([issue.getIssueID(), issue.getBoatID(), boat.getName(), boat.getType(), creator.getUsername(), creator.getName(), 
			readableCreationDate, str(issue.getSeverity()), issue.getDetails(), fixDate, str(issue.getResolved()), icon, resolved])


	if filterIssuesForm.is_submitted():
		# sort according to the filters applied
		resolvedFilter = filterIssuesForm.resolved.data
		for issue in collectionItems:
			if int(issue[7]) < int(filterIssuesForm.minSeverity.data) and issue[10] not in resolvedFilter:
				# Issue number, BoatID, BoatName, Creator, creationdate, severity, details, fixdate, resolved
				collectionItems.remove(issue)

	else:
		# only show unresolved issues
		for issue in collectionItems:
			if issue[10] == "1":
				collectionItems.remove(issue)

	message=""
	if "msg" in request.args:
		if request.args["msg"] == "issueCreationSuccess":
			message = "Succesfully created issue"

	return render_template('issues.html', message=message, collectionItems=collectionItems, filterIssuesForm=filterIssuesForm)

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


		issueCreation = boatmanager.newIssue(issueID, Username, boatID, Details=details, FixDate=fixDate, Severity=severity, Resolved=0)
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
	boatmanager.deleteIssue(IssueID)
	return redirect("/issues")

@app.route("/markIssueResolved", methods=["GET", "POST"])
def markIssueResolved():
	if "Username" not in session:
		return redirect("/login")
	Username = session["Username"]
	IssueID = request.args.get("issue")
	issue = boatmanager.getIssue(IssueID)
	if boatmanager.findAdminIndex(Username) == -1 and not boatmanager.getOptions()["UniversalIssueEditing"]:
		return redirect("/forbidden")
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

	issue = boatmanager.getIssue(IssueID)
	BoatID = issue.getBoatID()
	BoatName = boatmanager.getBoat(BoatID).getName()
	Creator = issue.getCreator()
	CreationDate = issue.getCreationDate()
	Details = issue.getDetails()
	FixDate = issue.getFixDate()
	Severity = issue.getSeverity()
	Resolved = issue.getResolved()

	editIssueForm = issueDetailsForm()
	editIssueForm.boat.choices=boatsList
	editIssueForm.boat.default=BoatID
	editIssueForm.severity.default=Severity
	editIssueForm.process()


	if editIssueForm.is_submitted():
		issue = boatmanager.getIssue(IssueID)
		newBoatID = editIssueForm.boat.data
		newBoatName = boatmanager.getBoat(BoatID).getName()
		newDetails = editIssueForm.details.data
		newFixDate = editIssueForm.fixDate.data
		newSeverity = editIssueForm.severity.data

		issueEdit = boatmanager.editIssue(IssueID, Creator, newBoatID, CreationDate, newDetails, newFixDate, newSeverity, Resolved)
		if issueEdit != 1:
			return render_template("editIssue.html", message=issueEdit, editIssueForm=editIssueForm, IssueID=IssueID, BoatID=BoatID, 
			BatName=BoatName, CreationDate=CreationDate, Details=Details, FixDate=FixDate, Severity=Severity, Resolved=Resolved)
		return render_template("editIssue.html", message="Successfully upated values", editIssueForm=editIssueForm, IssueID=IssueID, BoatID=newBoatID, 
			BatName=newBoatName, CreationDate=CreationDate, Details=newDetails, FixDate=newFixDate, Severity=newSeverity, Resolved=Resolved)

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