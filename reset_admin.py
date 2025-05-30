from app import db, User
admin = User.query.filter_by(email="admin@fithub.com").first()
if admin:
    admin.set_password("admin123")
    db.session.commit()
    print("Admin password reset successfully!")
