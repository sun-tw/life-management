from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Goal, GoalMilestone
from datetime import date

goals_bp = Blueprint('goals', __name__, url_prefix='/goals')

CATEGORIES = ['財務', '健康', '學習', '家庭', '旅遊', '事業', '其他']
TIMEFRAMES = ['短期（1年內）', '中期（1-5年）', '長期（5年以上）']
STATUSES = ['進行中', '已完成', '暫停', '放棄']


@goals_bp.route('/')
@login_required
def index():
    active = Goal.query.filter(Goal.status.in_(['進行中', '暫停'])).order_by(Goal.created_at.desc()).all()
    completed = Goal.query.filter(Goal.status.in_(['已完成', '放棄'])).order_by(Goal.created_at.desc()).all()
    return render_template('goals/index.html',
        active_goals=active,
        completed_goals=completed,
        categories=CATEGORIES
    )


@goals_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        goal = Goal(
            title=request.form['title'],
            description=request.form.get('description', ''),
            category=request.form['category'],
            timeframe=request.form['timeframe'],
            target_date=date.fromisoformat(request.form['target_date']) if request.form.get('target_date') else None,
            status=request.form.get('status', '進行中'),
            progress=int(request.form.get('progress', 0)),
            user_id=current_user.id
        )
        db.session.add(goal)
        db.session.commit()
        flash('目標已新增！', 'success')
        return redirect(url_for('goals.index'))
    return render_template('goals/form.html',
        goal=None,
        categories=CATEGORIES,
        timeframes=TIMEFRAMES,
        statuses=STATUSES,
        action='新增'
    )


@goals_bp.route('/detail/<int:id>')
@login_required
def detail(id):
    goal = Goal.query.get_or_404(id)
    pending = [m for m in goal.milestones if not m.is_completed]
    done = [m for m in goal.milestones if m.is_completed]
    return render_template('goals/detail.html',
        goal=goal,
        pending_milestones=pending,
        done_milestones=done
    )


@goals_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    goal = Goal.query.get_or_404(id)
    if request.method == 'POST':
        goal.title = request.form['title']
        goal.description = request.form.get('description', '')
        goal.category = request.form['category']
        goal.timeframe = request.form['timeframe']
        goal.target_date = date.fromisoformat(request.form['target_date']) if request.form.get('target_date') else None
        goal.status = request.form.get('status', '進行中')
        goal.progress = int(request.form.get('progress', 0))
        db.session.commit()
        flash('目標已更新！', 'success')
        return redirect(url_for('goals.detail', id=goal.id))
    return render_template('goals/form.html',
        goal=goal,
        categories=CATEGORIES,
        timeframes=TIMEFRAMES,
        statuses=STATUSES,
        action='編輯'
    )


@goals_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    goal = Goal.query.get_or_404(id)
    db.session.delete(goal)
    db.session.commit()
    flash('目標已刪除。', 'success')
    return redirect(url_for('goals.index'))


@goals_bp.route('/milestone/add/<int:goal_id>', methods=['POST'])
@login_required
def milestone_add(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    milestone = GoalMilestone(
        goal_id=goal.id,
        title=request.form['title'],
        due_date=date.fromisoformat(request.form['due_date']) if request.form.get('due_date') else None,
        notes=request.form.get('notes', '')
    )
    db.session.add(milestone)
    db.session.commit()
    flash('里程碑已新增！', 'success')
    return redirect(url_for('goals.detail', id=goal_id))


@goals_bp.route('/milestone/complete/<int:milestone_id>', methods=['POST'])
@login_required
def milestone_complete(milestone_id):
    milestone = GoalMilestone.query.get_or_404(milestone_id)
    milestone.is_completed = True
    milestone.completed_date = date.today()
    db.session.commit()
    flash('里程碑已完成！', 'success')
    return redirect(url_for('goals.detail', id=milestone.goal_id))


@goals_bp.route('/milestone/delete/<int:milestone_id>', methods=['POST'])
@login_required
def milestone_delete(milestone_id):
    milestone = GoalMilestone.query.get_or_404(milestone_id)
    goal_id = milestone.goal_id
    db.session.delete(milestone)
    db.session.commit()
    flash('里程碑已刪除。', 'success')
    return redirect(url_for('goals.detail', id=goal_id))
