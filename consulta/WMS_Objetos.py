
from flask import Blueprint, jsonify
from database.server import create_connection_tinturaria # Conexão correta (Stik DB)

wms_objetos_bp = Blueprint('wms_objetos', __name__)

@wms_objetos_bp.route('/consulta/wms/objetos/<int:grupo_id>', methods=['GET'])
def get_wms_objetos(grupo_id):
    """
    Endpoint para consultar os objetos (filhos) de um grupo específico (pai).
    """
    connection = None
    try:
        connection = create_connection_tinturaria() 
        cursor = connection.cursor()

        sql_query = """
            SET NOCOUNT ON;
            
            SELECT
                CdObjMae = ObjMae.CdObj
            ,   NmObjMae = ObjMae.NmObj
            ,   CdObj = Obj.CdObj
            ,   NmObj = Obj.NmObj
            FROM 
                dbo.TbObj Obj
            LEFT JOIN 
                dbo.TbArvObj ArvObj ON ArvObj.CdObjFil = Obj.CdObj
            JOIN 
                dbo.TbObj ObjMae ON ObjMae.CdObj = Obj.CdObjMae
            WHERE
                ArvObj.CdObj = ? -- Parâmetro dinâmico da URL
        """
        
        # Passa o ID da URL (grupo_id) como parâmetro para a query
        cursor.execute(sql_query, (grupo_id,))

        registros = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        
        print(f"✅ Consulta WMS Objetos (Grupo {grupo_id}) executada. {len(registros)} linhas retornadas.")
        return jsonify(registros)

    except Exception as e:
        print(f"❌ Erro ao consultar WMS Objetos: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()
            print("🔌 Conexão com o banco de dados fechada.")