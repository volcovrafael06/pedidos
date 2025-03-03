from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='staff')  # admin, staff
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    available = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_state = db.Column(db.String(50), default='initial')  # initial, menu, ordering, payment, etc.
    current_order_id = db.Column(db.Integer, nullable=True)  # ID do pedido atual em andamento
    temp_data = db.Column(db.Text, nullable=True)  # Dados temporários para a conversa
    human_support = db.Column(db.Boolean, default=False)  # Se está em modo de atendimento humano
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Atendente responsável
    orders = db.relationship('Order', backref='customer', lazy=True)
    assigned_user = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_customers', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    status = db.Column(db.String(20), default='novo')  # novo, em_preparo, pronto, em_entrega, entregue, cancelado
    total = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(50), nullable=True)  # dinheiro, cartao, pix
    payment_status = db.Column(db.String(20), default='pendente')  # pendente, pago
    address = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)  # Preço no momento da compra
    notes = db.Column(db.Text, nullable=True)  # Observações específicas para este item

class WhatsAppMessage(db.Model):
    """
    Modelo para mensagens de WhatsApp enviadas e recebidas.
    
    Attributes:
        id (int): ID único da mensagem.
        customer_id (int): ID do cliente associado à mensagem.
        message (str): Conteúdo da mensagem.
        direction (str): Direção da mensagem ('inbound' para recebida, 'outbound' para enviada).
        timestamp (datetime): Data e hora da mensagem.
        is_human (bool): Indica se a mensagem foi enviada por um atendente humano ou pelo bot.
    """
    __tablename__ = 'whats_app_message'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    direction = db.Column(db.String(10), nullable=False)  # 'inbound' ou 'outbound'
    timestamp = db.Column(db.DateTime, default=datetime.now)
    is_human = db.Column(db.Boolean, default=False)
    
    customer = db.relationship('Customer', backref=db.backref('messages', lazy=True))
