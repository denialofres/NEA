salt = input("salt: ")
password = input("password: ")

def hash(Password, Salt):
	hash = 14
	for i in list(Password)+list(Salt):
		hash = (hash * 65599) + 2^33
	return str(hash)

print(hash(password, salt))