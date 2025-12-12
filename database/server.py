import pyodbc

def create_connection():
    server = '168.190.30.18'
    database = 'EmbalagemIn'
    username = 'sa'
    password = 'Stik0123'
    
    # Criar a string de conexão
    connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    
    # Estabelecer a conexão com o banco de dados
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except pyodbc.Error as e:
        print(f'Erro ao conectar ao banco de dados: {str(e)}')
        return None
    
def create_connection_tinturaria():
    server = '45.235.240.135'
    database = 'Stik'
    username = 'ti'
    password = 'Stik0123'

    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )

    try:
        conn = pyodbc.connect(connection_string, timeout=5)
        print("✅ Conectado ao banco de dados Stik com sucesso.")
        return conn
    except pyodbc.Error as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        return None
   