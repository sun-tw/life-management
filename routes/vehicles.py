from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from models import db, Vehicle, Loan
from datetime import datetime

vehicles_bp = Blueprint('vehicles', __name__, url_prefix='/vehicles')

@vehicles_bp.route('/')
@login_required
def index():
    vehicles = Vehicle.query.all()
    loans = Loan.query.filter_by(status='active').all()
    return render_template('vehicles/index.html', vehicles=vehicles, loans=loans)

@vehicles_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    loans = Loan.query.filter_by(status='active').all()
    if request.method == 'POST':
        v = Vehicle(
            name=request.form['name'],
            vehicle_type=request.form['vehicle_type'],
            brand=request.form.get('brand', ''),
            model=request.form.get('model', ''),
            year=int(request.form['year']) if request.form.get('year') else None,
            plate_number=request.form.get('plate_number', ''),
            owner_name=request.form['owner_name'],
            loan_id=int(request.form['loan_id']) if request.form.get('loan_id') else None,
            insurance_due=datetime.strptime(request.form['insurance_due'], '%Y-%m-%d').date() if request.form.get('insurance_due') else None,
            maintenance_due=datetime.strptime(request.form['maintenance_due'], '%Y-%m-%d').date() if request.form.get('maintenance_due') else None,
            notes=request.form.get('notes', '')
        )
        db.session.add(v)
        db.session.commit()
        flash(f'車輛「{v.name}」已新增', 'success')
        return redirect(url_for('vehicles.index'))
    return render_template('vehicles/form.html', vehicle=None, loans=loans, action='新增')

@vehicles_bp.route('/edit/<int:vid>', methods=['GET', 'POST'])
@login_required
def edit(vid):
    v = Vehicle.query.get_or_404(vid)
    loans = Loan.query.filter_by(status='active').all()
    if request.method == 'POST':
        v.name = request.form['name']
        v.vehicle_type = request.form['vehicle_type']
        v.brand = request.form.get('brand', '')
        v.model = request.form.get('model', '')
        v.year = int(request.form['year']) if request.form.get('year') else None
        v.plate_number = request.form.get('plate_number', '')
        v.owner_name = request.form['owner_name']
        v.loan_id = int(request.form['loan_id']) if request.form.get('loan_id') else None
        v.insurance_due = datetime.strptime(request.form['insurance_due'], '%Y-%m-%d').date() if request.form.get('insurance_due') else None
        v.maintenance_due = datetime.strptime(request.form['maintenance_due'], '%Y-%m-%d').date() if request.form.get('maintenance_due') else None
        v.notes = request.form.get('notes', '')
        db.session.commit()
        flash(f'車輛「{v.name}」已更新', 'success')
        return redirect(url_for('vehicles.index'))
    return render_template('vehicles/form.html', vehicle=v, loans=loans, action='編輯')

@vehicles_bp.route('/delete/<int:vid>', methods=['POST'])
@login_required
def delete(vid):
    v = Vehicle.query.get_or_404(vid)
    name = v.name
    db.session.delete(v)
    db.session.commit()
    flash(f'車輛「{name}」已刪除', 'success')
    return redirect(url_for('vehicles.index'))
