from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Investment
from datetime import date, datetime

investments_bp = Blueprint('investments', __name__, url_prefix='/investments')

INVESTMENT_TYPES = ['股票', 'ETF', '基金', '定存', '儲蓄險', '債券', '外幣', '房地產', '其他']
CURRENCIES = ['TWD', 'USD']


@investments_bp.route('/')
@login_required
def index():
    investments = Investment.query.order_by(Investment.investment_type, Investment.name).all()

    total_invested = sum(i.amount_invested for i in investments)
    total_current = sum(i.current_value for i in investments)
    total_gain = total_current - total_invested
    total_gain_pct = round((total_gain / total_invested * 100), 2) if total_invested else 0

    # 依類型分組
    grouped = {}
    for inv in investments:
        grouped.setdefault(inv.investment_type, []).append(inv)

    return render_template('investments/index.html',
        investments=investments,
        grouped=grouped,
        investment_types=INVESTMENT_TYPES,
        total_invested=total_invested,
        total_current=total_current,
        total_gain=total_gain,
        total_gain_pct=total_gain_pct
    )


@investments_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        inv = Investment(
            name=request.form['name'],
            investment_type=request.form['investment_type'],
            institution=request.form.get('institution', ''),
            owner_name=request.form['owner_name'],
            amount_invested=float(request.form.get('amount_invested', 0)),
            current_value=float(request.form.get('current_value', 0)),
            currency=request.form.get('currency', 'TWD'),
            purchase_date=date.fromisoformat(request.form['purchase_date']) if request.form.get('purchase_date') else None,
            maturity_date=date.fromisoformat(request.form['maturity_date']) if request.form.get('maturity_date') else None,
            annual_return=float(request.form['annual_return']) if request.form.get('annual_return') else None,
            notes=request.form.get('notes', ''),
            updated_at=datetime.utcnow()
        )
        db.session.add(inv)
        db.session.commit()
        flash('投資項目已新增！', 'success')
        return redirect(url_for('investments.index'))
    return render_template('investments/form.html',
        investment=None,
        investment_types=INVESTMENT_TYPES,
        currencies=CURRENCIES,
        action='新增'
    )


@investments_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    inv = Investment.query.get_or_404(id)
    if request.method == 'POST':
        inv.name = request.form['name']
        inv.investment_type = request.form['investment_type']
        inv.institution = request.form.get('institution', '')
        inv.owner_name = request.form['owner_name']
        inv.amount_invested = float(request.form.get('amount_invested', 0))
        inv.current_value = float(request.form.get('current_value', 0))
        inv.currency = request.form.get('currency', 'TWD')
        inv.purchase_date = date.fromisoformat(request.form['purchase_date']) if request.form.get('purchase_date') else None
        inv.maturity_date = date.fromisoformat(request.form['maturity_date']) if request.form.get('maturity_date') else None
        inv.annual_return = float(request.form['annual_return']) if request.form.get('annual_return') else None
        inv.notes = request.form.get('notes', '')
        inv.updated_at = datetime.utcnow()
        db.session.commit()
        flash('投資項目已更新！', 'success')
        return redirect(url_for('investments.index'))
    return render_template('investments/form.html',
        investment=inv,
        investment_types=INVESTMENT_TYPES,
        currencies=CURRENCIES,
        action='編輯'
    )


@investments_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    inv = Investment.query.get_or_404(id)
    db.session.delete(inv)
    db.session.commit()
    flash('投資項目已刪除。', 'success')
    return redirect(url_for('investments.index'))
