import os
import tempfile
import json
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from models import db, Transaction
from datetime import datetime, date
from sqlalchemy import extract

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

EXPENSE_CATEGORIES = ['餐飲', '交通', '購物', '娛樂', '醫療', '教育', '住宿',
                      '車輛', '訂閱服務', '手續費', '貸款還款', '保險', '其他']
INCOME_CATEGORIES  = ['薪資', '業外收入', '投資收益', '租金收入', '其他收入']


# ── 收支列表 ──────────────────────────────────────────────────────────────────
@transactions_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    today = date.today()
    year  = request.args.get('year',  today.year,  type=int)
    month = request.args.get('month', today.month, type=int)

    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract('year',  Transaction.date) == year,
        extract('month', Transaction.date) == month
    ).order_by(Transaction.date.desc()).all()

    total_income  = sum(t.amount for t in transactions if t.trans_type == 'income')
    total_expense = sum(t.amount for t in transactions if t.trans_type == 'expense')
    balance       = total_income - total_expense

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
        today=today,
        expense_categories=EXPENSE_CATEGORIES,
        income_categories=INCOME_CATEGORIES,
    )


# ── 新增單筆 ──────────────────────────────────────────────────────────────────
@transactions_bp.route('/add', methods=['POST'])
@login_required
def add():
    try:
        date_str   = request.form.get('date')
        trans_type = request.form.get('trans_type')
        category   = request.form.get('category', '').strip()
        amount_str = request.form.get('amount', '0')
        description = request.form.get('description', '').strip()

        if not date_str or not trans_type or not category or not amount_str:
            flash('請填寫所有必填欄位', 'error')
            return redirect(url_for('transactions.index'))

        trans_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        amount     = float(amount_str)

        if amount <= 0:
            flash('金額必須大於 0', 'error')
            return redirect(url_for('transactions.index'))

        t = Transaction(
            date=trans_date, trans_type=trans_type, category=category,
            amount=amount, description=description,
            user_id=current_user.id, created_at=datetime.utcnow()
        )
        db.session.add(t)
        db.session.commit()
        flash('交易記錄已新增', 'success')
    except ValueError:
        flash('資料格式有誤，請重新輸入', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'新增失敗：{str(e)}', 'error')

    year  = request.form.get('year',  date.today().year)
    month = request.form.get('month', date.today().month)
    return redirect(url_for('transactions.index', year=year, month=month))


# ── 刪除單筆 ──────────────────────────────────────────────────────────────────
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


# ── 信用卡帳單匯入 ────────────────────────────────────────────────────────────
@transactions_bp.route('/import-cc', methods=['GET', 'POST'])
@login_required
def import_cc():
    """上傳帳單 PDF → 解析 → 跳到預覽頁"""
    if request.method == 'GET':
        return render_template('transactions/import_cc.html')

    # POST：接收 PDF
    pdf_file = request.files.get('pdf_file')
    if not pdf_file or not pdf_file.filename.lower().endswith('.pdf'):
        flash('請上傳 PDF 格式的信用卡帳單', 'error')
        return render_template('transactions/import_cc.html')

    # 存到暫存目錄
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    try:
        pdf_file.save(tmp.name)
        tmp.close()

        from utils.cc_parser import parse_cathay_pdf
        txns, bill_year, bill_month, card_last4 = parse_cathay_pdf(tmp.name)
    except RuntimeError as e:
        flash(str(e), 'error')
        return render_template('transactions/import_cc.html')
    except Exception as e:
        flash(f'解析失敗：{str(e)}', 'error')
        return render_template('transactions/import_cc.html')
    finally:
        os.unlink(tmp.name)

    if not txns:
        flash('未能從帳單中解析出任何交易，請確認 PDF 格式正確', 'warning')
        return render_template('transactions/import_cc.html')

    # 重複偵測：比對相同 (user, date, amount, description) 的記錄
    existing = set()
    for t in Transaction.query.filter_by(user_id=current_user.id).all():
        existing.add((str(t.date), t.amount, (t.description or '').strip()))

    for tx in txns:
        key = (str(tx['date']), tx['amount'], tx['description'].strip())
        tx['duplicate'] = key in existing

    # 序列化到暫存檔（session 只存檔名，避免超過 cookie 4KB 上限）
    serial = [{ **tx, 'date': str(tx['date']) } for tx in txns]
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix='.json', mode='w', encoding='utf-8'
    )
    json.dump(serial, tmp, ensure_ascii=False)
    tmp.close()

    # 清掉舊暫存
    old = session.get('cc_import_file')
    if old and os.path.exists(old):
        try: os.unlink(old)
        except Exception: pass
    session['cc_import_file'] = tmp.name

    return render_template(
        'transactions/import_preview.html',
        txns=txns,
        bill_year=bill_year,
        bill_month=bill_month,
        card_last4=card_last4,
        expense_categories=EXPENSE_CATEGORIES,
        income_categories=INCOME_CATEGORIES,
    )


# ── 確認匯入 ──────────────────────────────────────────────────────────────────
@transactions_bp.route('/import-cc/confirm', methods=['POST'])
@login_required
def import_cc_confirm():
    """接收使用者勾選的交易，寫入資料庫"""
    # 從 form 重建要匯入的列表
    indices = request.form.getlist('include')  # 勾選的索引

    # 讀取暫存檔
    tmp_file = session.get('cc_import_file')
    if not tmp_file or not os.path.exists(tmp_file):
        flash('匯入資料已過期，請重新上傳帳單', 'error')
        return redirect(url_for('transactions.import_cc'))

    with open(tmp_file, 'r', encoding='utf-8') as f:
        raw = f.read()

    all_txns = json.loads(raw)
    imported = 0
    skipped  = 0

    for idx_str in indices:
        try:
            idx = int(idx_str)
            tx  = all_txns[idx]
        except (ValueError, IndexError):
            continue

        # 類別可能被使用者在 form 中修改
        override_cat  = request.form.get(f'category_{idx}', '').strip()
        override_type = request.form.get(f'trans_type_{idx}', '').strip()

        category   = override_cat  or tx['category']
        trans_type = override_type or tx['trans_type']

        try:
            tx_date = datetime.strptime(tx['date'], '%Y-%m-%d').date()
            amount  = float(tx['amount'])
        except (ValueError, KeyError):
            skipped += 1
            continue

        t = Transaction(
            date=tx_date,
            trans_type=trans_type,
            category=category,
            amount=amount,
            description=tx.get('description', ''),
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )
        db.session.add(t)
        imported += 1

    try:
        db.session.commit()
        # 清掉暫存
        if tmp_file and os.path.exists(tmp_file):
            try: os.unlink(tmp_file)
            except Exception: pass
        session.pop('cc_import_file', None)
        flash(f'成功匯入 {imported} 筆交易記錄 ✓', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'匯入失敗：{str(e)}', 'error')
        return redirect(url_for('transactions.import_cc'))

    # 跳到帳單月份
    if all_txns:
        try:
            d = datetime.strptime(all_txns[0]['date'], '%Y-%m-%d')
            return redirect(url_for('transactions.index', year=d.year, month=d.month))
        except Exception:
            pass
    return redirect(url_for('transactions.index'))
