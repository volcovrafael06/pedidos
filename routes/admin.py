from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import User, Product, Category, Customer, Order, OrderItem, WhatsAppMessage
from database import db
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import json

admin_bp = Blueprint('admin_bp', __name__)

# Dashboard
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Obter estatísticas para o dashboard
    total_orders = Order.query.count()
    orders_today = Order.query.filter(func.date(Order.created_at) == func.date(datetime.utcnow())).count()
    
    # Pedidos recentes
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Total de vendas hoje
    sales_today = db.session.query(func.sum(Order.total)).filter(
        func.date(Order.created_at) == func.date(datetime.utcnow())
    ).scalar() or 0
    
    # Total de clientes
    total_customers = Customer.query.count()
    
    return render_template('admin/dashboard.html', 
                           total_orders=total_orders,
                           orders_today=orders_today,
                           recent_orders=recent_orders,
                           sales_today=sales_today,
                           total_customers=total_customers)

# Orders
@admin_bp.route('/orders')
@login_required
def orders():
    # Filtrar por status se fornecido
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if status:
        orders = Order.query.filter_by(status=status).order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page)
    else:
        orders = Order.query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/orders.html', orders=orders, current_status=status)

@admin_bp.route('/orders/<int:id>')
@login_required
def view_order(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/<int:id>/status', methods=['POST'])
@login_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    status = request.form.get('status')
    
    if status in ['novo', 'em_preparo', 'pronto', 'em_entrega', 'entregue', 'cancelado']:
        order.status = status
        db.session.commit()
        
        # Enviar notificação ao cliente via WhatsApp, dependendo do status
        flash('Status do pedido atualizado com sucesso.', 'success')
    else:
        flash('Status inválido.', 'danger')
    
    return redirect(url_for('admin_bp.view_order', id=id))

# Products
@admin_bp.route('/products')
@login_required
def products():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories)

@admin_bp.route('/products/add', methods=['POST'])
@login_required
def add_product():
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    category_id = request.form.get('category_id')
    available = True if request.form.get('available') == 'on' else False
    
    if name and price and category_id:
        product = Product(
            name=name,
            description=description,
            price=float(price),
            category_id=int(category_id),
            available=available
        )
        db.session.add(product)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
    else:
        flash('Erro ao adicionar produto. Verifique os campos obrigatórios.', 'danger')
        
    return redirect(url_for('admin_bp.products'))

