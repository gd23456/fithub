from app import db, User, MembershipPlan
from datetime import datetime

def init_db():
    # Create all tables
    db.create_all()

    # Check if admin user exists
    admin = User.query.filter_by(email='admin@fithub.com').first()
    if not admin:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@fithub.com',
            is_admin=True
        )
        admin.set_password('admin123')  # Set default admin password
        db.session.add(admin)

    # Check if default membership plans exist
    if not MembershipPlan.query.first():
        # Create default membership plans
        plans = [
            MembershipPlan(plan_name='Basic Monthly', duration_months=1, price=1499.00),
            MembershipPlan(plan_name='Standard Quarterly', duration_months=3, price=3999.00),
            MembershipPlan(plan_name='Premium Annual', duration_months=12, price=14999.00)
        ]
        db.session.bulk_save_objects(plans)

    try:
        db.session.commit()
        print("Database initialized successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing database: {str(e)}")

if __name__ == '__main__':
    init_db()