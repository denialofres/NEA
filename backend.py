import sqlite3
from sqlite3 import Error
import time, datetime
import json

def Main():
	# import settings
	# run boatManager with correct settings
	
	program = BoatManager("options.json")
	#program.newUser("ILoveBoats", "Boatlover5000@gmail.com", "$2y$10$.vGA1O9wmRjrwAVXD9","?A.Cs3", ("John", "Smith"))


class BoatManager():
	def __init__(self, optionsFile):
		with open(optionsFile, "r") as optionsFileObject:
			options = json.load(optionsFileObject)
		
		self.__dbfile = options["dbfile"]
		try:
			with open(self.__dbfile) as DB:
				pass
		except FileNotFoundError:
			self.setupDatabase(self.__dbfile)
		self.loadDatabase(self.__dbfile)

		self.__logging = options["logging"]
		if self.__logging:
			self.__logfile = options["logfile"]

		print("BoatManager Initialized")


	def getDetails(self, toPrint):
		details = {}
		details["dbfile"] = self.__dbfile
		details["users"] = self.__Users
		details["admins"] = self.__Admins
		details["boats"] = self.__Boats

		if toPrint:
			for item in details:
				print(item, end=" - ")
				print(details[item])
		else:
			return details

	def log(self, message):
		with open(self.__logfile, "a") as log:
			time = datetime.datetime.now().replace(microsecond=0).isoformat(" ")
			log.write(f"{time} 	{message}\n")

	def hash(self, Password, Salt):
		hash = 14
		for i in list(Password)+list(Salt):
			hash = (hash * 65599) + ord(i)
		return hash


	def setupDatabase(self, dbfile):
		print(f"Database not found, creating {dbfile}")
		conn = sqlite3.connect(dbfile)
		cursor = conn.cursor()
		# Make Users table
		cursor.execute("""CREATE TABLE Users (
			UserName varChar(30) NOT NULL,
			Email varChar(255) NOT NULL,
			PasswordHash varChar(64) NOT NULL,
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
			Details varChar(1000),
			FixDate Integer,
			Severity Integer NOT NULL,
			Resolved Boolean NOT NULL,
			Primary key (IssueID),
			Foreign key (Creator) references Users(UserName),
			Foreign key (BoatID) references Boats(BoatID)
			);""")

		conn.commit()
		conn.close()

	def loadDatabase(self, dbfile):
		conn = sqlite3.connect(dbfile)
		cursor = conn.cursor()

		self.__Users = []
		self.__Admins = []
		self.__Boats = []
		self.__Issues = []

		UserData = cursor.execute("SELECT UserName, Email, PasswordHash, Salt, Firstname, Lastname, IsAdmin FROM Users")
		for user in UserData:
			if user[6] == 0:
				self.__Users.append(User(user[0], user[1], user[2], user[3], (user[4], user[5])))
			else:
				self.__Admins.append(Admin(user[0], user[1], user[2], user[3], (user[4], user[5])))

		BoatData = cursor.execute("SELECT BoatID, BoatName, BoatType, Owner, Comments FROM Boats")
		for boat in BoatData:
			self.__Boats.append(Boat(boat[0], boat[1], boat[2], boat[3], boat[4]))

		IssueData = cursor.execute("SELECT IssueID, Creator, BoatID, CreationDate, Severity, Details, FixDate, Resolved FROM Issues")
		for issue in IssueData:
			self.__Issues.append(Issue(issue[0], issue[1], issue[2], issue[3], issue[4], issue[5], issue[6], issue[7]))

		conn.close()


	def findUserIndex(self, username):
		index = 0
		for user in self.__Users:
			if user.getUsername() == username:
				return index
			index += 1
		return -1

	def findAdminIndex(self, username):
		index = 0
		for admin in self.__Admins:
			if admin.getUsername() == username:
				return index
			index += 1
		return -1

	def findBoatIndex(self, ID):
		index = 0
		for boat in self.__Boats:
			if boat.getID() == ID:
				return index
			index += 1
		return -1

	def findIssueIndex(self, IssueID):
		index = 0
		for issue in self.__Issues:
			if issue.getIssueID() == IssueID:
				return index
			index += 1
		return -1


	def newUser(self, username, Email, PasswordHash, Salt, Name):
		if self.findUserIndex(username) != -1 or self.findAdminIndex(username) != -1:
			self.log(f"Failed to add User {username} - already exists")
			return -1

		self.__Users.append(User(username, Email, PasswordHash, Salt, Name))

		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			INSERT INTO Users (UserName, Email, PasswordHash, Salt, Firstname, Lastname, isAdmin)
			VALUES ('{username}', '{Email}', '{PasswordHash}','{Salt}', '{Name[0]}', '{Name[1]}', False)
			""")
		conn.commit()
		conn.close()

		self.log(f"added user {username}")

	def newAdmin(self, username, Email, PasswordHash, Salt, Name):
		if self.findUserIndex(username) != -1 or self.findAdminIndex(username) != -1:
			self.log(f"Failed to add Admin {username} - already exists")
			return -1

		self.__Admins.append(User(username, Email, PasswordHash, Salt, Name))

		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			INSERT INTO Users (UserName, Email, PasswordHash, Salt, Firstname, Lastname, isAdmin)
			VALUES ('{username}', '{Email}', '{PasswordHash}','{Salt}', '{Name[0]}', '{Name[1]}', 1)
			""")
		conn.commit()
		conn.close()

		self.log(f"added admin {username}")

	def newBoat(self, BoatID, BoatName, BoatType, Owner, Comments):
		if self.findBoatIndex(BoatID) != -1:
			self.log(f"Failed to add Boat {username} - already exists")
			return -1

		self.__Boats.append(Boat(BoatID, BoatName, BoatType, Owner, Comments))

		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			INSERT INTO Boats (BoatID, BoatName, BoatType, Owner, Comments)
			VALUES ('{BoatID}', '{BoatName}', '{BoatType}','{Owner}', '{Comments}')
			""")
		conn.commit()
		conn.close()

		self.log(f"added boat {BoatID}")

	def newIssue(self, IssueID, Creator, BoatID, CreationDate, Severity=None, Details="", FixDate=-1, Resolved=False):
		if self.findBoatIndex(BoatID) != -1:
			self.log(f"Failed to add Boat {username} - already exists")
			return -1

		self.__Boats.append(Boat(BoatID, BoatName, BoatType, Owner, Comments))

		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			INSERT INTO Issues (IssueID, Creator, BoatID, CreationDate, Severity, Details, FixDate, Resolved)
			VALUES ('{IssueID}', '{Creator}', '{BoatID}','{CreationDate}', '{Severity}', '{Details}', '{FixDate}', '{Resolved}')
			""")
		conn.commit()
		conn.close()

		self.log(f"added issue {IssueID}")


	def giveAdminPerms(self, username):
		index = self.findUserIndex(username)
		self.__Users[index].changeIsAdmin()
		self.__Admins.append(self.__Users[index])
		self.__Users.pop(index)

		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			UPDATE Users
			SET IsAdmin = True
			WHERE UserName = '{username}';
			""")
		conn.commit()
		conn.close()

	def removeAdminPerms(self, username):
		index = self.findAdminIndex(username)
		self.__Admins[index].changeIsAdmin()
		self.__Users.append(self.__Admins[index])
		self.__Admins.pop(index)

		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			UPDATE Users
			SET IsAdmin = False
			WHERE UserName = '{username}';
			""")
		conn.commit()
		conn.close()



