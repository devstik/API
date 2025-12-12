from flask import Blueprint, jsonify, request
from database.server import create_connection_tinturaria 
import datetime  

# Define o Blueprint
wms_movimentos_bp = Blueprint('wms_movimentos', __name__)

# ===================================================================
# ROTA 1: POST (para INSERIR um novo movimento)
# ===================================================================
@wms_movimentos_bp.route('/consulta/wms/movimentar', methods=['POST'])
def inserir_movimento():
    """
    Endpoint para registrar uma nova entrada (1) ou saída (2)
    de um SKU em um endereço.
    """
    connection = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados JSON não fornecidos"}), 400

        # Pega os dados do JSON enviado
        endereco = data.get('Endereco')
        cod_sku = data.get('CodSKU')
        tp_mov = data.get('TpMov')
        # Pega a quantidade (opcional, assume 1 se não for enviada)
        qt_movida = data.get('QtMovida', 1) 

        if not all([endereco, cod_sku, tp_mov]):
            return jsonify({"error": "Campos 'Endereco', 'CodSKU' e 'TpMov' são obrigatórios"}), 400

        connection = create_connection_tinturaria() 
        cursor = connection.cursor()

        sql_query = """
            SET NOCOUNT ON;
            INSERT INTO dbo.stik_WMS_Movimento
                (Endereco, CodSKU, TpMov, QtMovida, DataMovimento)
            VALUES
                (?, ?, ?, ?, GETDATE());
        """
        
        cursor.execute(sql_query, (endereco, cod_sku, tp_mov, qt_movida))
        
        # IMPORTANTE: Commit() é necessário para salvar um INSERT
        connection.commit() 
        
        print(f"✅ Movimento registrado: SKU {cod_sku} -> Endereço {endereco}, Tipo {tp_mov}")
        return jsonify({"message": "Movimento registrado com sucesso!"}), 201

    except Exception as e:
        if connection:
            connection.rollback() # Desfaz a alteração se der erro
        print(f"❌ Erro ao registrar movimento: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()
            print("🔌 Conexão com o banco de dados fechada.")

# ===================================================================
# ROTA 2: GET (para CONSULTAR os movimentos)
# ===================================================================
@wms_movimentos_bp.route('/consulta/wms/movimentos', methods=['GET'])
def get_movimentos():
    """
    Endpoint para consultar o histórico de movimentos.
    Aceita filtros por ?CodSKU=... ou ?Endereco=...
    """
    connection = None
    try:
        # Pega filtros opcionais da URL
        cod_sku = request.args.get('CodSKU')
        endereco = request.args.get('Endereco')

        connection = create_connection_tinturaria() 
        cursor = connection.cursor()

        # Constrói a query base
        sql_query = "SET NOCOUNT ON; SELECT * FROM dbo.stik_WMS_Movimento"
        params = []
        
        # Adiciona filtros se eles existirem
        if cod_sku or endereco:
            sql_query += " WHERE 1=1"
            if cod_sku:
                sql_query += " AND CodSKU = ?"
                params.append(int(cod_sku))
            if endereco:
                sql_query += " AND Endereco = ?"
                params.append(endereco)
        
        sql_query += " ORDER BY DataMovimento DESC;" # Mais recente primeiro

        cursor.execute(sql_query, params)
        registros = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        
        print(f"✅ Consulta de movimentos executada. {len(registros)} linhas retornadas.")
        return jsonify(registros)

    except Exception as e:
        print(f"❌ Erro ao consultar movimentos: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()
            print("🔌 Conexão com o banco de dados fechada.")