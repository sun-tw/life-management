from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, BudgetYear, BudgetCategory, BudgetSubcategory, Loan
from datetime import date

budget_bp = Blueprint('budget', __name__, url_prefix='/budget')

@budget_bp.route('/')
@login_required
def index():
    years = BudgetYear.query.order_by(BudgetYear.year.desc()).all()
    current_year = date.today().year
    current_budget = BudgetYear.query.filter_by(year=current_year).first()
    return render_template('budget/index.html',
        years=years,
        current_budget=current_budget,
        current_year=current_year
    )

@budget_bp.route('/year/<int:year>')
@login_required
def year_detail(year):
    budget = BudgetYear.query.filter_by(year=year).first_or_404()
    income_cats = [c for c in budget.categories if c.category_type == 'income']
    expense_cats = [c for c in budget.categories if c.category_type == 'expense']

    # 固定支出：自動帶入貸款
    active_loans = Loan.query.filter_by(status='active').all()
    monthly_loan_total = sum(l.monthly_payment for l in active_loans)
    annual_loan_total = monthly_loan_total * 12

    return render_template('budget/year.html',
        budget=budget,
        income_cats=income_cats,
        expense_cats=expense_cats,
        year=year,
        active_loans=active_loans,
        annual_loan_total=annual_loan_total
    )

@budget_bp.route('/create', methods=['POST'])
@login_required
def create_year():
    year = int(request.form['year'])
    existing = BudgetYear.query.filter_by(year=year).first()
    if existing:
        flash(f'{year} 年的預算計劃已存在', 'warning')
        return redirect(url_for('budget.year_detail', year=year))
    budget = BudgetYear(year=year, created_by=current_user.id)
    db.session.add(budget)
    db.session.flush()

    # 預設類別
    default_income = ['薪資收入', '業外收入', '投資收益', '租金收入', '其他收入']
    default_expense = ['貸款還款', '生活費用', '交通費用', '醫療健康', '教育學習', '旅遊娛樂', '保險費用', '其他支出']
    for i, name in enumerate(default_income):
        db.session.add(BudgetCategory(budget_year_id=budget.id, category_name=name, category_type='income', sort_order=i))
    for i, name in enumerate(default_expense):
        db.session.add(BudgetCategory(budget_year_id=budget.id, category_name=name, category_type='expense', sort_order=i))
    db.session.commit()
    flash(f'{year} 年預算計劃已建立', 'success')
    return redirect(url_for('budget.year_detail', year=year))

@budget_bp.route('/category/add', methods=['POST'])
@login_required
def add_category():
    budget_id = int(request.form['budget_year_id'])
    cat = BudgetCategory(
        budget_year_id=budget_id,
        category_name=request.form['category_name'],
        category_type=request.form['category_type'],
        planned_amount=float(request.form.get('planned_amount', 0)),
        actual_amount=float(request.form.get('actual_amount', 0)),
    )
    db.session.add(cat)
    db.session.commit()
    budget = BudgetYear.query.get(budget_id)
    return redirect(url_for('budget.year_detail', year=budget.year))

@budget_bp.route('/category/update/<int:cat_id>', methods=['POST'])
@login_required
def update_category(cat_id):
    cat = BudgetCategory.query.get_or_404(cat_id)
    cat.category_name = request.form.get('category_name', cat.category_name)
    cat.planned_amount = float(request.form.get('planned_amount', cat.planned_amount))
    cat.actual_amount = float(request.form.get('actual_amount', cat.actual_amount))
    db.session.commit()
    return redirect(url_for('budget.year_detail', year=cat.budget_year.year))

@budget_bp.route('/category/delete/<int:cat_id>', methods=['POST'])
@login_required
def delete_category(cat_id):
    cat = BudgetCategory.query.get_or_404(cat_id)
    year = cat.budget_year.year
    db.session.delete(cat)
    db.session.commit()
    return redirect(url_for('budget.year_detail', year=year))

@budget_bp.route('/subcategory/add', methods=['POST'])
@login_required
def add_subcategory():
    cat_id = int(request.form['category_id'])
    sub = BudgetSubcategory(
        category_id=cat_id,
        subcategory_name=request.form['subcategory_name'],
        planned_amount=float(request.form.get('planned_amount', 0)),
        actual_amount=float(request.form.get('actual_amount', 0)),
        notes=request.form.get('notes', '')
    )
    db.session.add(sub)
    db.session.commit()
    cat = BudgetCategory.query.get(cat_id)
    return redirect(url_for('budget.year_detail', year=cat.budget_year.year))

@budget_bp.route('/subcategory/update/<int:sub_id>', methods=['POST'])
@login_required
def update_subcategory(sub_id):
    sub = BudgetSubcategory.query.get_or_404(sub_id)
    sub.subcategory_name = request.form.get('subcategory_name', sub.subcategory_name)
    sub.planned_amount = float(request.form.get('planned_amount', sub.planned_amount))
    sub.actual_amount = float(request.form.get('actual_amount', sub.actual_amount))
    sub.notes = request.form.get('notes', sub.notes)
    db.session.commit()
    year = sub.category.budget_year.year
    return redirect(url_for('budget.year_detail', year=year))

@budget_bp.route('/subcategory/delete/<int:sub_id>', methods=['POST'])
@login_required
def delete_subcategory(sub_id):
    sub = BudgetSubcategory.query.get_or_404(sub_id)
    year = sub.category.budget_year.year
    db.session.delete(sub)
    db.session.commit()
    return redirect(url_for('budget.year_detail', year=year))
