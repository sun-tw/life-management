from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Transaction
from datetime import datetime, date
from sqlalchemy import extract

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@transactions_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    today = date.today()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)

    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract('year', Transaction.date) == year,
        extract('month', Transaction.date) == month
    ).order_by(Transaction.date.desc()).all()

    total_income = sum(t.amount for t in transactions if t.trans_type == 'income')
    total_expense = sum(t.amount for t in transactions if t.trans_type == 'expense')
    balance = total_income - total_expense

    # 產生月份選項（近 24 個月）
    from dateutil.relativedelta import relativedelta
    months = []
    cursor = date(today.year, today.month, 1)
    for _ in range(24):
        months.append(cursor)
        cursor = cursor - relativedelta(months=1)

    return render_template(
        'transactions/index.html',
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        current_year=year,
        current_month=month,
        months=months,
        today=today
    )


@transactions_bp.route('/add', methods=['POST'])
@login_required
def add():
    try:
        date_str = request.form.get('date')
        trans_type = request.form.get('trans_type')
        category = request.form.get('category', '').strip()
        amount_str = request.form.get('amount', '0')
        description = request.form.get('description', '').strip()

        if not date_str or not trans_type or not category or not amount_str:
            flash('請填寫所有必填欄位', 'error')
            return redirect(url_for('transactions.index'))

        trans_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        amount = float(amount_str)

        if amount <= 0:
            flash('金額必須大於 0', 'error')
            return redirect(url_for('transactions.index'))

        t = Transaction(
            date=trans_date,
            trans_type=trans_type,
            category=category,
            amount=amount,
            description=description,
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )
        db.session.add(t)
        db.session.commit()
        flash('交易記錄已新增', 'success')
    except ValueError:
        flash('資料格式有誤，請重新輸入', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'新增失敗：{str(e)}', 'error')

    year = request.form.get('year', date.today().year)
    month = request.form.get('month', date.today().month)
    return redirect(url_for('transactions.index', year=year, month=month))


@transactions_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    t = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        db.session.delete(t)
        db.session.commit()
        flash('交易記錄已刪除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'刪除失敗：{str(e)}', 'error')
    return redirect(url_for('transactions.index'))
