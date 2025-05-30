from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import csv
import io
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1321334050@localhost/gym_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 10  # Add connection pooling
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30  # Connection timeout in seconds
app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800  # Recycle connections after 30 minutes

db = SQLAlchemy(app)

@app.before_request
def before_request():
    if not db.engine.pool._pool:
        # Reconnect if pool is empty
        db.engine.dispose()
        db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Set up logging
if not app.debug:
    # Ensure logs directory exists
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, 'fithub.log')
    file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('FitHub startup')

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Member(db.Model):
    __tablename__ = 'members'
    member_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    gender = db.Column(db.String(10))
    join_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    user = db.relationship('User', backref=db.backref('member', uselist=False))

class MembershipPlan(db.Model):
    __tablename__ = 'membership_plans'
    plan_id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(50), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

class Trainer(db.Model):
    __tablename__ = 'trainers'
    trainer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100), unique=True)
    sessions = db.relationship('Session', backref='trainer', lazy=True)

class Session(db.Model):
    __tablename__ = 'sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(100))
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.trainer_id', ondelete='SET NULL'))
    session_date = db.Column(db.Date)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

class MemberPlan(db.Model):
    __tablename__ = 'member_plans'
    member_plan_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id', ondelete='CASCADE'))
    plan_id = db.Column(db.Integer, db.ForeignKey('membership_plans.plan_id', ondelete='CASCADE'))
    start_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    end_date = db.Column(db.Date)
    member = db.relationship('Member', backref='plans')
    plan = db.relationship('MembershipPlan', backref='member_plans')

class Attendance(db.Model):
    __tablename__ = 'attendance'
    attendance_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id', ondelete='CASCADE'))
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id', ondelete='CASCADE'))
    attended = db.Column(db.Boolean, default=True)
    date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    member = db.relationship('Member', backref='attendance')
    session = db.relationship('Session', backref='attendance')

class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id', ondelete='CASCADE'))
    amount = db.Column(db.Numeric(10, 2))
    payment_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    payment_method = db.Column(db.Enum('Cash', 'Card', 'UPI', 'Online'))
    member = db.relationship('Member', backref='payments')

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Routes
@app.route('/')
def index():
    upcoming_classes = Session.query\
        .join(Trainer)\
        .filter(Session.session_date >= datetime.now().date())\
        .order_by(Session.session_date, Session.start_time)\
        .limit(5)\
        .all()
    
    membership_plans = MembershipPlan.query.all()
    
    return render_template('index.html', 
                         upcoming_classes=upcoming_classes,
                         membership_plans=membership_plans)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        app.logger.info(f'Login attempt for email: {email}')
        
        user = User.query.filter_by(email=email).first()
        if not user:
            app.logger.warning(f'Login failed - no user found for email: {email}')
            flash('Invalid email or password', 'danger')
            return render_template('auth/login.html')
            
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember', False))
            app.logger.info(f'Successful login for user: {email} (Admin: {user.is_admin})')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        app.logger.warning(f'Login failed - invalid password for email: {email}')
        flash('Invalid email or password', 'danger')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    plans = MembershipPlan.query.all()
    
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already registered', 'danger')
            return render_template('auth/register.html', plans=plans)
        
        if request.form['password'] != request.form['confirm_password']:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html', plans=plans)
        
        # Validate password requirements
        password = request.form['password']
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return render_template('auth/register.html', plans=plans)
        if not any(c.isupper() for c in password):
            flash('Password must contain at least one uppercase letter', 'danger')
            return render_template('auth/register.html', plans=plans)
        if not any(c.islower() for c in password):
            flash('Password must contain at least one lowercase letter', 'danger')
            return render_template('auth/register.html', plans=plans)
        if not any(c.isdigit() for c in password):
            flash('Password must contain at least one number', 'danger')
            return render_template('auth/register.html', plans=plans)
        if not any(c in '@$!%*?&' for c in password):
            flash('Password must contain at least one special character (@$!%*?&)', 'danger')
            return render_template('auth/register.html', plans=plans)
        
        user = User(
            username=request.form['username'],
            email=request.form['email']
        )
        user.set_password(request.form['password'])
        
        member = Member(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone'],
            gender=request.form['gender'],
            user=user
        )
        
        try:
            db.session.add(user)
            db.session.add(member)
            db.session.commit()  # Commit first to get member_id
            
            # Now create the membership plan
            plan = MembershipPlan.query.get_or_404(request.form['plan_id'])
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30 * plan.duration_months)
            
            member_plan = MemberPlan(
                member_id=member.member_id,
                plan_id=request.form['plan_id'],
                start_date=start_date,
                end_date=end_date.date()
            )
            
            # Record the payment
            payment = Payment(
                member_id=member.member_id,
                amount=plan.price,
                payment_method=request.form['payment_method']
            )
            
            db.session.add(member_plan)
            db.session.add(payment)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
            app.logger.error(f'Registration error: {str(e)}')
    
    return render_template('auth/register.html', plans=plans)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/members')