class User():
	def __init__(self, username, Email, PasswordHash, Salt, Name):
		self.__username = username
		self.__Email = Email
		self.__PasswordHash = PasswordHash
		self.__Salt = Salt
		self.__Name = Name




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
		return self.__username

	def getEmail(self):
		return self.__Email

	def getPasswordHash(self):
		return self.__PasswordHash

	def getSalt(self):
		return self.__Salt

	def getName(self):
		return self.__Name

	def getIsAdmin(self):
		return False


class Admin(User):
	def __init__(self, username, Email, PasswordHash, Salt, Name):
		User.__init__(self, username, Email, PasswordHash, Salt, Name)


	def getIsAdmin(self):
		return True


class Boat():
	def __init__(self, BoatID, BoatName, BoatType, Owner, Comments):
		self.__BoatID = BoatID
		self.__BoatName = BoatName
		self.__BoatType = BoatType
		self.__Owner = Owner
		self.__Comments = Comments


	def editName(self, newName):
		self.__BoatName = newName

	def editType(self, newType):
		self.__BoatType = newType

	def editOwner(self, newOwner):
		self.__Owner = newOwner

	def editComments(self, newComments):
		self.__Comments = newComments

	def getID(self):
		return self.__BoatID

	def getName(self):
		return self.__BoatName

	def getType(self):
		return self.__BoatType

	def getOwner(self):
		return self.__Owner

	def getComments(self):
		return self.__Comments


class Issue():
	def __init__(self, IssueID, Creator, BoatID, CreationDate, Severity, Details, FixDate, Resolved):
		self.__IssueID = IssueID
		self.__Creator = Creator
		self.__BoatID = BoatID
		self.__CreationDate = CreationDate
		self.__Severity = Severity
		self.__Details = getDetails
		self.__FixDate = FixDate
		self.__Resolved = Resolved


	def editSeverity(self, newSeverity):
		self.__Severity = newSeverity

	def editDetails(self, newDetails):
		self.__Details = newDetails

	def editFixDate(self, newFixDate):
		self.__FixDate = newFixDate

	def editResolved(self, newResolved):
		self.__Resolved = newResolved

	def getIssueID(self):
		return self.__IssueID

	def getCreator(self):
		return self.__Creator

	def getBoatID(self):
		return self.__BoatID

	def getCreationDate(self):
		return self.__CreationDate

	def getSeverity(self):
		return self.__Severity

	def getDetails(self):
		return self.__Details

	def getFixDate(self):
		return self.__FixDate

	def getResolved(self):
		return self.__Resolved


class Booking():
	def __init__(self, BookingID, UserName, BoatID, Datetime, Length, CreationDate):
		self.__BookingID = BookingID
		self.__UserName = UserName
		self.__BoatID = BoatID
		self.__Datetime = Datetime
		self.__Length = Length
		self.__CreationDate = CreationDate


if __name__ == "__main__":
	Main()