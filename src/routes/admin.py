from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from src.models.user import User, db
from src.models.account import InstagramAccount, AccountType
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
    
    # Verificar se é o administrador específico (Kannenberg)
    return user.username == 'kelvin'

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    
    # Verificar se os dados necessários foram fornecidos
    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Verificar credenciais específicas do administrador
    if data['username'] != 'kelvin' or data['password'] != 'kkkjjjkkk':
        return jsonify({'success': False, 'message': 'Credenciais inválidas'}), 401
    
    # Verificar se o usuário admin existe, se não, criar
    admin_user = User.query.filter_by(username='kelvin').first()
    if not admin_user:
        admin_user = User(username='kelvin', email='admin1@example.com')
        admin_user.set_password('kkkjjjkkk')
        db.session.add(admin_user)
        db.session.commit()
    
    # Guardar na sessão
    session['user_id'] = admin_user.id
    session['username'] = admin_user.username
    session['is_admin'] = True
    
    return jsonify({'success': True, 'message': 'Login administrativo efetuado com sucesso'}), 200

@admin_bp.route('/dashboard', methods=['GET'])
def admin_dashboard():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    # Obter estatísticas
    empty_account_types = AccountType.query.filter_by(is_empty=True).all()
    built_account_types = AccountType.query.filter_by(is_empty=False).all()
    
    total_accounts = InstagramAccount.query.count()
    sold_accounts = InstagramAccount.query.filter_by(is_sold=True).count()
    available_accounts = total_accounts - sold_accounts
    
    stats = {
        'total_accounts': total_accounts,
        'sold_accounts': sold_accounts,
        'available_accounts': available_accounts,
        'empty_account_types': len(empty_account_types),
        'built_account_types': len(built_account_types)
    }
    
    return jsonify({
        'success': True, 
        'stats': stats,
        'empty_account_types': [t.to_dict() for t in empty_account_types],
        'built_account_types': [t.to_dict() for t in built_account_types]
    }), 200

@admin_bp.route('/account-types', methods=['GET'])
def list_account_types():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    account_types = AccountType.query.all()
    
    return jsonify({
        'success': True,
        'account_types': [t.to_dict() for t in account_types]
    }), 200

@admin_bp.route('/account-types', methods=['POST'])
def add_account_type():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    data = request.get_json()
    
    # Verificar se os dados necessários foram fornecidos
    if not data or not all(k in data for k in ('name', 'price', 'is_empty')):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    # Criar novo tipo de conta
    new_type = AccountType(
        name=data['name'],
        description=data.get('description', ''),
        price=float(data['price']),
        is_empty=bool(data['is_empty']),
        available_quantity=0
    )
    
    db.session.add(new_type)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Tipo de conta adicionado com sucesso',
        'account_type': new_type.to_dict()
    }), 201

@admin_bp.route('/account-types/<int:type_id>', methods=['PUT'])
def update_account_type(type_id):
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    account_type = AccountType.query.get(type_id)
    if not account_type:
        return jsonify({'success': False, 'message': 'Tipo de conta não encontrado'}), 404
    
    data = request.get_json()
    
    # Atualizar campos
    if 'name' in data:
        account_type.name = data['name']
    if 'description' in data:
        account_type.description = data['description']
    if 'price' in data:
        account_type.price = float(data['price'])
    if 'is_empty' in data:
        account_type.is_empty = bool(data['is_empty'])
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Tipo de conta atualizado com sucesso',
        'account_type': account_type.to_dict()
    }), 200

@admin_bp.route('/account-types/<int:type_id>', methods=['DELETE'])
def delete_account_type(type_id):
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    account_type = AccountType.query.get(type_id)
    if not account_type:
        return jsonify({'success': False, 'message': 'Tipo de conta não encontrado'}), 404
    
    # Verificar se há contas associadas a este tipo
    associated_accounts = InstagramAccount.query.filter_by(account_type_id=type_id).count()
    if associated_accounts > 0:
        return jsonify({
            'success': False, 
            'message': f'Não é possível excluir: existem {associated_accounts} contas associadas a este tipo'
        }), 400
    
    db.session.delete(account_type)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Tipo de conta removido com sucesso'
    }), 200

