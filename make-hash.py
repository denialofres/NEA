salt = input("salt: ")
password = input("password: ")

def hash(Password, Salt):
	hash = 14
	for i in list(Salt)+list(Password):
		hash = (hash * 65599) + ord(i)
	return hash

print(hash(password, salt))