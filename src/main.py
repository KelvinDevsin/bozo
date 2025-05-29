import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, session, redirect, url_for
from src.models.user import db, User
from src.routes.user import user_bp
from src.routes.account import account_bp
from src.routes.admin import admin_bp
import secrets

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = secrets.token_hex(16)

app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(account_bp, url_prefix='/api/account')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# Ativar a base de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'Kelvin2002!?')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()
    
    # Verificar se existe pelo menos um utilizador (para admin)
    if User.query.count() == 0:
        admin = User(username="admin", email="admin@example.com")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

@app.route('/admin', defaults={'path': ''})
@app.route('/admin/<path:path>')
def admin(path):
    # Redirecionar para a página de admin
    return send_from_directory(app.static_folder, 'admin.html')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
