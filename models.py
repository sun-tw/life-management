from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='member')  # admin / member
    birth_date = db.Column(db.Date, nullable=True)
    life_expectancy = db.Column(db.Integer, default=82)
    avatar_color = db.Column(db.String(20), default='#4F46E5')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def remaining_days(self):
        if not self.birth_date:
            return None
        target = date(self.birth_date.year + self.life_expectancy, self.birth_date.month, self.birth_date.day)
        delta = target - date.today()
        return max(0, delta.days)

    def remaining_waking_hours(self):
        days = self.remaining_days()
        if days is None:
            return None
        return days * 16  # 16 waking hours per day


class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    loan_type = db.Column(db.String(50), nullable=False)  # 車貸/房貸/周轉金/其他
    borrower_name = db.Column(db.String(100), nullable=False)  # 自訂借款人名稱
    original_amount = db.Column(db.Float, nullable=False)
    current_balance = db.Column(db.Float, nullable=False)
    monthly_payment = db.Column(db.Float, nullable=False)
    interest_only = db.Column(db.Boolean, default=False)
    interest_rate = db.Column(db.Float, nullable=True)  # 年利率 %
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active')  # active / paid
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def months_remaining(self):
        if self.interest_only or self.monthly_payment <= 0:
            return None
        if self.end_date:
            today = date.today()
            if self.end_date <= today:
                return 0
            months = (self.end_date.year - today.year) * 12 + (self.end_date.month - today.month)
            return max(0, months)
        if self.current_balance <= 0:
            return 0
        principal_payment = self.monthly_payment
        if principal_payment <= 0:
            return None
        return int(self.current_balance / principal_payment)

    def payoff_date_estimate(self):
        months = self.months_remaining()
        if months is None:
            return None
        today = date.today()
        year = today.year + (today.month + months - 1) // 12
        month = (today.month + months - 1) % 12 + 1
        return date(year, month, 1)


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vehicle_type = db.Column(db.String(20), nullable=False)  # 汽車/機車
    brand = db.Column(db.String(50), nullable=True)
    model = db.Column(db.String(50), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    plate_number = db.Column(db.String(20), nullable=True)
    owner_name = db.Column(db.String(100), nullable=False)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=True)
    insurance_due = db.Column(db.Date, nullable=True)
    maintenance_due = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    loan = db.relationship('Loan', backref='vehicles')


class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    property_type = db.Column(db.String(50), nullable=False)  # 住宅/商業/門市
    owner_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='持有中')  # 持有中/已售出/交屋中
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    sale_date = db.Column(db.Date, nullable=True)
    handover_date = db.Column(db.Date, nullable=True)
    estimated_value = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    loan = db.relationship('Loan', backref='properties')


class BudgetYear(db.Model):
    __tablename__ = 'budget_years'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False, unique=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    categories = db.relationship('BudgetCategory', backref='budget_year', cascade='all, delete-orphan')

    def total_income_planned(self):
        return sum(c.planned_amount for c in self.categories if c.category_type == 'income')

    def total_expense_planned(self):
        return sum(c.planned_amount for c in self.categories if c.category_type == 'expense')

    def net_planned(self):
        return self.total_income_planned() - self.total_expense_planned()


class BudgetCategory(db.Model):
    __tablename__ = 'budget_categories'
    id = db.Column(db.Integer, primary_key=True)
    budget_year_id = db.Column(db.Integer, db.ForeignKey('budget_years.id'), nullable=False)
    category_name = db.Column(db.String(100), nullable=False)
    category_type = db.Column(db.String(20), nullable=False)  # income / expense
    planned_amount = db.Column(db.Float, default=0)
    actual_amount = db.Column(db.Float, default=0)
    sort_order = db.Column(db.Integer, default=0)
    subcategories = db.relationship('BudgetSubcategory', backref='category', cascade='all, delete-orphan')

    def achievement_rate(self):
        if self.planned_amount == 0:
            return None
        return round((self.actual_amount / self.planned_amount) * 100, 1)


class BudgetSubcategory(db.Model):
    __tablename__ = 'budget_subcategories'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('budget_categories.id'), nullable=False)
    subcategory_name = db.Column(db.String(100), nullable=False)
    planned_amount = db.Column(db.Float, default=0)
    actual_amount = db.Column(db.Float, default=0)
    notes = db.Column(db.Text, nullable=True)


class TravelPlan(db.Model):
    __tablename__ = 'travel_plans'
    id = db.Column(db.Integer, primary_key=True)
    trip_name = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    total_budget = db.Column(db.Float, default=0)
    status = db.Column(db.String(30), default='計劃中')  # 計劃中/已確認/已完成/已取消
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('TravelItem', backref='travel_plan', cascade='all, delete-orphan')

    def total_planned(self):
        return sum(i.planned_amount for i in self.items)

    def total_actual(self):
        return sum(i.actual_amount or 0 for i in self.items)


class TravelItem(db.Model):
    __tablename__ = 'travel_items'
    id = db.Column(db.Integer, primary_key=True)
    travel_id = db.Column(db.Integer, db.ForeignKey('travel_plans.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 機票/住宿/交通/餐飲/活動/其他
    description = db.Column(db.String(200), nullable=True)
    planned_amount = db.Column(db.Float, default=0)
    actual_amount = db.Column(db.Float, nullable=True)
    is_booked = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
