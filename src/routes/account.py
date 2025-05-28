from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from src.models.user import User, db
from src.models.account import InstagramAccount
import os
import io
import random
import string

account_bp = Blueprint('account', __name__)

# Verificar se o utilizador está autenticado
def is_authenticated():
    return 'user_id' in session

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
            'price': account.price
        })
    
    return jsonify({'success': True, 'accounts': accounts_data}), 200

@account_bp.route('/purchase/<int:account_id>', methods=['GET'])
def purchase_account(account_id):
    # Verificar se o utilizador está autenticado
    if not is_authenticated():
        return jsonify({'success': False, 'message': 'Utilizador não autenticado'}), 401
    
    # Verificar se a conta existe
    account = InstagramAccount.query.get(account_id)
    if not account:
        return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
    
    # Verificar se a conta já foi vendida
    if account.is_sold:
        return jsonify({'success': False, 'message': 'Esta conta já foi vendida'}), 400
    
    # Marcar a conta como vendida
    account.is_sold = True
    db.session.commit()
    
    # Criar conteúdo do ficheiro TXT
    account_info = f"Detalhes da Conta Instagram\n"
    account_info += f"------------------------\n"
    account_info += f"Utilizador: {account.username}\n"
    account_info += f"Senha: {account.password}\n"
    account_info += f"Código 2FA: {account.two_factor}\n"
    
    # Criar ficheiro para download
    buffer = io.BytesIO()
    buffer.write(account_info.encode('utf-8'))
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"conta_instagram_{account.username}.txt",
        mimetype="text/plain"
    )
