import threading
import time
import webbrowser
from flask import Flask, render_template
from flask_cors import CORS
from flask_compress import Compress
from flask_bcrypt import Bcrypt # Importa a biblioteca Bcrypt

from consulta.embalagem import embalagem_bp
from consulta.tinturaria import tinturaria_bp
from consulta.movimentacao import movimentacao_bp
from consulta.usuarios import usuarios_bp # 💡 
from database.server import create_connection
from database.server import create_connection_tinturaria
from consulta.movimentacao import movimentacao_historico_bp
from consulta.TinturariaDados import tinturariaDados_bp, tinturariaOperador_bp
from consulta.WMS_Romaneio import wms_bp 
from consulta.WMS_Enderecos import wms_enderecos_bp
from consulta.WMS_Ruas import wms_ruas_bp
from consulta.WMS_Usuarios import wms_usuarios_bp
from consulta.WMS_Objetos import wms_objetos_bp
from consulta.WMS_Alocacao import wms_alocacao_bp
from consulta.WMS_Movimentos import wms_movimentos_bp

app = Flask(__name__, template_folder="template")
CORS(app) # Habilita CORS para todas as rotas
Compress(app) # Habilita compressão Gzip
bcrypt = Bcrypt(app) # 💡 Inicializa o Bcrypt com a aplicação Flask

# Estabelece a conexão com o banco de dados para teste de conexão inicial
conn = create_connection()

if conn:
    print('Conexão com o banco de dados estabelecida com sucesso.')
    conn.close() # Fechar logo após o teste para liberar recurso
else:
    print('Falha ao estabelecer conexão com o banco de dados.')


@app.route('/', methods=['GET'])
def home():
    # Renderiza o template home.html (o código HTML corrigido acima)
    return render_template('home.html')

# Registro dos blueprints das rotas
app.register_blueprint(embalagem_bp)
app.register_blueprint(tinturaria_bp)
app.register_blueprint(movimentacao_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(movimentacao_historico_bp)
app.register_blueprint(tinturariaDados_bp)
app.register_blueprint(tinturariaOperador_bp)
app.register_blueprint(wms_bp) 
app.register_blueprint(wms_enderecos_bp)
app.register_blueprint(wms_ruas_bp)
app.register_blueprint(wms_usuarios_bp)
app.register_blueprint(wms_objetos_bp)
app.register_blueprint(wms_alocacao_bp)
app.register_blueprint(wms_movimentos_bp)

# Função para abrir navegador automaticamente (se desejar usar, descomente)
# def abrir_navegador():
#     time.sleep(1) # Espera o servidor iniciar
#     # Tenta pegar IP local da máquina
#     # hostname = socket.gethostname()
#     # local_ip = socket.gethostbyname(hostname)
#     # url_local = f"http://{local_ip}:5000"
#     # print(f"Abrindo navegador no endereço {url_local}")
#     # webbrowser.open(url_local)

if __name__ == '__main__':
    # Inicia o servidor Flask
    app.run(host="0.0.0.0", port=5000, debug=False)