@admin_bp.route('/accounts/bulk-add', methods=['POST'])
def bulk_add_accounts():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    data = request.get_json()
    
    # Verificar se os dados necessários foram fornecidos
    if not data or not all(k in data for k in ('account_type_id', 'accounts_text')):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    account_type_id = data['account_type_id']
    accounts_text = data['accounts_text']
    
    # Verificar se o tipo de conta existe
    account_type = AccountType.query.get(account_type_id)
    if not account_type:
        return jsonify({'success': False, 'message': 'Tipo de conta não encontrado'}), 404
    
    # Processar o texto de contas (formato usuário/senha)
    lines = accounts_text.strip().split('\n')
    
    # Verificar se o número de linhas é par (usuário/senha)
    if len(lines) % 2 != 0:
        return jsonify({
            'success': False, 
            'message': 'Formato inválido: o número de linhas deve ser par (usuário/senha)'
        }), 400
    
    # Processar pares de usuário/senha
    added_count = 0
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            username = lines[i].strip()
            password = lines[i + 1].strip()
            
            # Verificar se a conta já existe
            existing_account = InstagramAccount.query.filter_by(username=username).first()
            if existing_account:
                continue
            
            # Criar nova conta
            new_account = InstagramAccount(
                username=username,
                password=password,
                account_type_id=account_type_id,
                is_sold=False
            )
            
            db.session.add(new_account)
            added_count += 1
    
    # Atualizar quantidade disponível
    account_type.available_quantity += added_count
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Adicionadas {added_count} contas com sucesso',
        'added_count': added_count,
        'new_available_quantity': account_type.available_quantity
    }), 201

@admin_bp.route('/accounts', methods=['GET'])
def list_accounts():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    # Filtros opcionais
    account_type_id = request.args.get('account_type_id', type=int)
    is_sold = request.args.get('is_sold', type=lambda v: v.lower() == 'true' if v else None)
    
    # Construir query base
    query = InstagramAccount.query
    
    # Aplicar filtros se fornecidos
    if account_type_id is not None:
        query = query.filter_by(account_type_id=account_type_id)
    if is_sold is not None:
        query = query.filter_by(is_sold=is_sold)
    
    # Executar query
    accounts = query.all()
    accounts_data = [account.to_dict() for account in accounts]
    
    return jsonify({
        'success': True,
        'accounts': accounts_data,
        'count': len(accounts_data)
    }), 200

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
    if 'account_type_id' in data:
        # Se estiver mudando o tipo de conta, atualizar contadores
        if account.account_type_id != data['account_type_id']:
            # Decrementar contador do tipo antigo se existir
            if account.account_type_id:
                old_type = AccountType.query.get(account.account_type_id)
                if old_type and not account.is_sold:
                    old_type.available_quantity = max(0, old_type.available_quantity - 1)
            
            # Incrementar contador do novo tipo
            new_type = AccountType.query.get(data['account_type_id'])
            if new_type and not account.is_sold:
                new_type.available_quantity += 1
            
            account.account_type_id = data['account_type_id']
    
    if 'is_sold' in data:
        # Se estiver alterando o status de venda, atualizar contador
        if account.is_sold != data['is_sold']:
            if account.account_type_id:
                account_type = AccountType.query.get(account.account_type_id)
                if account_type:
                    if data['is_sold']:  # Marcando como vendida
                        account_type.available_quantity = max(0, account_type.available_quantity - 1)
                    else:  # Marcando como disponível
                        account_type.available_quantity += 1
        
        account.is_sold = data['is_sold']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Conta atualizada com sucesso',
        'account': account.to_dict()
    }), 200

@admin_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    account = InstagramAccount.query.get(account_id)
    if not account:
        return jsonify({'success': False, 'message': 'Conta não encontrada'}), 404
    
    # Atualizar contador se a conta não estiver vendida
    if not account.is_sold and account.account_type_id:
        account_type = AccountType.query.get(account.account_type_id)
        if account_type:
            account_type.available_quantity = max(0, account_type.available_quantity - 1)
    
    db.session.delete(account)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Conta removida com sucesso'
    }), 200
