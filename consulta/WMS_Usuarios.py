from flask import Blueprint, jsonify
from database.server import create_connection_tinturaria 
import datetime

# Define o Blueprint
wms_usuarios_bp = Blueprint('wms_usuarios', __name__)

@wms_usuarios_bp.route('/consulta/wms/usuarios', methods=['GET'])
def get_wms_usuarios():
    """
    Endpoint para consultar os usuários do WMS/sistema (TbUsr),
    agora com um grupo (Admin/Separador).
    """
    connection = None
    try:
        connection = create_connection_tinturaria() 
        cursor = connection.cursor()

        # Consulta SQL atualizada com a tabela temporária
        sql_query = """
            SET NOCOUNT ON;
            
            -- 1. Cria a tabela temporária para os Separadores
            IF OBJECT_ID('tempdb..#Separadores') IS NOT NULL DROP TABLE #Separadores;
            CREATE TABLE #Separadores (CdUsr INT PRIMARY KEY);

            -- 2. Insere os IDs dos Separadores
            INSERT INTO #Separadores (CdUsr) VALUES
            (357), (372), (183), (324), (168), (358), (347), (138), (333), 
            (390), (294), (332), (373), (114), (367);

            -- 3. Consulta final
            SELECT 
                Usr.CdUsr, 
                Usr.NmUsr,
                -- Cria a coluna 'Grupo' com base na tabela temporária
                Grupo = CASE 
                            WHEN Sep.CdUsr IS NOT NULL THEN 'Separador' 
                            ELSE 'Admin' 
                        END
            FROM dbo.TbUsr AS Usr
            -- Faz um LEFT JOIN com a temp table
            LEFT JOIN #Separadores AS Sep ON Usr.CdUsr = Sep.CdUsr
            WHERE 
                -- Filtra por TODOS os usuários (Admins E Separadores)
                Usr.CdUsr IN (
                    -- Lista de Admins (do código original)
                    58, 323, 322, 325, 376, 329, 328, 334, 400, 461, 327, 207, 504, 476,
                    -- Lista de Separadores
                    357, 372, 183, 324, 168, 358, 347, 138, 333, 390, 294, 332, 373, 114, 367
                );

            -- 4. Limpa a tabela temporária
            DROP TABLE #Separadores;
        """
        
        cursor.execute(sql_query)

        # Converte o resultado em uma lista de dicionários
        registros = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        
        print(f"✅ Consulta WMS Usuários (TbUsr) executada. {len(registros)} linhas retornadas.")
        return jsonify(registros)

    except Exception as e:
        print(f"❌ Erro ao consultar WMS Usuários: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()
            print("🔌 Conexão com o banco de dados fechada.")