@login_required
def members():
    members = Member.query.all()
    plans = MembershipPlan.query.all()
    return render_template('members.html', members=members, plans=plans)

@app.route('/add_member', methods=['POST'])
@login_required
def add_member():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    try:
        member = Member(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone'],
            gender=request.form['gender']
        )
        db.session.add(member)
        db.session.commit()
        flash('Member added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding member: {str(e)}', 'danger')
    return redirect(url_for('members'))

@app.route('/members/<int:id>/delete', methods=['GET'])
@login_required
def delete_member(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    try:
        member = Member.query.get_or_404(id)
        db.session.delete(member)
        db.session.commit()
        flash('Member deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting member: {str(e)}', 'danger')
    return redirect(url_for('members'))

@app.route('/members/<int:id>/edit', methods=['POST'])
@login_required
def edit_member(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    try:
        member = Member.query.get_or_404(id)
        member.name = request.form['name']
        member.email = request.form['email']
        member.phone = request.form['phone']
        member.gender = request.form['gender']
        db.session.commit()
        flash('Member updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating member: {str(e)}', 'danger')
    return redirect(url_for('members'))

@app.route('/members/<int:member_id>/assign_plan', methods=['POST'])
@login_required
def assign_plan(member_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Calculate end date based on plan duration
        plan = MembershipPlan.query.get_or_404(request.form['plan_id'])
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = start_date + timedelta(days=30 * plan.duration_months)
        
        member_plan = MemberPlan(
            member_id=member_id,
            plan_id=request.form['plan_id'],
            start_date=start_date,
            end_date=end_date.date()
        )
        
        # Record the payment
        payment = Payment(
            member_id=member_id,
            amount=plan.price,
            payment_method=request.form['payment_method']
        )
        
        # Add both records in a single transaction
        db.session.add(member_plan)
        db.session.add(payment)
        db.session.commit()
        
        flash('Plan updated and payment recorded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating plan: {str(e)}', 'danger')
    return redirect(url_for('members'))

@app.route('/membership_plans')
@login_required
def membership_plans():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    plans = MembershipPlan.query.all()
    return render_template('membership.html', plans=plans)

@app.route('/add_plan', methods=['POST'])
@login_required
def add_plan():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    try:
        plan = MembershipPlan(
            plan_name=request.form['plan_name'],
            duration_months=request.form['duration'],
            price=request.form['price']
        )
        db.session.add(plan)
        db.session.commit()
        flash('Membership plan added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding plan: {str(e)}', 'danger')
    return redirect(url_for('membership_plans'))

@app.route('/plans/<int:id>/delete', methods=['GET'])
@login_required
def delete_plan(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    try:
        plan = MembershipPlan.query.get_or_404(id)
        db.session.delete(plan)
        db.session.commit()
        flash('Plan deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting plan: {str(e)}', 'danger')
    return redirect(url_for('membership_plans'))

@app.route('/plans/<int:id>/edit', methods=['POST'])
@login_required
def edit_plan(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
        
    try:
        plan = MembershipPlan.query.get_or_404(id)
        plan.plan_name = request.form['plan_name']
        plan.duration_months = request.form['duration']
        plan.price = request.form['price']
        db.session.commit()
        flash('Plan updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating plan: {str(e)}', 'danger')
    return redirect(url_for('membership_plans'))

@app.route('/classes')
@login_required
def classes():
    classes = Session.query.join(Trainer).all()
    trainers = Trainer.query.all()
    return render_template('classes.html', classes=classes, trainers=trainers)

@app.route('/add_class', methods=['POST'])
def add_class():
    try:
        session = Session(
            session_name=request.form['session_name'],
            trainer_id=request.form['trainer_id'],
            session_date=datetime.strptime(request.form['session_date'], '%Y-%m-%d').date(),
            start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(request.form['end_time'], '%H:%M').time()
        )
        db.session.add(session)
        db.session.commit()
        flash('Class added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding class: {str(e)}', 'danger')
    return redirect(url_for('classes'))

@app.route('/classes/<int:id>/delete', methods=['GET'])
def delete_class(id):
    try:
        session = Session.query.get_or_404(id)
        db.session.delete(session)
        db.session.commit()
        flash('Class deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting class: {str(e)}', 'danger')
    return redirect(url_for('classes'))

@app.route('/classes/<int:id>')
def view_class(id):
    session = Session.query.get_or_404(id)
    attendees = Attendance.query.filter_by(session_id=id).join(Member).all()
    today = datetime.now().date()
    return render_template('class_details.html', 
                         session=session, 
                         attendees=attendees,
                         today=today)

@app.route('/classes/<int:id>/edit', methods=['POST'])
def edit_class(id):
    try:
        session = Session.query.get_or_404(id)
        session.session_name = request.form['session_name']
        session.trainer_id = request.form['trainer_id']
        session.session_date = datetime.strptime(request.form['session_date'], '%Y-%m-%d').date()
        session.start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        session.end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
        db.session.commit()
        flash('Class updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating class: {str(e)}', 'danger')
    return redirect(url_for('classes'))

@app.route('/classes/<int:id>/register', methods=['POST'])
@login_required
def register_for_class(id):
    try:
        session = Session.query.get_or_404(id)
        
        # Skip membership check for admin users
        if not current_user.is_admin:
            # Check if member has active membership for the class date
            if not has_active_membership(current_user.member.member_id, session.session_date):
                flash('Error: You need an active membership plan to register for classes', 'danger')
                return redirect(url_for('classes'))
        
        # Check if already registered
        existing_attendance = Attendance.query.filter_by(
            member_id=current_user.member.member_id if hasattr(current_user, 'member') else None,
            session_id=id
        ).first()
        
        if existing_attendance:
            flash('You are already registered for this class', 'warning')
        # Create attendance record (default attended=True will be set when class occurs)
        attendance = Attendance(
            member_id=current_user.member.member_id,
            session_id=id,
            date=session.session_date
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Successfully registered for the class!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error registering for class: {str(e)}', 'danger')
    return redirect(url_for('classes'))

@app.route('/trainers')
@login_required
def trainers():
    trainers = Trainer.query.all()
    return render_template('trainers.html', trainers=trainers)

@app.route('/add_trainer', methods=['POST'])
def add_trainer():
    try:
        trainer = Trainer(
            name=request.form['name'],
            specialization=request.form['specialization'],
            phone=request.form['phone'],
            email=request.form['email']
        )
        db.session.add(trainer)
        db.session.commit()
        flash('Trainer added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding trainer: {str(e)}', 'danger')
    return redirect(url_for('trainers'))

@app.route('/trainers/<int:id>/delete', methods=['GET'])
def delete_trainer(id):
    try:
        trainer = Trainer.query.get_or_404(id)
        db.session.delete(trainer)
        db.session.commit()
        flash('Trainer deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting trainer: {str(e)}', 'danger')
    return redirect(url_for('trainers'))

@app.route('/trainers/<int:id>/edit', methods=['POST'])
def edit_trainer(id):
    try:
        trainer = Trainer.query.get_or_404(id)
        trainer.name = request.form['name']
        trainer.specialization = request.form['specialization']
        trainer.phone = request.form['phone']
        trainer.email = request.form['email']
        db.session.commit()
        flash('Trainer updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating trainer: {str(e)}', 'danger')
    return redirect(url_for('trainers'))

@app.route('/attendance')
@login_required
def attendance():
    sessions = Session.query.all()
    members = Member.query.all()
    attendance_records = Attendance.query.join(Member).join(Session).all()
    return render_template('attendance.html', 
                         sessions=sessions, 
                         members=members, 
                         attendance=attendance_records)

def has_active_membership(member_id, date=None):
    if date is None:
        date = datetime.now().date()
    elif isinstance(date, datetime):
        date = date.date()
    
    active_plan = MemberPlan.query.filter(
        MemberPlan.member_id == member_id
    ).filter(
        func.date(MemberPlan.start_date) <= date
    ).filter(
        or_(
            MemberPlan.end_date >= date,
            MemberPlan.end_date.is_(None)
        )
    ).first()
    
    return active_plan is not None

@app.route('/record_attendance', methods=['POST'])
def record_attendance():
    try:
        member_id = request.form['member_id']
        session_id = request.form['session_id']
        session = Session.query.get_or_404(session_id)
        
        if not has_active_membership(member_id, session.session_date):
            flash('Error: Member does not have an active membership plan for this date', 'danger')
            return redirect(url_for('attendance'))
        
        attendance = Attendance(
            member_id=member_id,
            session_id=session_id,
            attended='attended' in request.form
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Attendance recorded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error recording attendance: {str(e)}', 'danger')
    return redirect(url_for('attendance'))

@app.route('/record_batch_attendance', methods=['POST'])
def record_batch_attendance():
    try:
        session_id = request.form['session_id']
        session = Session.query.get_or_404(session_id)
        member_ids = request.form.getlist('member_ids[]')
        attended_ids = request.form.getlist('attended_ids[]')
        
        # Validate memberships
        invalid_members = []
        for member_id in member_ids:
            if not has_active_membership(member_id, session.session_date):
                member = Member.query.get(member_id)
                invalid_members.append(member.name)
        
        if invalid_members:
            flash(f'Error: The following members do not have active memberships: {", ".join(invalid_members)}', 'danger')
            return redirect(url_for('view_class', id=session_id))
        
        # Delete existing attendance records for this session
        Attendance.query.filter_by(session_id=session_id).delete()
        
        # Create new attendance records
        for member_id in member_ids:
            attendance = Attendance(
                member_id=member_id,
                session_id=session_id,
                attended=member_id in attended_ids
            )
            db.session.add(attendance)
        
        db.session.commit()
        app.logger.info(f'Batch attendance recorded for session {session_id}')
        flash('Attendance recorded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error recording batch attendance: {str(e)}')
        flash(f'Error recording attendance: {str(e)}', 'danger')
    return redirect(url_for('view_class', id=session_id))

@app.route('/attendance/<int:id>/delete', methods=['GET'])
def delete_attendance(id):
    try:
        attendance = Attendance.query.get_or_404(id)
        db.session.delete(attendance)
        db.session.commit()
        flash('Attendance record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting attendance record: {str(e)}', 'danger')
    return redirect(url_for('attendance'))

@app.route('/attendance/<int:id>/edit', methods=['POST'])
def edit_attendance(id):
    try:
        attendance = Attendance.query.get_or_404(id)
        attendance.attended = request.form.get('attended') == 'true'
        db.session.commit()
        flash('Attendance updated successfully!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/payments')
@login_required
def payments():
    payments = Payment.query.join(Member).all()
    members = Member.query.all()
    
    # Calculate payment summaries
    total_payments = db.session.query(func.sum(Payment.amount)).scalar() or 0
    first_day_of_month = datetime.today().replace(day=1)
    monthly_payments = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.payment_date >= first_day_of_month)\
        .scalar() or 0
    
    return render_template('payments.html', 
                         payments=payments, 
                         members=members,
                         total_payments=total_payments,
                         monthly_payments=monthly_payments)

@app.route('/record_payment', methods=['POST'])
def record_payment():
    try:
        payment = Payment(
            member_id=request.form['member_id'],
            amount=request.form['amount'],
            payment_method=request.form['payment_method']
        )
        db.session.add(payment)
        db.session.commit()
        flash('Payment recorded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error recording payment: {str(e)}', 'danger')
    return redirect(url_for('payments'))

@app.route('/payments/<int:id>/delete', methods=['GET'])
def delete_payment(id):
    try:
        payment = Payment.query.get_or_404(id)
        db.session.delete(payment)
        db.session.commit()
        flash('Payment record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting payment record: {str(e)}', 'danger')
    return redirect(url_for('payments'))

@app.route('/export/attendance')
def export_attendance():
    try:
        # Query all attendance records with related data
        records = db.session.query(
            Attendance, Member, Session
        ).join(Member).join(Session).all()

        # Create a PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )

        # Add title
        elements.append(Paragraph("Attendance Records", title_style))

        # Create table data
        data = [['Date', 'Member Name', 'Class Name', 'Status']]  # Header row
        for attendance, member, session in records:
            data.append([
                attendance.date.strftime('%Y-%m-%d'),
                member.name,
                session.session_name,
                'Present' if attendance.attended else 'Absent'
            ])

        # Create table
        table = Table(data, colWidths=[1.5*inch, 2*inch, 2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        elements.append(table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        app.logger.info(f'Attendance records exported successfully as PDF')
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': 'attachment; filename=attendance_records.pdf'
            }
        )
    except Exception as e:
        app.logger.error(f'Error exporting attendance records: {str(e)}')
        flash('Error exporting attendance records', 'danger')
        return redirect(url_for('attendance'))

@app.route('/export/payments')
def export_payments():
    try:
        # Query all payment records with member data
        records = Payment.query.join(Member).all()

        # Create a PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )

        # Add title
        elements.append(Paragraph("Payment Records", title_style))

        # Create table data
        data = [['Date', 'Member Name', 'Amount', 'Payment Method']]  # Header row
        for payment in records:
            data.append([
                payment.payment_date.strftime('%Y-%m-%d'),
                payment.member.name,
                f'${float(payment.amount):.2f}',
                payment.payment_method
            ])

        # Create table
        table = Table(data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        elements.append(table)

        # Add total at the bottom
        total = sum(float(payment.amount) for payment in records)
        elements.append(Paragraph(f"<br/><br/>Total Amount: ${total:.2f}", styles['Normal']))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        app.logger.info(f'Payment records exported successfully as PDF')
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': 'attachment; filename=payment_records.pdf'
            }
        )
    except Exception as e:
        app.logger.error(f'Error exporting payment records: {str(e)}')
        flash('Error exporting payment records', 'danger')
        return redirect(url_for('payments'))

# API Endpoints
@app.route('/api/member_plans/<int:member_id>')
@login_required
def get_member_plans(member_id):
    if not current_user.is_admin and current_user.member.member_id != member_id:
        return jsonify({"error": "Access denied"}), 403
        
    plans = db.session.query(MemberPlan, MembershipPlan)\
        .join(MembershipPlan, MemberPlan.plan_id == MembershipPlan.plan_id)\
        .filter(MemberPlan.member_id == member_id)\
        .all()
    
    result = []
    for mp, plan in plans:
        result.append({
            'plan_name': plan.plan_name,
            'start_date': mp.start_date.strftime('%Y-%m-%d'),
            'end_date': mp.end_date.strftime('%Y-%m-%d') if mp.end_date else None,
            'price': float(plan.price),
            'duration': plan.duration_months
        })
    return jsonify(result)

@app.route('/api/check_class_conflict', methods=['POST'])
def check_class_conflict():
    data = request.json
    trainer_id = data.get('trainer_id')
    date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    start_time = datetime.strptime(data.get('start_time'), '%H:%M').time()
    end_time = datetime.strptime(data.get('end_time'), '%H:%M').time()
    
    # Check for existing classes in the time range
    conflicts = Session.query.filter(
        Session.trainer_id == trainer_id,
        Session.session_date == date,
        or_(
            and_(Session.start_time <= start_time, Session.end_time > start_time),
            and_(Session.start_time < end_time, Session.end_time >= end_time),
            and_(Session.start_time >= start_time, Session.end_time <= end_time)
        )
    ).all()
    
    return jsonify({'conflict': len(conflicts) > 0})

@app.route('/api/trainer_schedule/<int:trainer_id>')
def trainer_schedule(trainer_id):
    # Get next 7 days of classes for the trainer
    today = datetime.today().date()
    week_later = today + timedelta(days=7)
    
    classes = Session.query.filter(
        Session.trainer_id == trainer_id,
        Session.session_date >= today,
        Session.session_date <= week_later
    ).order_by(Session.session_date, Session.start_time).all()
    
    schedule = []
    for cls in classes:
        schedule.append({
            'session_name': cls.session_name,
            'date': cls.session_date.strftime('%Y-%m-%d'),
            'start_time': cls.start_time.strftime('%H:%M'),
            'end_time': cls.end_time.strftime('%H:%M')
        })
    
    return jsonify(schedule)

@app.route('/api/payment_details/<int:payment_id>')
def payment_details(payment_id):
    payment = Payment.query.join(Member).filter(Payment.payment_id == payment_id).first()
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
        
    return jsonify({
        'payment_id': payment.payment_id,
        'member_name': payment.member.name,
        'amount': float(payment.amount),
        'date': payment.payment_date.strftime('%Y-%m-%d %H:%M'),
        'method': payment.payment_method
    })

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    app.logger.info(f'Page not found: {request.url}')
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f'Server Error: {e}')
    app.logger.error(f'Request: {request.url}\nData: {request.data}')
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)