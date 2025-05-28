from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from src.models.user import User, db
from src.models.account import InstagramAccount, AccountType
import os
import io
import random
import string

account_bp = Blueprint('account', __name__)

# Verificar se o utilizador está autenticado
def is_authenticated():
    return 'user_id' in session

@account_bp.route('/dashboard', methods=['GET'])
def dashboard():
    # Verificar se o utilizador está autenticado
    if not is_authenticated():
        return jsonify({'success': False, 'message': 'Utilizador não autenticado'}), 401
    
    # Obter tipos de contas vazias e montadas
    empty_accounts = AccountType.query.filter_by(is_empty=True).all()
    built_accounts = AccountType.query.filter_by(is_empty=False).all()
    
    empty_accounts_data = [account_type.to_dict() for account_type in empty_accounts]
    built_accounts_data = [account_type.to_dict() for account_type in built_accounts]
    
    return jsonify({
        'success': True, 
        'empty_accounts': empty_accounts_data,
        'built_accounts': built_accounts_data
    }), 200

@account_bp.route('/type/<int:type_id>', methods=['GET'])
def get_account_type(type_id):
    # Verificar se o utilizador está autenticado
    if not is_authenticated():
        return jsonify({'success': False, 'message': 'Utilizador não autenticado'}), 401
    
    # Obter o tipo de conta
    account_type = AccountType.query.get(type_id)
    if not account_type:
        return jsonify({'success': False, 'message': 'Tipo de conta não encontrado'}), 404
    
    return jsonify({
        'success': True,
        'account_type': account_type.to_dict()
    }), 200

@account_bp.route('/purchase', methods=['POST'])
def purchase_accounts():
    # Verificar se o utilizador está autenticado
    if not is_authenticated():
        return jsonify({'success': False, 'message': 'Utilizador não autenticado'}), 401
    
    data = request.get_json()
    
    # Verificar se os dados necessários foram fornecidos
    if not data or not all(k in data for k in ('account_type_id', 'quantity')):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    account_type_id = data['account_type_id']
    quantity = int(data['quantity'])
    
    # Verificar se o tipo de conta existe
    account_type = AccountType.query.get(account_type_id)
    if not account_type:
        return jsonify({'success': False, 'message': 'Tipo de conta não encontrado'}), 404
    
    # Verificar se há contas suficientes disponíveis
    if account_type.available_quantity < quantity:
        return jsonify({'success': False, 'message': 'Quantidade insuficiente de contas disponíveis'}), 400
    
    # Obter contas disponíveis deste tipo
    available_accounts = InstagramAccount.query.filter_by(
        account_type_id=account_type_id, 
        is_sold=False
    ).limit(quantity).all()
    
    if len(available_accounts) < quantity:
        return jsonify({'success': False, 'message': 'Quantidade insuficiente de contas disponíveis'}), 400
    
    # Marcar contas como vendidas
    accounts_info = []
    for account in available_accounts:
        account.is_sold = True
        accounts_info.append({
            'username': account.username,
            'password': account.password,
            'two_factor': account.two_factor
        })
    
    # Atualizar quantidade disponível
    account_type.available_quantity -= quantity
    db.session.commit()
    
    # Criar conteúdo do ficheiro TXT
    account_info_text = f"Detalhes das Contas {account_type.name}\n"
    account_info_text += f"------------------------\n\n"
    
    for i, account in enumerate(accounts_info, 1):
        account_info_text += f"Conta {i}:\n"
        account_info_text += f"Utilizador: {account['username']}\n"
        account_info_text += f"Senha: {account['password']}\n"
        if account['two_factor']:
            account_info_text += f"Código 2FA: {account['two_factor']}\n"
        account_info_text += f"\n"
    
    # Criar ficheiro para download
    buffer = io.BytesIO()
    buffer.write(account_info_text.encode('utf-8'))
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"contas_{account_type.name.lower().replace(' ', '_')}_{quantity}.txt",
        mimetype="text/plain"
    )

@account_bp.route('/list', methods=['GET'])
def list_accounts():
    # Verificar se o utilizador está autenticado
    if not is_authenticated():
        return jsonify({'success': False, 'message': 'Utilizador não autenticado'}), 401
    
    # Retornar lista de contas disponíveis
    accounts = InstagramAccount.query.filter_by(is_sold=False).all()
    accounts_data = []
    
    for account in accounts:
        accounts_data.append({
            'id': account.id,
            'username': account.username,
            'price': account.account_type.price if account.account_type else 0.0
        })
    
    return jsonify({'success': True, 'accounts': accounts_data}), 200
