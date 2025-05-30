from werkzeug.security import generate_password_hash

password = 'admin123'  # This is the default admin password
hash = generate_password_hash(password)
print(f"Generated hash: {hash}")
