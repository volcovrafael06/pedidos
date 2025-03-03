import os
from app import app, db
from models import User, Category, Product, Customer
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    """Initialize the database with sample data."""
    with app.app_context():
        # Create tables
        db.create_all()
        
        print("Criando usuário admin...")
        # Criar usuário admin se não existir
        if not User.query.filter_by(email='admin@pizzaria.com').first():
            admin = User(
                name='Administrador',
                email='admin@pizzaria.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            
            # Criar um usuário funcionário
            staff = User(
                name='Funcionário',
                email='staff@pizzaria.com',
                password=generate_password_hash('staff123'),
                role='staff'
            )
            db.session.add(staff)
            db.session.commit()
        
        print("Criando categorias e produtos...")
        # Criar categorias e produtos se não existirem
        if not Category.query.first():
            # Categoria: Pizzas Tradicionais
            cat_tradicional = Category(name='Pizzas Tradicionais', description='Pizzas com sabores tradicionais e clássicos')
            db.session.add(cat_tradicional)
            db.session.commit()
            
            produtos_tradicionais = [
                {'name': 'Pizza de Calabresa', 'description': 'Calabresa fatiada, cebola e mussarela', 'price': 38.90},
                {'name': 'Pizza de Mussarela', 'description': 'Mussarela, tomate e orégano', 'price': 36.90},
                {'name': 'Pizza de Portuguesa', 'description': 'Presunto, mussarela, ovo, cebola e ervilha', 'price': 42.90},
                {'name': 'Pizza de Frango com Catupiry', 'description': 'Frango desfiado e catupiry', 'price': 40.90},
                {'name': 'Pizza de Bacon', 'description': 'Bacon, mussarela e cebola', 'price': 41.90}
            ]
            
            for p in produtos_tradicionais:
                produto = Product(
                    name=p['name'],
                    description=p['description'],
                    price=p['price'],
                    category_id=cat_tradicional.id,
                    available=True
                )
                db.session.add(produto)
            
            # Categoria: Pizzas Especiais
            cat_especial = Category(name='Pizzas Especiais', description='Pizzas com ingredientes especiais e combinações exclusivas')
            db.session.add(cat_especial)
            db.session.commit()
            
            produtos_especiais = [
                {'name': 'Pizza Quatro Queijos', 'description': 'Mussarela, provolone, parmesão e gorgonzola', 'price': 46.90},
                {'name': 'Pizza Vegetariana', 'description': 'Brócolis, champignon, palmito, cebola e mussarela', 'price': 44.90},
                {'name': 'Pizza Margherita', 'description': 'Mussarela, tomate e manjericão', 'price': 42.90},
                {'name': 'Pizza Pepperoni', 'description': 'Pepperoni e mussarela', 'price': 48.90},
                {'name': 'Pizza Suprema', 'description': 'Calabresa, presunto, champignon, pimentão, cebola e mussarela', 'price': 52.90}
            ]
            
            for p in produtos_especiais:
                produto = Product(
                    name=p['name'],
                    description=p['description'],
                    price=p['price'],
                    category_id=cat_especial.id,
                    available=True
                )
                db.session.add(produto)
            
            # Categoria: Bebidas
            cat_bebidas = Category(name='Bebidas', description='Refrigerantes, sucos e outras bebidas')
            db.session.add(cat_bebidas)
            db.session.commit()
            
            bebidas = [
                {'name': 'Refrigerante Lata', 'description': 'Coca-Cola, Guaraná Antarctica, Fanta (350ml)', 'price': 5.90},
                {'name': 'Refrigerante 2L', 'description': 'Coca-Cola, Guaraná Antarctica, Fanta', 'price': 12.90},
                {'name': 'Suco Natural', 'description': 'Laranja, Limão ou Abacaxi (500ml)', 'price': 8.90},
                {'name': 'Água Mineral', 'description': 'Com ou sem gás (500ml)', 'price': 3.90},
                {'name': 'Cerveja Lata', 'description': 'Brahma, Skol, Antarctica (350ml)', 'price': 6.90}
            ]
            
            for b in bebidas:
                bebida = Product(
                    name=b['name'],
                    description=b['description'],
                    price=b['price'],
                    category_id=cat_bebidas.id,
                    available=True
                )
                db.session.add(bebida)
                
            # Categoria: Sobremesas
            cat_sobremesas = Category(name='Sobremesas', description='Doces e sobremesas')
            db.session.add(cat_sobremesas)
            db.session.commit()
            
            sobremesas = [
                {'name': 'Pizza de Chocolate', 'description': 'Chocolate ao leite com granulado', 'price': 38.90},
                {'name': 'Pizza de Banana', 'description': 'Banana, canela e leite condensado', 'price': 38.90},
                {'name': 'Petit Gateau', 'description': 'Com sorvete de creme', 'price': 16.90},
                {'name': 'Pudim de Leite', 'description': 'Pudim tradicional de leite condensado', 'price': 12.90}
            ]
            
            for s in sobremesas:
                sobremesa = Product(
                    name=s['name'],
                    description=s['description'],
                    price=s['price'],
                    category_id=cat_sobremesas.id,
                    available=True
                )
                db.session.add(sobremesa)
            
            db.session.commit()
        
        print("Criando cliente de exemplo...")
        # Criar cliente de exemplo
        if not Customer.query.first():
            cliente = Customer(
                phone='+5511999999999',
                name='Cliente Exemplo',
                address='Rua Exemplo, 123 - Bairro - São Paulo/SP',
                last_interaction=datetime.utcnow()
            )
            db.session.add(cliente)
            db.session.commit()
        
        print("Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_db()
