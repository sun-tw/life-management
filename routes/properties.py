from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from models import db, Property, Loan
from datetime import datetime

properties_bp = Blueprint('properties', __name__, url_prefix='/properties')

PROPERTY_STATUSES = ['持有中', '已售出', '交屋中', '出租中']

@properties_bp.route('/')
@login_required
def index():
    props = Property.query.all()
    loans = Loan.query.filter_by(status='active').all()
    return render_template('properties/index.html', properties=props, loans=loans)

@properties_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    loans = Loan.query.filter_by(status='active').all()
    if request.method == 'POST':
        p = Property(
            name=request.form['name'],
            property_type=request.form['property_type'],
            owner_name=request.form['owner_name'],
            address=request.form.get('address', ''),
            status=request.form.get('status', '持有中'),
            loan_id=int(request.form['loan_id']) if request.form.get('loan_id') else None,
            purchase_date=datetime.strptime(request.form['purchase_date'], '%Y-%m-%d').date() if request.form.get('purchase_date') else None,
            sale_date=datetime.strptime(request.form['sale_date'], '%Y-%m-%d').date() if request.form.get('sale_date') else None,
            handover_date=datetime.strptime(request.form['handover_date'], '%Y-%m-%d').date() if request.form.get('handover_date') else None,
            estimated_value=float(request.form['estimated_value']) if request.form.get('estimated_value') else None,
            notes=request.form.get('notes', '')
        )
        db.session.add(p)
        db.session.commit()
        flash(f'房產「{p.name}」已新增', 'success')
        return redirect(url_for('assets.index', tab='properties'))
    return render_template('properties/form.html', property=None, loans=loans, statuses=PROPERTY_STATUSES, action='新增')

@properties_bp.route('/edit/<int:pid>', methods=['GET', 'POST'])
@login_required
def edit(pid):
    p = Property.query.get_or_404(pid)
    loans = Loan.query.filter_by(status='active').all()
    if request.method == 'POST':
        p.name = request.form['name']
        p.property_type = request.form['property_type']
        p.owner_name = request.form['owner_name']
        p.address = request.form.get('address', '')
        p.status = request.form.get('status', '持有中')
        p.loan_id = int(request.form['loan_id']) if request.form.get('loan_id') else None
        p.purchase_date = datetime.strptime(request.form['purchase_date'], '%Y-%m-%d').date() if request.form.get('purchase_date') else None
        p.sale_date = datetime.strptime(request.form['sale_date'], '%Y-%m-%d').date() if request.form.get('sale_date') else None
        p.handover_date = datetime.strptime(request.form['handover_date'], '%Y-%m-%d').date() if request.form.get('handover_date') else None
        p.estimated_value = float(request.form['estimated_value']) if request.form.get('estimated_value') else None
        p.notes = request.form.get('notes', '')
        db.session.commit()
        flash(f'房產「{p.name}」已更新', 'success')
        return redirect(url_for('assets.index', tab='properties'))
    return render_template('properties/form.html', property=p, loans=loans, statuses=PROPERTY_STATUSES, action='編輯')

@properties_bp.route('/delete/<int:pid>', methods=['POST'])
@login_required
def delete(pid):
    p = Property.query.get_or_404(pid)
    name = p.name
    db.session.delete(p)
    db.session.commit()
    flash(f'房產「{name}」已刪除', 'success')
    return redirect(url_for('assets.index', tab='properties'))
