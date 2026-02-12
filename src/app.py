# app.py
# Bookshelf
# Copyright (C) 2025  TheCosmicAspect

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from flask import Flask
from models import db, User, create_tables
from config import Config
from flask_login import LoginManager, UserMixin, login_required, current_user

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Init flask_login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Log in to access this page.'

# User loader
@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)

@app.context_processor
def inject_current_user():
    return dict(current_user=current_user)


# Register blueprints
from routes.main import main_bp
from routes.books import books_bp
from routes.authors import authors_bp
from routes.tags import tags_bp
from routes.locations import locations_bp
from routes.users import users_bp
from routes.api import api_bp
from routes.auth import auth_bp

app.register_blueprint(main_bp)
app.register_blueprint(books_bp, url_prefix='/books')
app.register_blueprint(authors_bp, url_prefix='/authors')
app.register_blueprint(tags_bp, url_prefix='/tags')
app.register_blueprint(locations_bp, url_prefix='/locations')
app.register_blueprint(users_bp, url_prefix='/users')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp)


if __name__ == '__main__':
    app.run(debug=True)