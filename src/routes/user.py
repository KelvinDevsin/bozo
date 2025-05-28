from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from src.models.user import User, db
import os

user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Verificar se os dados necessários foram fornecidos
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Verificar se o utilizador ou email já existem
    existing_user = User.query.filter_by(username=data['username']).first()
    existing_email = User.query.filter_by(email=data['email']).first()
    
    if existing_user:
        return jsonify({'success': False, 'message': 'Nome de utilizador já existe'}), 400
    
    if existing_email:
        return jsonify({'success': False, 'message': 'Email já registado'}), 400
    
    # Criar novo utilizador
    new_user = User(username=data['username'], email=data['email'])
    new_user.set_password(data['password'])
    
    # Adicionar à base de dados
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Registo concluído com sucesso'}), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Verificar se os dados necessários foram fornecidos
    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Verificar credenciais
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'success': False, 'message': 'Credenciais inválidas'}), 401
    
    # Guardar na sessão
    session['user_id'] = user.id
    session['username'] = user.username
    
    return jsonify({'success': True, 'message': 'Login efetuado com sucesso'}), 200

@user_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Sessão terminada com sucesso'}), 200

@user_bp.route('/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True, 
            'username': session.get('username')
        }), 200
    return jsonify({'authenticated': False}), 200
