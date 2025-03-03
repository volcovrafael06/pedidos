import os
from flask import Flask
from database import db
import sqlite3
from dotenv import load_dotenv
import os.path

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
# Forçar o caminho para usar a pasta instance (onde o banco de dados foi encontrado)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/pizzaria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def add_column(conn, table_name, column_name, column_type):
    """Adiciona uma coluna à tabela se ela não existir"""
    # Verificar se a coluna já existe
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
    columns = [info[1] for info in cursor.fetchall()]
    
    if column_name not in columns:
        print(f"Adicionando coluna {column_name} à tabela {table_name}")
        cursor.execute(f"ALTER TABLE \"{table_name}\" ADD COLUMN {column_name} {column_type}")
        return True
    else:
        print(f"Coluna {column_name} já existe na tabela {table_name}")
        return False

def migrate():
    """Executa as migrações necessárias"""
    # Usar diretamente o caminho para a pasta instance
    db_path = os.path.join(os.path.dirname(__file__), 'instance/pizzaria.db')
    
    print(f"Conectando ao banco de dados: {db_path}")
    
    # Verificar se o arquivo existe
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado em: {db_path}")
        return
    
    # Conectar diretamente ao SQLite
    conn = sqlite3.connect(db_path)
    
    # Adicionar novas colunas à tabela customer
    add_column(conn, 'customer', 'temp_data', 'TEXT')
    add_column(conn, 'customer', 'human_support', 'BOOLEAN DEFAULT 0')
    add_column(conn, 'customer', 'assigned_to', 'INTEGER')
    
    # Adicionar nova coluna à tabela whats_app_message (nome correto da tabela)
    add_column(conn, 'whats_app_message', 'is_human', 'BOOLEAN DEFAULT 0')
    
    # Commit das alterações
    conn.commit()
    conn.close()
    
    print("Migração concluída com sucesso!")

if __name__ == '__main__':
    with app.app_context():
        migrate()
