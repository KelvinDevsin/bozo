from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from src.models.user import User, db
from src.models.account import InstagramAccount
import os
import io
import random
import string

admin_bp = Blueprint('admin', __name__)

# Verificar se o utilizador é administrador
def is_admin():
    if 'user_id' not in session:
        return False
    
    user = User.query.get(session['user_id'])
    if not user:
        return False
    
    # Por simplicidade, consideramos o primeiro utilizador como administrador
    # Em produção, seria necessário um campo específico na tabela de utilizadores
    return user.id == 1

@admin_bp.route('/', methods=['GET'])
def admin_panel():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    return jsonify({'success': True, 'message': 'Painel administrativo'}), 200

@admin_bp.route('/accounts', methods=['GET'])
def list_accounts():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    accounts = InstagramAccount.query.all()
    accounts_data = [account.to_dict() for account in accounts]
    
    return jsonify({'success': True, 'accounts': accounts_data}), 200

@admin_bp.route('/accounts/add', methods=['POST'])
def add_account():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    data = request.get_json()
    
    # Verificar se os dados necessários foram fornecidos
    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Verificar se a conta já existe
    existing_account = InstagramAccount.query.filter_by(username=data['username']).first()
    if existing_account:
        return jsonify({'success': False, 'message': 'Conta já existe'}), 400
    
    # Criar nova conta
    new_account = InstagramAccount(
        username=data['username'],
        password=data['password'],
        two_factor=data.get('two_factor', ''),
        price=data.get('price', 0.10)
    )
    
    # Adicionar à base de dados
    db.session.add(new_account)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Conta adicionada com sucesso', 'account': new_account.to_dict()}), 201

@admin_bp.route('/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    account = InstagramAccount.query.get(account_id)
    if not account:
        return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
    
    data = request.get_json()
    
    # Atualizar campos
    if 'username' in data:
        account.username = data['username']
    if 'password' in data:
        account.password = data['password']
    if 'two_factor' in data:
        account.two_factor = data['two_factor']
    if 'price' in data:
        account.price = data['price']
    if 'is_sold' in data:
        account.is_sold = data['is_sold']
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Conta atualizada com sucesso', 'account': account.to_dict()}), 200

@admin_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    account = InstagramAccount.query.get(account_id)
    if not account:
        return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
    
    db.session.delete(account)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Conta removida com sucesso'}), 200

@admin_bp.route('/users', methods=['GET'])
def list_users():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    users = User.query.all()
    users_data = []
    
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({'success': True, 'users': users_data}), 200

@admin_bp.route('/generate-accounts', methods=['POST'])
def generate_accounts():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    data = request.get_json()
    count = data.get('count', 10)
    
    # Limitar o número de contas geradas
    if count > 100:
        count = 100
    
    # Gerar contas aleatórias
    for i in range(count):
        username = f"instagram_user_{random.randint(1000, 9999)}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        two_factor = ''.join(random.choices(string.digits, k=6))
        
        # Verificar se a conta já existe
        existing_account = InstagramAccount.query.filter_by(username=username).first()
        if existing_account:
            continue
        
        # Criar nova conta
        new_account = InstagramAccount(
            username=username,
            password=password,
            two_factor=two_factor,
            price=0.10
        )
        
        # Adicionar à base de dados
        db.session.add(new_account)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Geradas {count} contas com sucesso'}), 201
