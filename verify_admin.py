from app import db, User
admin = User.query.filter_by(email="admin@fithub.com").first()
print(f"Admin exists: {admin is not None}")
if admin:
    print(f"Username: {admin.username}")
    print(f"Email: {admin.email}")
    print(f"Is admin: {admin.is_admin}")
