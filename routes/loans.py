from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Loan
from datetime import date, datetime

loans_bp = Blueprint('loans', __name__, url_prefix='/loans')

LOAN_TYPES = ['車貸', '房貸', '周轉金', '信貸', '其他']

@loans_bp.route('/')
@login_required
def index():
    loans = Loan.query.order_by(Loan.status, Loan.loan_type).all()
    active_loans = [l for l in loans if l.status == 'active']
    paid_loans = [l for l in loans if l.status == 'paid']
    total_monthly = sum(l.monthly_payment for l in active_loans)
    total_balance = sum(l.current_balance for l in active_loans)
    return render_template('loans/index.html',
        active_loans=active_loans,
        paid_loans=paid_loans,
        total_monthly=total_monthly,
        total_balance=total_balance,
        loan_types=LOAN_TYPES
    )

@loans_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        loan = Loan(
            name=request.form['name'],
            loan_type=request.form['loan_type'],
            borrower_name=request.form['borrower_name'],
            original_amount=float(request.form['original_amount'] or 0),
            current_balance=float(request.form['current_balance'] or 0),
            monthly_payment=float(request.form['monthly_payment'] or 0),
            interest_only='interest_only' in request.form,
            interest_rate=float(request.form['interest_rate']) if request.form.get('interest_rate') else None,
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else None,
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None,
            status=request.form.get('status', 'active'),
            notes=request.form.get('notes', '')
        )
        db.session.add(loan)
        db.session.commit()
        flash(f'貸款「{loan.name}」已新增', 'success')
        return redirect(url_for('loans.index'))
    return render_template('loans/form.html', loan=None, loan_types=LOAN_TYPES, action='新增')

@loans_bp.route('/edit/<int:loan_id>', methods=['GET', 'POST'])
@login_required
def edit(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if request.method == 'POST':
        loan.name = request.form['name']
        loan.loan_type = request.form['loan_type']
        loan.borrower_name = request.form['borrower_name']
        loan.original_amount = float(request.form['original_amount'] or 0)
        loan.current_balance = float(request.form['current_balance'] or 0)
        loan.monthly_payment = float(request.form['monthly_payment'] or 0)
        loan.interest_only = 'interest_only' in request.form
        loan.interest_rate = float(request.form['interest_rate']) if request.form.get('interest_rate') else None
        loan.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else None
        loan.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None
        loan.status = request.form.get('status', 'active')
        loan.notes = request.form.get('notes', '')
        loan.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'貸款「{loan.name}」已更新', 'success')
        return redirect(url_for('loans.index'))
    return render_template('loans/form.html', loan=loan, loan_types=LOAN_TYPES, action='編輯')

@loans_bp.route('/delete/<int:loan_id>', methods=['POST'])
@login_required
def delete(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    name = loan.name
    db.session.delete(loan)
    db.session.commit()
    flash(f'貸款「{name}」已刪除', 'success')
    return redirect(url_for('loans.index'))

@loans_bp.route('/api/summary')
@login_required
def api_summary():
    loans = Loan.query.filter_by(status='active').all()
    data = []
    for l in loans:
        data.append({
            'id': l.id,
            'name': l.name,
            'type': l.loan_type,
            'borrower': l.borrower_name,
            'balance': l.current_balance,
            'monthly': l.monthly_payment,
            'interest_only': l.interest_only,
            'payoff_date': l.payoff_date_estimate().isoformat() if l.payoff_date_estimate() else None
        })
    return jsonify(data)
