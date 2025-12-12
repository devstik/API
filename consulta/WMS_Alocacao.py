from flask import Blueprint, jsonify, request
from database.server import create_connection_tinturaria 
import datetime  

# Define o Blueprint
wms_alocacao_bp = Blueprint('wMS_alocacao', __name__)

@wms_alocacao_bp.route('/consulta/wms/gerar_alocacao', methods=['GET'])
def get_wms_alocacao():
    """
    Endpoint que EXECUTA o Stored Procedure 'sp_WMS_GerarAlocacao'.
    
    Parâmetros da Query:
    ?data_inicio=YYYY-MM-DD (Obrigatório)
    ?data_fim=YYYY-MM-DD    (Obrigatório)
    ?CodSKU=12345           (Opcional - se omitido, recalcula tudo)
    """
    connection = None
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # 1. Captura o CodSKU. Se não vier, fica como None.
        cod_sku = request.args.get('CodSKU')

        # Tratamento: Se vier uma string vazia (ex: ?CodSKU=), forçamos None
        if not cod_sku:
            cod_sku = None

        if not data_inicio or not data_fim:
            return jsonify({"error": "Parâmetros 'data_inicio' e 'data_fim' são obrigatórios."}), 400

        connection = create_connection_tinturaria() 
        cursor = connection.cursor()

        # 2. Atualizamos a chamada para aceitar 3 parâmetros
        # @Param_CodSKU é o nome que demos no SQL
        sql_query = "EXEC dbo.sp_WMS_GerarAlocacao @DataInicioABC = ?, @DataFimABC = ?, @Param_CodSKU = ?;"
        
        # 3. Passamos as 3 variáveis. O driver (pyodbc) converterá None para NULL automaticamente.
        cursor.execute(sql_query, (data_inicio, data_fim, cod_sku))

        registros = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        
        # Salva as alterações (INSERT/DELETE/UPDATE)
        connection.commit()
        
        msg_extra = f"Filtro SKU: {cod_sku}" if cod_sku else "Filtro: GERAL (Todos)"
        print(f"✅ Alocação WMS gerada e SALVA. {len(registros)} registros retornados. ({msg_extra})")
        
        return jsonify(registros)

    except Exception as e:
        print(f"❌ Erro ao gerar alocação WMS: {e}")
        if connection:
            connection.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()
            print("🔌 Conexão com o banco de dados fechada.")