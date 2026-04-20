from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Document
from datetime import datetime, date

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

DOC_TYPES = ['護照', '房契', '保單', '駕照', '身分證', '合約', '車輛行照', '健保卡', '其他']


@documents_bp.route('/')
@login_required
def index():
    docs = Document.query.filter_by(user_id=current_user.id).order_by(
        Document.is_important.desc(), Document.doc_type
    ).all() if hasattr(Document, 'user_id') else Document.query.order_by(
        Document.is_important.desc(), Document.doc_type
    ).all()

    expiring = [d for d in docs if d.is_expiring_soon(90)]

    # 按重要度和類型分組
    important_docs = [d for d in docs if d.is_important]
    regular_docs = [d for d in docs if not d.is_important]

    grouped_regular = {}
    for t in DOC_TYPES:
        items = [d for d in regular_docs if d.doc_type == t]
        if items:
            grouped_regular[t] = items

    return render_template(
        'documents/index.html',
        docs=docs,
        expiring=expiring,
        important_docs=important_docs,
        grouped_regular=grouped_regular,
        doc_types=DOC_TYPES
    )


@documents_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            doc = Document(
                name=request.form.get('name', '').strip(),
                doc_type=request.form.get('doc_type', ''),
                owner_name=request.form.get('owner_name', '').strip(),
                issue_date=_parse_date(request.form.get('issue_date')),
                expiry_date=_parse_date(request.form.get('expiry_date')),
                storage_location=request.form.get('storage_location', '').strip(),
                notes=request.form.get('notes', '').strip(),
                is_important=bool(request.form.get('is_important'))
            )
            if hasattr(Document, 'user_id'):
                doc.user_id = current_user.id
            db.session.add(doc)
            db.session.commit()
            flash('文件已新增', 'success')
            return redirect(url_for('data_hub.index', tab='documents'))
        except Exception as e:
            db.session.rollback()
            flash(f'新增失敗：{str(e)}', 'error')

    return render_template('documents/form.html', doc=None, doc_types=DOC_TYPES, action='add')


@documents_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    doc = Document.query.get_or_404(id)

    if request.method == 'POST':
        try:
            doc.name = request.form.get('name', '').strip()
            doc.doc_type = request.form.get('doc_type', '')
            doc.owner_name = request.form.get('owner_name', '').strip()
            doc.issue_date = _parse_date(request.form.get('issue_date'))
            doc.expiry_date = _parse_date(request.form.get('expiry_date'))
            doc.storage_location = request.form.get('storage_location', '').strip()
            doc.notes = request.form.get('notes', '').strip()
            doc.is_important = bool(request.form.get('is_important'))
            db.session.commit()
            flash('文件已更新', 'success')
            return redirect(url_for('data_hub.index', tab='documents'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗：{str(e)}', 'error')

    return render_template('documents/form.html', doc=doc, doc_types=DOC_TYPES, action='edit')


@documents_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    doc = Document.query.get_or_404(id)
    try:
        db.session.delete(doc)
        db.session.commit()
        flash('文件已刪除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'刪除失敗：{str(e)}', 'error')
    return redirect(url_for('data_hub.index', tab='documents'))


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None
