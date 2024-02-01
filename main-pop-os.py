import sqlite3
from sqlite3 import Error
import time

def Main():
	# import settings
	# run boatManager with correct settings
	program = BoatManager("datafile.db", False)
	a = Admin("beezlebub", "me@wtf", "pwordhash123", "9ol.PL", "John Smith")
	a.getIsAdmin()

class BoatManager:
	def __init__(self, dbfile, optionsFile):
		print("BoatManager init")
		self.__dbfile = dbfile
		try:
			with open(self.__dbfile) as DB:
				pass
		except FileNotFoundError:
			self.setupDatabase(self.__dbfile)
		self.loadDatabase()




	def setupDatabase(self, dbfile):
		print(1)
		conn = sqlite3.connect(dbfile)
		cursor = conn.cursor()
		# Make Users table
		cursor.execute("""CREATE TABLE Users (
			UserName varChar(30) NOT NULL,
			Email varChar(255) NOT NULL,
			PasswordHash varChar(60) NOT NULL,
			Salt varChar(6) NOT NULL,
			Firstname varChar(30) NOT NULL,
			Lastname varChar(30) NOT NULL,
			IsAdmin Bool NOT NULL,   
			Primary key (userName)
						);""")

		# Make Boats table
		cursor.execute("""CREATE TABLE Boats (
			BoatID varChar(4) NOT NULL,
			BoatName varChar(30) NOT NULL,
			BoatType varChar(30) NOT NULL,
			Owner varChar(30),
			Comments varChar(511),
			Primary key (BoatID),
			Foreign key (Owner) references Users(UserName)
			);""")

		# Make Bookings table
		cursor.execute("""CREATE TABLE Bookings (
			BookingID varChar(5) NOT NULL,
			UserName varChar(30) NOT NULL,
			BoatID varChar(4) NOT NULL,
			Datetime Integer NOT NULL,
			Length int NOT NULL,
			CreationDate Integer NOT NULL,
			Primary key (BookingID),
			Foreign key (UserName) references Users(UserName),
			Foreign key (BoatID) references Boats(BoatID)
			);""")

		# Make Issues table
		cursor.execute("""CREATE TABLE Issues (
			IssueID varChar(6) NOT NULL,
			Creator varChar(30) NOT NULL,
			BoatID varChar(4) NOT NULL,
			CreationDate Integer NOT NULL,
			FixDate Integer,
			Severity Integer NOT NULL,
			Resolved Boolean NOT NULL,
			Primary key (IssueID),
			Foreign key (Creator) references Users(UserName),
			Foreign key (BoatID) references Boats(BoatID)
			);""")

		conn.close()

	def loadDatabase(self, dbfile):
		conn = sqlite3.connect(dbfile)
		cursor = conn.cursor()
		Users = []
		Admins = []
		UserData = cursor.execute("SELECT UserName, Email, PasswordHash, Salt, Firstname, Lastname, IsAdmin")
		for user in UserData:
			if user[6] == 0:
				Users.append(User(user[0], user[1], user[2], user[3], (user[4], user[5])))
			else:
				Admins.append(Admins(Admin[0], Admin[1], Admin[2], Admin[3], (Admin[4], Admin[5])))

		conn.close()

	def newUser(self, userName, Email, PasswordHash, Salt, Name):
		Users.append(User(userName, Email, PasswordHash, Salt, Name))
		conn = sqlite3.connect(dbfile)
		conn.execute(f"""
			INSERT INTO Users (UserName, Email, PasswordHash, Salt, Firstname, Lastname, isAdmin)
			VALUES ('{}', '', '','', '', '', )

			""")


class User():
	def __init__(self, userName, Email, PasswordHash, Salt, Name):
		self.__userName = userName
		self.__Email = Email
		self.__PasswordHash = PasswordHash
		self.__Salt = Salt
		self.__Name = Name
		self.__IsAdmin = False

	def hash(self, Password, Salt):
		return Password + Salt

	def editEmail(self, newEmail):
		self.__Email = newEmail

	def editPasswordHash(self, newPassword):
		newPasswordHash = BoatManager.hash(newPassword, self.__Salt)
		self.__PasswordHash = newPasswordHash

	def editName(self, newName):
		self.__Name = newName

	def changeIsAdmin(self):
		self.__IsAdmin = not self.__IsAdmin

	def getUsername(self):
		return self.__userName

	def getEmail(self):
		return self.__Email

	def getPasswordHash(self):
		return self.__PasswordHash

	def getSalt(self):
		return self.__Salt

	def getName(self):
		return self.__Name

	def getIsAdmin(self):
		return self.__IsAdmin



class Admin(User):
	def __init__(self, *args):
		super().__init__(*args)
		self.__IsAdmin = True


Main()