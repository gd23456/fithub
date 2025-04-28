from datetime import datetime, timedelta
from app import db, Member, MemberPlan

class Notification:
    @staticmethod
    def get_expiring_memberships(days=7):
        """Get list of members whose memberships are expiring within given days"""
        today = datetime.now().date()
        expiry_date = today + timedelta(days=days)
        
        expiring_plans = MemberPlan.query.join(Member).filter(
            MemberPlan.end_date.between(today, expiry_date)
        ).all()
        
        return [{
            'member_name': plan.member.name,
            'plan_name': plan.plan.plan_name,
            'expiry_date': plan.end_date.strftime('%Y-%m-%d')
        } for plan in expiring_plans]
    
    @staticmethod
    def get_birthday_members():
        """Get list of members who have birthdays today"""
        today = datetime.now().date()
        return Member.query.filter(
            db.func.extract('month', Member.date_of_birth) == today.month,
            db.func.extract('day', Member.date_of_birth) == today.day
        ).all()
    
    @staticmethod
    def get_inactive_members(days=30):
        """Get list of members who haven't attended any classes in given days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        inactive_members = Member.query.join(
            MemberPlan, Member.member_id == MemberPlan.member_id
        ).outerjoin(
            Attendance, Member.member_id == Attendance.member_id
        ).group_by(Member.member_id).having(
            db.or_(
                db.func.max(Attendance.date) < cutoff_date,
                db.func.count(Attendance.attendance_id) == 0
            )
        ).all()
        
        return inactive_members