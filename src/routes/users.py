from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import datetime
from models import db
from models.models import User, UserRole
from forms.forms import UserForm

users_bp = Blueprint('users', __name__)

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Users main route - shows all users
@users_bp.route('/')
@login_required
@admin_required
def user_list():
    users = db.session.query(User).all()
    return render_template('user_list.html', users=users)

# User detail
@users_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def user_add():
    form = UserForm()

    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            join_date=datetime.utcnow(),
            permissions=UserRole.VIEWER.value
        )
        db.session.add(user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('users.user_list'))

    return render_template('user_form.html', form=form, title='Add User')

# Edit user
@users_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        user.name = form.name.data
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('users.user_list'))

    return render_template('user_form.html', form=form, title='Edit User')

# Delete user
@users_bp.route('/<int:id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def user_delete(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('users.user_list'))