from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Contact

contacts_bp = Blueprint('contacts', __name__, url_prefix='/contacts')

CATEGORIES = ['醫療', '法律', '財務', '保險', '緊急', '家人', '朋友', '其他']


@contacts_bp.route('/')
@login_required
def index():
    important = Contact.query.filter_by(is_important=True).order_by(Contact.name).all()
    others = Contact.query.filter_by(is_important=False).order_by(Contact.category, Contact.name).all()

    grouped = {}
    for c in others:
        grouped.setdefault(c.category, []).append(c)

    return render_template('contacts/index.html',
        important=important,
        grouped=grouped,
        categories=CATEGORIES
    )


@contacts_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        contact = Contact(
            name=request.form['name'],
            category=request.form['category'],
            relationship=request.form.get('relationship', ''),
            phone=request.form.get('phone', ''),
            email=request.form.get('email', ''),
            address=request.form.get('address', ''),
            institution=request.form.get('institution', ''),
            is_important=bool(request.form.get('is_important')),
            notes=request.form.get('notes', '')
        )
        db.session.add(contact)
        db.session.commit()
        flash('聯絡人已新增！', 'success')
        return redirect(url_for('contacts.index'))
    return render_template('contacts/form.html',
        contact=None,
        categories=CATEGORIES,
        action='新增'
    )


@contacts_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    contact = Contact.query.get_or_404(id)
    if request.method == 'POST':
        contact.name = request.form['name']
        contact.category = request.form['category']
        contact.relationship = request.form.get('relationship', '')
        contact.phone = request.form.get('phone', '')
        contact.email = request.form.get('email', '')
        contact.address = request.form.get('address', '')
        contact.institution = request.form.get('institution', '')
        contact.is_important = bool(request.form.get('is_important'))
        contact.notes = request.form.get('notes', '')
        db.session.commit()
        flash('聯絡人已更新！', 'success')
        return redirect(url_for('contacts.index'))
    return render_template('contacts/form.html',
        contact=contact,
        categories=CATEGORIES,
        action='編輯'
    )


@contacts_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('聯絡人已刪除。', 'success')
    return redirect(url_for('contacts.index'))
