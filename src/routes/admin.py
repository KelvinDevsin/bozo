from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from src.models.user import User
from src.models.account import InstagramAccount
from src.models.user import db
import os

admin_bp = Blueprint('admin', __name__)

# Verificar se o usuário é administrador
def is_admin():
    if 'user_id' not in session:
        return False
    
    user = User.query.get(session['user_id'])
    return user and user.username == 'Kannenberg'

@admin_bp.route('/admin')
def admin_panel():
    if not is_admin():
        return redirect(url_for('user.login'))
    
    return send_from_directory('static', 'admin.html')

@admin_bp.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    # Contar estatísticas
    total_accounts = InstagramAccount.query.count()
    sold_accounts = InstagramAccount.query.filter_by(is_sold=True).count()
    available_accounts = total_accounts - sold_accounts
    
    return jsonify({
        'success': True,
        'stats': {
            'total_accounts': total_accounts,
            'sold_accounts': sold_accounts,
            'available_accounts': available_accounts
        }
    })

@admin_bp.route('/api/admin/accounts', methods=['GET'])
def get_admin_accounts():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    # Filtrar por status de venda, se fornecido
    is_sold = request.args.get('is_sold')
    if is_sold is not None:
        is_sold = is_sold.lower() == 'true'
        accounts = InstagramAccount.query.filter_by(is_sold=is_sold).all()
    else:
        accounts = InstagramAccount.query.all()
    
    return jsonify({
        'success': True,
        'accounts': [account.to_dict() for account in accounts]
    })

@admin_bp.route('/api/admin/accounts/add', methods=['POST'])
def add_account():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    two_factor = data.get('two_factor')
    is_sold = data.get('is_sold', False)
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'}), 400
    
    account = InstagramAccount(
        username=username,
        password=password,
        two_factor=two_factor,
        is_sold=is_sold
    )
    
    db.session.add(account)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Conta adicionada com sucesso',
        'account': account.to_dict()
    })

@admin_bp.route('/api/admin/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    account = InstagramAccount.query.get(account_id)
    if not account:
        return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
    
    data = request.json
    if 'username' in data:
        account.username = data['username']
    if 'password' in data:
        account.password = data['password']
    if 'two_factor' in data:
        account.two_factor = data['two_factor']
    if 'is_sold' in data:
        account.is_sold = data['is_sold']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Conta atualizada com sucesso',
        'account': account.to_dict()
    })

@admin_bp.route('/api/admin/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    account = InstagramAccount.query.get(account_id)
    if not account:
        return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
    
    db.session.delete(account)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Conta removida com sucesso'
    })

@admin_bp.route('/api/admin/accounts/bulk-add', methods=['POST'])
def bulk_add_accounts():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    data = request.json
    accounts_text = data.get('accounts_text', '')
    
    if not accounts_text:
        return jsonify({'success': False, 'message': 'Texto de contas vazio'}), 400
    
    lines = accounts_text.strip().split('\n')
    if len(lines) % 2 != 0:
        return jsonify({'success': False, 'message': 'Formato inválido. Deve haver um par usuário/senha por linha'}), 400
    
    added_count = 0
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            username = lines[i].strip()
            password = lines[i + 1].strip()
            
            if username and password:
                account = InstagramAccount(
                    username=username,
                    password=password,
                    is_sold=False
                )
                db.session.add(account)
                added_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{added_count} contas adicionadas com sucesso',
        'added_count': added_count
    })
