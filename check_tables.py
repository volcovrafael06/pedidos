import os
import sqlite3
import os.path

def check_tables(db_path):
    """Verifica quais tabelas existem no banco de dados"""
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado em: {db_path}")
        return
    
    print(f"Verificando tabelas no banco de dados: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Consultar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tabelas encontradas:")
    for table in tables:
        table_name = table[0]
        print(f"- {table_name}")
        
        # Mostrar colunas da tabela
        try:
            cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
            columns = cursor.fetchall()
            print("  Colunas:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        except sqlite3.OperationalError as e:
            print(f"  Erro ao obter informações da tabela: {e}")
    
    conn.close()

if __name__ == '__main__':
    # Verificar em ambos os caminhos possíveis
    paths = ['pizzaria.db', 'instance/pizzaria.db']
    for path in paths:
        check_tables(path)
