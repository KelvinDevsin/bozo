from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file
from src.models.user import User
from src.models.account import InstagramAccount
from src.models.user import db
import os
import tempfile

account_bp = Blueprint('account', __name__)

@account_bp.route('/api/accounts/available', methods=['GET'])
def get_available_accounts():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
    
    # Obter contas disponíveis (não vendidas)
    accounts = InstagramAccount.query.filter_by(is_sold=False).all()
    
    # Contar quantas contas estão disponíveis
    available_count = len(accounts)
    
    # Calcular preço (fixo para todas as contas)
    price = 10.00  # Preço fixo para todas as contas
    
    return jsonify({
        'success': True,
        'available_count': available_count,
        'price': price,
        'name': 'Contas Instagram',
        'description': 'Contas Instagram prontas para uso'
    })

@account_bp.route('/api/accounts/purchase', methods=['POST'])
def purchase_accounts():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
    
    data = request.json
    quantity = data.get('quantity', 0)
    
    if quantity <= 0:
        return jsonify({'success': False, 'message': 'Quantidade inválida'}), 400
    
    # Verificar se há contas suficientes disponíveis
    available_accounts = InstagramAccount.query.filter_by(is_sold=False).limit(quantity).all()
    
    if len(available_accounts) < quantity:
        return jsonify({'success': False, 'message': f'Apenas {len(available_accounts)} contas disponíveis'}), 400
    
    # Marcar contas como vendidas
    purchased_accounts = []
    for account in available_accounts:
        account.is_sold = True
        purchased_accounts.append({
            'username': account.username,
            'password': account.password,
            'two_factor': account.two_factor
        })
    
    db.session.commit()
    
    # Criar arquivo temporário com as contas compradas
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt')
    temp_file_path = temp_file.name
    
    for account in purchased_accounts:
        temp_file.write(f"Usuário: {account['username']}\n")
        temp_file.write(f"Senha: {account['password']}\n")
        if account['two_factor']:
            temp_file.write(f"Código 2FA: {account['two_factor']}\n")
        temp_file.write("\n")
    
    temp_file.close()
    
    return jsonify({
        'success': True,
        'message': f'{quantity} contas compradas com sucesso',
        'accounts_file': os.path.basename(temp_file_path),
        'accounts': purchased_accounts
    })

@account_bp.route('/api/accounts/download/<filename>', methods=['GET'])
def download_accounts(filename):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
    
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Arquivo não encontrado'}), 404
    
    return send_file(file_path, as_attachment=True, download_name='contas_instagram.txt')
