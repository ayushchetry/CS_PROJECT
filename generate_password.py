import bcrypt

# Generate hashed password for 'admin123'
password = "admin123"
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print("=" * 50)
print("HASHED PASSWORD GENERATED:")
print("=" * 50)
print(hashed_password)
print("\nNow run this SQL command in MySQL:")
print("=" * 50)
print(f"INSERT INTO users (username, password, email) VALUES ('admin', '{hashed_password}', 'admin@lab.com');")
print("=" * 50)