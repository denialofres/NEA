import sqlite3
from sqlite3 import Error
import time, datetime
import json
import string as stringModule
import re
import time
from datetime import datetime
import random

def Main():
	# import settings
	# run boatManager with correct settings
	
	program = BoatManager("options.json")
	program.newBoat("0001", "Boater", "Firefly", "SuperSpeedy", "commentrsdugkn/?ad v q3284AFSd")
	#program.newUser("ILoveBoats", "Boatlover5000@gmail.com", "$2y$10$.vGA1O9wmRjrwAVXD9","?A.Cs3", ("John", "Smith"))


class BoatManager():
	def __init__(self, optionsFile):
		with open(optionsFile, "r") as optionsFileObject:
			self.__options = json.load(optionsFileObject)
		
		self.__dbfile = self.__options["dbfile"]
		try:
			with open(self.__dbfile) as DB:
				pass
		except FileNotFoundError:
			self.setupDatabase(self.__dbfile)
		self.loadDatabase(self.__dbfile)

		self.__logging = self.__options["logging"]
		if self.__logging:
			self.__logfile = self.__options["logfile"]
		self.__UniversalBoatEditing = self.__options["UniversalBoatEditing"]
		self.__UniversalIssueEditing = self.__options["UniversalIssueEditing"]
		self.__UniversalBookingEditing = self.__options["UniversalBookingEditing"]
		self.__MaxBookingLength = self.__options["MaxBookingLength"]
		self.__sysAdminUsername = self.__options["sysAdminUsername"]
		self.__SysAdefaults = self.__options["sysAdminDefaultDetails"]
		SysAdefaultPwordHash = self.__options["sysAdminDefaultPasswordHash"]

		if self.findUserIndex(self.__sysAdminUsername) != -1:
			self.giveAdminPerms(self.__sysAdminUsername)
		elif self.findAdminIndex(self.__sysAdminUsername) == -1:
			self.newUser(self.__sysAdminUsername, self.__SysAdefaults[0], self.__SysAdefaults[1], SysAdefaultPwordHash, self.__SysAdefaults[2])
			self.giveAdminPerms(self.__sysAdminUsername)

		print("BoatManager Initialized")


	def getDetails(self, toPrint):
		details = {}
		details["users"] = self.__Users
		details["admins"] = self.__Admins
		details["boats"] = self.__Boats
		details["bookings"] = self.__Bookings
		details["options"] = self.__options

		if toPrint:
			for item in details:
				print(item, end=" - ")
				print(details[item])
		else:
			return details

	def getOptions(self):
		return self.__options

	def log(self, message):
		with open(self.__logfile, "a") as log:
			time = datetime.now().replace(microsecond=0).isoformat(" ")
			log.write(f"{time} 	{message}\n")

	def hash(self, Password, Salt):
		hash = 14
		for i in list(Password)+list(Salt):
			hash = (hash * 65599) + ord(i)
		return str(hash)


	def setupDatabase(self, dbfile):
		print(f"Database not found, creating {dbfile}")
		conn = sqlite3.connect(dbfile)
		cursor = conn.cursor()
		# Make Users table
		cursor.execute("""CREATE TABLE Users (
			Username varChar(30) NOT NULL,
			Name varChar(30) NOT NULL,
			Email varChar(255) NOT NULL,
			PasswordHash varChar(255) NOT NULL,
			Salt varChar(6) NOT NULL,
			IsAdmin Bool NOT NULL,   
			Primary key (Username)
						);""")

		# Make Boats table
		cursor.execute("""CREATE TABLE Boats (
			BoatID varChar(4) NOT NULL,
			BoatName varChar(30) NOT NULL,
			BoatType varChar(30) NOT NULL,
			Owner varChar(30),
			Comments varChar(511),
			Primary key (BoatID),
			Foreign key (Owner) references Users(Username)
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
			Foreign key (Creator) references Users(Username),
			Foreign key (BoatID) references Boats(BoatID)
			);""")

		# Make Bookings table
		cursor.execute("""CREATE TABLE Bookings (
			BookingID varChar(5) NOT NULL,
			Username varChar(30) NOT NULL,
			BoatID varChar(4) NOT NULL,
			startTime Integer NOT NULL,
			Length int NOT NULL,
			CreationDate Integer NOT NULL,
			Primary key (BookingID),
			Foreign key (Username) references Users(Username),
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
		self.__Bookings = []

		UserData = cursor.execute("SELECT Username, Name, Email, PasswordHash, Salt, IsAdmin FROM Users")
		for user in UserData:
			if user[5] == 0:
				self.__Users.append(User(user[0], user[1], user[2], user[3], user[4]))
			else:
				self.__Admins.append(Admin(user[0], user[1], user[2], user[3], user[4]))

		BoatData = cursor.execute("SELECT BoatID, BoatName, BoatType, Owner, Comments FROM Boats")
		for boat in BoatData:
			self.__Boats.append(Boat(boat[0], boat[1], boat[2], boat[3], boat[4]))

		IssueData = cursor.execute("SELECT IssueID, Creator, BoatID, CreationDate, Details, FixDate, Severity, Resolved FROM Issues")
		for issue in IssueData:
			self.__Issues.append(Issue(issue[0], issue[1], issue[2], issue[3], issue[4], issue[5], issue[6], issue[7]))

		BookingData = cursor.execute("SELECT BookingID, Username, BoatID, startTime, Length, CreationDate FROM Bookings")
		for booking in BookingData:
			self.__Bookings.append(Booking(booking[0], booking[1], booking[2], booking[3], booking[4], booking[5]))

		conn.close()


	def findUserIndex(self, Username):
		index = 0
		for user in self.__Users:
			if user.getUsername() == Username:
				return index
			index += 1
		return -1

	def findAdminIndex(self, Username):
		index = 0
		for admin in self.__Admins:
			if admin.getUsername() == Username:
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

	def findBookingIndex(self, BookingID):
		index = 0
		for booking in self.__Bookings:
			if booking.getBookingID() == BookingID:
				return index
			index += 1
		return -1


	def getUser(self, Username):
		Index = self.findUserIndex(Username)
		if Index != -1:
			return self.__Users[Index]

		Index = self.findAdminIndex(Username)
		if Index != -1:
			return self.__Admins[Index]

		return -1	

	def getBoat(self, BoatID):
		Index = self.findBoatIndex(BoatID)
		if Index == -1:
			return -1

		return self.__Boats[Index]

	def getIssue(self, IssueID):
		Index = self.findIssueIndex(IssueID)
		if Index == -1:
			return -1

		return self.__Issues[Index]

	def getBooking(self, BookingID):
		Index = self.findBookingIndex(BookingID)
		if Index == -1:
			return -1

		return self.__Bookings[Index]


	def getAdmins(self):
		return self.__Admins

	def getUsers(self):
		return self.__Users

	def getBoats(self):
		return self.__Boats

	def getIssues(self):
		return self.__Issues

	def getBookings(self):
		return self.__Bookings


	def validatePasswordInput(self, password, passwordConfirm):
		if password != passwordConfirm:
			return "Passwords don't match"
		if len(password) < 6:
			return "Password is too short"
		if len(password) > 30:
			return "Password is too long"
		return True

	def validateUser(self, Username, Name, Email, PasswordHash, Salt):
		if len(Username)<3 or len(Username)>30:
			self.log(f"Failed to add User - wrong length of Username")
			return "Invalid input, Username must be between 1 and 30 chars"

		disallowedChars = [punc for punc in stringModule.punctuation if punc not in ("'", "-", "_")]
		disallowedChars.append(" ")

		if any(p in Username for p in disallowedChars):
			self.log(f"Failed to add User - banned character in Username")
			return "Invalid input, banned character used in Username"

		if not re.match(r"[^@]+@[^@]+\.[^@]+", Email):
			self.log(f"Failed to add User - invalid email")
			return "Invalid input, Email is not valid"



		
		Name = list(Name)
		disallowedChars = [punc for punc in stringModule.punctuation if punc not in ("'", "-")]

		if any(p in Name for p in disallowedChars):
				self.log(f"Failed to add User - banned character in name")
				return "Invalid input, banned character used in name"

		if len(Name) == 0:
			self.log(f"Failed to add User - name not entered")
			return "Invalid input, name is a required field"


		if len(Name)>30:
			self.log(f"Failed to add User - name is too long")
			return "Invalid input, name is too long"

		return 1

	def validateBoat(self, BoatID, BoatName, BoatType, Owner, Comments):
		if len(BoatName)<1 or len(BoatName)>30:
			self.log(f"Failed to add Boat - wrong length of boat name")
			return "Invalid input, boat name must be between 1 and 30 chars"
		
		disallowedChars = [punc for punc in stringModule.punctuation if punc not in ("'", "-", "_")]
		
		if any(p in BoatName for p in disallowedChars):
			self.log(f"Failed to add Boat - banned character in boatname")
			return "Invalid input, banned character used in the boat name"

		if len(BoatType)<1 or len(BoatType)>30:
			self.log(f"Failed to add Boat - wrong length of boat type")
			return "Invalid input, boat types must be between 1 and 30 chars"

		disallowedChars = [punc for punc in stringModule.punctuation if punc not in ("'", "-", "_")]

		if any(p in BoatType for p in disallowedChars):
			self.log(f"Failed to add Boat - banned character in boat type")
			return "Invalid input, banned character used"

		if self.findUserIndex(Owner) == -1 and self.findAdminIndex(Owner) == -1:
			self.log(f"Failed to add Issue - Owner doesn't exist")
			return "Owner Username doesn't exist - internal issue"

		try:
			if len(Comments) > 511:
				self.log(f"Failed to add boat - comments are too long")
				return "Invalid input, comment too long"
		except TypeError:
			pass

		return 1

	def validateIssue(self, IssueID, Creator, BoatID, CreationDate, Details, FixDate, Severity, Resolved):
		if self.findUserIndex(Creator) == -1 and self.findAdminIndex(Creator) == -1:
			self.log(f"Failed to add Issue - Creator doesn't exist")
			return "Creator Username doesn't exist - internal error"

		if self.findBoatIndex(BoatID) == -1:
			self.log(f"Failed to add Issue - Boat does not exist")
			return "Boat doesn't exist - internal error"
	
		if Details != None:
			if len(Details) > 1000:
				self.log(f"Failed to add Issue - Details exceed char limit")
				return "Characters must be 1000 chars max"

		return 1

	def validateBooking(self, BookingID, Username, BoatID, startTime, Length, CreationDate):
		if self.findUserIndex(Username) == -1 and self.findAdminIndex(Username) == -1:
			self.log(f"Failed to add Booking - Username doesn't exist")
			return "Username doesn't exist - internal error"

		if self.findBoatIndex(BoatID) == -1:
			self.log(f"Failed to add Booking - Boat does not exist")
			return "Boat doesn't exist - internal error"

		if self.__MaxBookingLength != False:
			if int(Length)>self.__MaxBookingLength:
				self.log(f"Failed to add Booking - Booking exceeds max length")
				return f"Booking exceeds max length of {self.__MaxBookingLength} minutes"
		if int(Length) < 1:
			self.log("Failbed to add Booking - Booking Length is less than 1")
			return f"Booking length cannot be 0 or negative"

		Finish = int(startTime) + int(Length)*60

		for booking in self.__Bookings: # check the booking won't overlap with any others
			if booking.getBoatID() == BoatID:
				if int(booking.getStartTime())>Finish or (int(booking.getStartTime())+int(booking.getLength())*60)<int(startTime):
					pass # Times do not overlap
				else:
					if booking.getBookingID() != BookingID:
						self.log(f"Failed to add Booking - Booking overlaps with existing booking {booking.getBookingID()}")
						return f"Booking overlaps with other booking from {datetime.fromtimestamp(booking.getStartTime()).isoformat()} to {datetime.fromtimestamp(booking.getStartTime()+booking.getLength()*60).isoformat()}"

		return 1


	def newUser(self, Username, Name, Email, PasswordHash, Salt):
		if self.findUserIndex(Username) != -1 or self.findAdminIndex(Username) != -1:
			self.log(f"Failed to add User {Username} - already exists")
			return "Failed to add user, Username already in use"

		validation = self.validateUser(Username, Name, Email, PasswordHash, Salt)
		if validation != 1:
			return validation		

		# Add user to self.__Users
		self.__Users.append(User(Username, Name, Email, PasswordHash, Salt))

		# Replaces apostrophes with " for sql use
		Username = Username.replace("'", "''")
		Salt = Salt.replace("'", "''")
		Name = Name.replace("'", "''")

		# Add user to Database
		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""INSERT INTO Users (Username,  Name, Email, PasswordHash, Salt, isAdmin)
			VALUES ('{Username}',  '{Name}', '{Email}', '{PasswordHash}','{Salt}', False)
			""")
		conn.commit()
		conn.close() 

		self.log(f"added user {Username}")
		return 1

	def newBoat(self, BoatID, BoatName, BoatType, Owner, Comments):
		if self.findBoatIndex(BoatID) != -1:
			self.log(f"Failed to add Boat {BoatID} - already exists")
			return "BoatID in use - internal error"

		validation = self.validateBoat(BoatID, BoatName, BoatType, Owner, Comments)
		if validation != 1:
			return validation


		# Add boat to self.__Boats and database
		self.__Boats.append(Boat(BoatID, BoatName, BoatType, Owner, Comments))

		# Replaces apostrophes with " for sql use
		BoatName = BoatName.replace("'", "''")
		BoatType = BoatType.replace("'", "''")
		Owner = Owner.replace("'", "''")
		Comments = Comments.replace("'", "''")

		# Add to datatbase
		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			INSERT INTO Boats (BoatID, BoatName, BoatType, Owner, Comments)
			VALUES ('{BoatID}', '{BoatName}', '{BoatType}','{Owner}', '{Comments}')
			""")
		conn.commit()
		conn.close()

		self.log(f"added boat {BoatID}")
		return 1

	def newIssue(self, IssueID, Creator, BoatID, CreationDate=int(time.time()), Details="", FixDate=None, Severity=None, Resolved=0):
		if self.findIssueIndex(IssueID) != -1:
			self.log(f"Failed to add Issue - IssueID already in use")
			return "IssueID in use - internal error"

		validation = self.validateIssue(IssueID, Creator, BoatID, CreationDate, Details, FixDate, Severity, Resolved)
		if validation != 1:
			return validation
	

		# Add issue to self.__Issues and database
		self.__Issues.append(Issue(IssueID, Creator, BoatID, CreationDate, Details, FixDate, Severity, Resolved))

		# Replaces apostrophes with " for sql use
		Creator = Creator.replace("'", "''")
		if Details != None:
			Details = Details.replace("'", "''")

		# Add to database
		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			INSERT INTO Issues (IssueID, Creator, BoatID, CreationDate, Details, FixDate, Severity, Resolved)
			VALUES ('{IssueID}', '{Creator}', '{BoatID}','{CreationDate}', '{Details}', '{FixDate}', '{Severity}', '{Resolved}')
			""")
		conn.commit()
		conn.close()

		self.log(f"added issue {IssueID}")
		return 1

	def newBooking(self, BookingID, Username, BoatID, startTime, Length, CreationDate=int(time.time())):
		if self.findBookingIndex(BookingID) != -1:
			self.log(f"Failed to add Booking - BookingID already in use")
			return "BookingID in use - internal error"

		validation = self.validateBooking(BookingID, Username, BoatID, startTime, Length, CreationDate)
		if validation != 1:
			return validation


		# Add booking to self.__Bookings and database
		self.__Bookings.append(Booking(BookingID, Username, BoatID, startTime, Length, CreationDate))

		# Replaces apostrophes with " for sql use
		Username = Username.replace("'", "''")

		# Add to database
		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			INSERT INTO Bookings (BookingID, Username, BoatID, startTime, Length, CreationDate)
			VALUES ('{BookingID}', '{Username}', '{BoatID}','{startTime}', '{Length}', '{CreationDate}')
			""")
		conn.commit()
		conn.close()

		self.log(f"added booking {BookingID}")
		return 1

	
	def deleteUser(self, Username):
		for booking in self.__Bookings:
			if booking.getUsername() == Username:
				self.deleteBooking(booking.getBookingID())

		for issue in self.__Issues:
			if issue.getCreator() == Username:
				attr = issue.getAllAttributes()
				self.editIssue(attr[0], self.__sysAdminUsername, attr[2], attr[3], attr[4], attr[5], attr[6], attr[7])

		for boat in self.__Boats:
			if boat.getOwner() == Username:
				attr = boat.getAllAttributes()
				self.editBoat(attr[0], attr[1], attr[2], self.__sysAdminUsername, attr[4])

		for user in self.__Users:
			if user.getUsername() == Username:
				prevDetails = user.getAllAttributes()
				self.__Users.remove(user)

		for admin in self.__Admins:
			if admin.getUsername() == Username:
				prevDetails = admin.getAllAttributes()
				self.__Admins.remove(user)

		conn = sqlite3.connect(self.__dbfile)
		Username = Username.replace("'", "''")
		conn.execute(f"""
			DELETE FROM Users WHERE Username = '{Username}'
			""")
		conn.commit()
		conn.close()

		self.log(f"deleted user {Username}")
		return prevDetails

	def deleteBoat(self, BoatID):
		for issue in self.__Issues:
			if issue.getBoatID() == BoatID:
				self.deleteIssue(issue.getIssueID())

		for booking in self.__Bookings:
			if booking.getBoatID() == BoatID:
				self.deleteBooking(booking.getBookingID())

		for boat in self.__Boats:
			if boat.getID() == BoatID:
				prevDetails = boat.getAllAttributes()
				self.__Boats.remove(boat)

				conn = sqlite3.connect(self.__dbfile)
				conn.execute(f"""
					DELETE FROM Boats WHERE BoatID = '{BoatID}'
					""")
				conn.commit()
				conn.close()

				self.log(f"deleted boat {BoatID}")
				return prevDetails
		return -1

	def deleteIssue(self, IssueID):
		for issue in self.__Issues:
			if issue.getIssueID() == IssueID:
				prevDetails = issue.getAllAttributes()
				self.__Issues.remove(issue)

		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			DELETE FROM Issues WHERE IssueID = '{IssueID}'
			""")
		conn.commit()
		conn.close()

		self.log(f"deleted issue {IssueID}")
		return prevDetails

	def deleteBooking(self, BookingID):
		for booking in self.__Bookings:
			if booking.getBookingID() == BookingID:
				prevDetails = booking.getAllAttributes()
				self.__Bookings.remove(booking)

		conn = sqlite3.connect(self.__dbfile)
		conn.execute(f"""
			DELETE FROM Bookings WHERE BookingID = '{BookingID}'
			""")
		conn.commit()
		conn.close()

		self.log(f"deleted booking {BookingID}")
		return prevDetails


	def editUser(self, Username, Name, Email, PasswordHash, Salt):
		validation = self.validateUser(Username, Name, Email, PasswordHash, Salt)
		if validation != 1:
			return validation
		self.deleteUser(Username)
		self.newUser(Username, Name, Email, PasswordHash, Salt)
		return 1

	def editBoat(self, BoatID, BoatName, BoatType, Owner, Comments):	
		validation = self.validateBoat(BoatID, BoatName, BoatType, Owner, Comments)
		if validation != 1:
			return validation
		self.deleteBoat(BoatID)
		self.newBoat(BoatID, BoatName, BoatType, Owner, Comments)
		return 1

	def editIssue(self, IssueID, Creator, BoatID, CreationDate, Details, FixDate, Severity, Resolved):
		validation = self.validateIssue(IssueID, Creator, BoatID, CreationDate, Details, FixDate, Severity, Resolved)
		if validation != 1:
			return validation
		self.deleteIssue(IssueID)
		self.newIssue(IssueID, Creator, BoatID, CreationDate, Details, FixDate, Severity, Resolved)
		return 1

	def editBooking(self, BookingID, Username, BoatID, startTime, Length, CreationDate):
		validation = self.validateBooking(BookingID, Username, BoatID, startTime, Length, CreationDate)
		if validation != 1:
			return validation
		self.deleteBooking(BookingID)
		self.newBooking(BookingID, Username, BoatID, startTime, Length, CreationDate)
		return 1


	def generateSalt(self):
		chars = stringModule.ascii_uppercase + stringModule.ascii_lowercase + stringModule.digits
		salt = ''.join(random.SystemRandom().choice(stringModule.ascii_uppercase + stringModule.digits) for _ in range(6))
		return salt

	def getNewBoatID(self):
		count = 1
		strcount = ("0000"+str(count))[-4:]
		while True:
			if self.findBoatIndex(strcount) == -1:
				return strcount
			count += 1
			strcount = ("0000"+str(count))[-4:]

	def getNewIssueID(self):
		count = 1
		strcount = ("000000"+str(count))[-6:]
		while True:
			if self.findIssueIndex(strcount) == -1:
				return strcount
			count += 1
			strcount = ("000000"+str(count))[-6:]

	def getNewBookingID(self):
		count = 1
		strcount = ("00000"+str(count))[-5:]
		while True:
			print("l616", strcount)
			print("l617", self.__Bookings)
			if self.findBookingIndex(strcount) == -1:
				print("l618", self.findBookingIndex(strcount))
				return strcount
			count += 1
			strcount = ("00000"+str(count))[-5:]


	def sortBoats(self):
		self.__Boats = self.mergeSortBoats(self.__Boats)

	def mergeSortBoats(self, data):
		if len(data) == 1 or len(data) == 0:
			return data

		midindex = int(len(data)//2)
		upper = data[midindex:]
		upper = self.mergeSortBoats(upper)

		lower = data[:midindex]
		lower = self.mergeSortBoats(lower)

		i, j, k = 0, 0, 0
		while i<len(lower) and j<len(upper):
			if int(lower[i].getID())<=int(upper[j].getID()):
				data[k] = lower[i]
				i += 1
			else:
				data[k] = upper[j]
				j += 1
			k += 1

		while i<len(lower):
			data[k] = lower[i]
			i += 1
			k += 1

		while j<len(upper):
			data[k] = upper[j]
			j += 1
			k += 1
		return data

	def sortIssues(self):
		resolved = []
		unresolved = []
		issueList = []
		for issue in self.__Issues:
			if issue.getResolved() == 1:
				resolved.append(issue)
			else:
				unresolved.append(issue)

		unresolved.sort(reverse=True, key=(lambda issue: int(issue.getSeverity())))
		resolved.sort(reverse=True, key=(lambda issue: int(issue.getCreationDate())))

		for bigSort in [unresolved, resolved]:
			for item in bigSort:
				issueList.append(item)
		
		self.__Issues = issueList

	def sortBookings(self):
		self.__Bookings.sort(reverse=False, key=(lambda booking: int(booking.getStartTime())))


	def giveAdminPerms(self, Username):
		index = self.findUserIndex(Username)
		user = self.getUser(Username)
		[Username, Name, Email, PasswordHash, Salt] = user.getAllAttributes()
		admin = Admin(Username, Name, Email, PasswordHash, Salt)
		self.__Admins.append(admin)
		self.__Users.pop(index)

		conn = sqlite3.connect(self.__dbfile)
		Username = Username.replace("'", "''")
		conn.execute(f"""
			UPDATE Users
			SET IsAdmin = True
			WHERE Username = '{Username}';
			""")
		conn.commit()
		conn.close()

	def removeAdminPerms(self, Username):
		index = self.findAdminIndex(Username)
		admin = self.getUser(Username)
		[Username, Name, Email, PasswordHash, Salt] = admin.getAllAttributes()
		user = User(Username, Name, Email, PasswordHash, Salt)
		self.__Users.append(user)
		self.__Admins.pop(index)

		conn = sqlite3.connect(self.__dbfile)
		Username = Username.replace("'", "''")
		conn.execute(f"""
			UPDATE Users
			SET IsAdmin = False
			WHERE Username = '{Username}';
			""")
		conn.commit()
		conn.close()


class User():
	def __init__(self, Username, Name, Email, PasswordHash, Salt):
		self.__Username = Username
		self.__Email = Email
		self.__PasswordHash = PasswordHash
		self.__Salt = Salt
		self.__Name = Name


	def getUsername(self):
		return self.__Username

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

	def getAllAttributes(self): # [Username, Name, Email, PasswordHash, Salt]
		return [self.__Username, self.__Name, self.__Email, self.__PasswordHash, self.__Salt]


class Admin(User):
	def __init__(self, Username, Email, PasswordHash, Salt, Name):
		User.__init__(self, Username, Email, PasswordHash, Salt, Name)


	def getIsAdmin(self):
		return True


class Boat():
	def __init__(self, BoatID, BoatName, BoatType, Owner, Comments):
		self.__BoatID = BoatID
		self.__BoatName = BoatName
		self.__BoatType = BoatType
		self.__Owner = Owner
		self.__Comments = Comments


	def getIsAdmin(self):
		return False

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

	def getAllAttributes(self):
		return [self.__BoatID, self.__BoatName, self.__BoatType, self.__Owner, self.__Comments]


class Issue():
	def __init__(self, IssueID, Creator, BoatID, CreationDate, Details, FixDate, Severity, Resolved):
		self.__IssueID = IssueID
		self.__Creator = Creator
		self.__BoatID = BoatID
		self.__CreationDate = CreationDate
		self.__Severity = Severity
		self.__Details = Details
		self.__FixDate = FixDate
		self.__Resolved = Resolved


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

	def getAllAttributes(self):
		return [self.__IssueID, self.__Creator, self.__BoatID, self.__CreationDate, self.__Details, self.__FixDate, self.__Severity, self.__Resolved]


class Booking():
	def __init__(self, BookingID, Username, BoatID, startTime, Length, CreationDate):
		self.__BookingID = BookingID
		self.__Username = Username
		self.__BoatID = BoatID
		self.__startTime = startTime
		self.__Length = Length
		self.__CreationDate = CreationDate


	def getBookingID(self):
		return self.__BookingID

	def getUsername(self):
		return self.__Username

	def getBoatID(self):
		return self.__BoatID

	def getStartTime(self):
		return self.__startTime

	def getLength(self):
		return self.__Length

	def getCreationDate(self):
		return self.__CreationDate

	def getAllAttributes(self):
		return [self.__BookingID, self.__Username, self.__BoatID, self.__startTime, self.__Length, self.__CreationDate]


if __name__ == "__main__":
	Main()