@admin_bp.route('/products/<int:id>/edit', methods=['POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    product.name = request.form.get('name')
    product.description = request.form.get('description')
    product.price = float(request.form.get('price'))
    product.category_id = int(request.form.get('category_id'))
    product.available = True if request.form.get('available') == 'on' else False
    
    db.session.commit()
    flash('Produto atualizado com sucesso!', 'success')
    return redirect(url_for('admin_bp.products'))

@admin_bp.route('/products/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('admin_bp.products'))

# Categories
@admin_bp.route('/categories')
@login_required
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    name = request.form.get('name')
    description = request.form.get('description')
    
    if name:
        category = Category(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        flash('Categoria adicionada com sucesso!', 'success')
    else:
        flash('O nome da categoria é obrigatório.', 'danger')
        
    return redirect(url_for('admin_bp.categories'))

@admin_bp.route('/categories/<int:id>/edit', methods=['POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    
    category.name = request.form.get('name')
    category.description = request.form.get('description')
    
    db.session.commit()
    flash('Categoria atualizada com sucesso!', 'success')
    return redirect(url_for('admin_bp.categories'))

@admin_bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    # Verificar se há produtos associados à categoria
    if category.products:
        flash('Não é possível excluir uma categoria que possui produtos associados.', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Categoria excluída com sucesso!', 'success')
        
    return redirect(url_for('admin_bp.categories'))

# Customers
@admin_bp.route('/customers')
@login_required
def customers():
    customers = Customer.query.all()
    return render_template('admin/customers.html', customers=customers)

@admin_bp.route('/customers/<int:id>')
@login_required
def view_customer(id):
    customer = Customer.query.get_or_404(id)
    orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.created_at.desc()).all()
    return render_template('admin/customer_detail.html', customer=customer, orders=orders)

@admin_bp.route('/customers/<int:id>/message', methods=['POST'])
@login_required
def send_customer_message(id):
    customer = Customer.query.get_or_404(id)
    message = request.form.get('message')
    
    if message:
        # Lógica para enviar mensagem via WhatsApp (será implementada com Twilio)
        # Aqui apenas registramos no banco de dados
        whatsapp_message = WhatsAppMessage(
            customer_id=customer.id,
            message=message,
            direction='outbound',
            timestamp=datetime.utcnow()
        )
        db.session.add(whatsapp_message)
        db.session.commit()
        
        flash('Mensagem enviada com sucesso!', 'success')
    else:
        flash('O conteúdo da mensagem é obrigatório.', 'danger')
        
    return redirect(url_for('admin_bp.view_customer', id=id))

# Users Management
@admin_bp.route('/users')
@login_required
def users():
    # Verificar se o usuário atual é admin
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem gerenciar usuários.', 'danger')
        return redirect(url_for('admin_bp.dashboard'))
        
    users = User.query.all()
    return render_template('admin/users.html', users=users, current_user=current_user)

@admin_bp.route('/users/add', methods=['POST'])
@login_required
def add_user():
    # Verificar se o usuário atual é admin
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem adicionar usuários.', 'danger')
        return redirect(url_for('admin_bp.dashboard'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    
    # Verificar se o email já está em uso
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Este email já está em uso por outro usuário.', 'danger')
        return redirect(url_for('admin_bp.users'))
    
    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role=role,
        created_at=datetime.utcnow()
    )
    db.session.add(user)
    db.session.commit()
    
    flash('Usuário adicionado com sucesso!', 'success')
    return redirect(url_for('admin_bp.users'))

@admin_bp.route('/users/<int:id>/edit', methods=['POST'])
@login_required
def edit_user(id):
    # Verificar se o usuário atual é admin
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem editar usuários.', 'danger')
        return redirect(url_for('admin_bp.dashboard'))
    
    user = User.query.get_or_404(id)
    
    user.name = request.form.get('name')
    
    # Verificar se o email está sendo alterado e se já está em uso
    new_email = request.form.get('email')
    if new_email != user.email:
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user:
            flash('Este email já está em uso por outro usuário.', 'danger')
            return redirect(url_for('admin_bp.users'))
        user.email = new_email
    
    # Atualizar senha apenas se fornecida
    password = request.form.get('password')
    if password:
        user.password = generate_password_hash(password)
    
    user.role = request.form.get('role')
    
    db.session.commit()
    flash('Usuário atualizado com sucesso!', 'success')
    return redirect(url_for('admin_bp.users'))

@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    # Verificar se o usuário atual é admin
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem excluir usuários.', 'danger')
        return redirect(url_for('admin_bp.dashboard'))
    
    # Não permitir que o usuário exclua a si mesmo
    if id == current_user.id:
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('admin_bp.users'))
    
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('admin_bp.users'))

# API para relatórios
@admin_bp.route('/api/sales-by-day')
@login_required
def sales_by_day():
    # Últimos 30 dias de vendas
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Consulta para obter vendas por dia
    sales_data = db.session.query(
        func.date(Order.created_at).label('date'),
        func.sum(Order.total).label('total')
    ).filter(
        Order.created_at.between(start_date, end_date)
    ).group_by(
        func.date(Order.created_at)
    ).order_by(
        func.date(Order.created_at)
    ).all()
    
    # Formatar resultados
    result = [
        {
            'date': date.strftime('%d/%m/%Y'),
            'total': float(total)
        }
        for date, total in sales_data
    ]
    
    return jsonify(result)

@admin_bp.route('/api/popular-products')
@login_required
def popular_products():
    # Consulta para obter produtos mais vendidos
    products_data = db.session.query(
        Product.id,
        Product.name,
        func.sum(OrderItem.quantity).label('count'),
        func.sum(OrderItem.price * OrderItem.quantity).label('revenue')
    ).join(
        OrderItem, OrderItem.product_id == Product.id
    ).group_by(
        Product.id
    ).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(10).all()
    
    # Formatar resultados
    result = [
        {
            'id': id,
            'name': name,
            'count': int(count),
            'revenue': float(revenue)
        }
        for id, name, count, revenue in products_data
    ]
    
    return jsonify(result)

# Reports
@admin_bp.route('/reports')
@login_required
def reports():
    return render_template('admin/reports.html')
