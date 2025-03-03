import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
import json
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave_secreta_padrao')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///pizzaria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Importar db e inicializar
from database import db
db.init_app(app)

# Importar models
from models import User, Product, Category, Customer, Order, OrderItem

# Configurar o login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Definindo inicialização da base de dados
with app.app_context():
    db.create_all()
    # Criar um usuário admin se não existir
    if not User.query.filter_by(email='admin@pizzaria.com').first():
        admin = User(
            name='Administrador',
            email='admin@pizzaria.com',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

# Importar rotas
from routes.admin import admin_bp
from routes.whatsapp import whatsapp_bp

# Registrar blueprints
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(whatsapp_bp, url_prefix='/whatsapp')

@app.route('/')
def index():
    return redirect(url_for('admin_bp.dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_bp.dashboard'))
        
        flash('Credenciais inválidas. Tente novamente.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5002)
