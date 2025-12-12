from flask import Blueprint, jsonify, request
# Presume que create_connection_tinturaria está definido em database.server
from database.server import create_connection_tinturaria 
import pyodbc # Importa pyodbc, se ainda não estiver importado no arquivo principal

tinturariaDados_bp = Blueprint('tinturariaDados', __name__)

@tinturariaDados_bp.route('/consulta/tinturariaDados', methods=['GET'])
def consultar_tinturaria_dados():
    connection = None
    try:
        connection = create_connection_tinturaria()
        cursor = connection.cursor()

        nr_ordem = request.args.get('ordem')

        # 🟢 Colunas do SELECT
        colunas_select = '''
            P.[ID],
            P.[SkuID],
            P.[SKU],
            P.[NrOrdem],
            CONVERT(varchar, P.[DtPedido], 103) AS DtPedido,
            CONVERT(varchar, P.[DtEntrega], 103) AS DtEntrega,
            CONVERT(varchar, P.[DtLeadtime], 103) AS DtLeadtime,
            COALESCE(M.[Cliente], P.[Cliente]) AS Cliente,
            CASE WHEN E.[PedidoEspecial] = 1 THEN 'Sim' ELSE 'Não' END AS PedidoEspecial,
            P.[Qtd],
            G.[Gramatura] AS MetrosEstimados
        '''

        # 🔹 Base da Query (seguindo o mesmo modelo do seu SELECT original)
        sql_query_base = '''
            FROM Stik_Tinturaria_Programacao P
            LEFT JOIN STIK_OneBeat_OrdensMTA M 
                ON P.NrOrdem = M.NrOrdem
            LEFT JOIN TbObj O 
                ON O.CdObj = M.CdObj
            LEFT JOIN Stik_PCP_PEDIDOESPECIAL E 
                ON E.NrOrdem = P.NrOrdem
            LEFT JOIN TbObj Obj 
                ON Obj.CdObj = P.SKUID
            LEFT JOIN Stik_PCP_GRAMATURA G 
                ON G.CdObj = Obj.CdObjMae
        '''

        # 🔸 Filtro opcional por número de ordem
        where_clause = ''
        params = ()
        if nr_ordem:
            where_clause = ' WHERE P.[NrOrdem] = ? '
            params = (nr_ordem,)

        # 🔴 GROUP BY igual ao seu SQL original
        colunas_group_by = '''
            P.[ID],
            P.[SkuID],
            P.[SKU],
            P.[NrOrdem],
            CONVERT(varchar, P.[DtPedido], 103),
            CONVERT(varchar, P.[DtEntrega], 103),
            CONVERT(varchar, P.[DtLeadtime], 103),
            COALESCE(M.[Cliente], P.[Cliente]),
            E.[PedidoEspecial],
            P.[Qtd],
            G.[Gramatura]
        '''

        # 🔹 Query final
        sql_query = f'''
            SELECT 
                {colunas_select}
            {sql_query_base}
            {where_clause}
            GROUP BY 
                {colunas_group_by}
            ORDER BY 
                P.[NrOrdem]
        '''

        # 🔹 Executa a query
        cursor.execute(sql_query, params)

        registros = [
            dict(zip([column[0] for column in cursor.description], row))
            for row in cursor.fetchall()
        ]

        return jsonify(registros)

    except Exception as e:
        print(f"❌ Erro ao consultar tinturaria: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()


@tinturariaDados_bp.route('/consulta/gramaturaByArtigo', methods=['GET'])
def consultar_gramatura_por_artigo():
    connection = None
    try:
        artigo_nome = request.args.get('artigo_nome')

        if not artigo_nome:
            return jsonify({"error": "Parâmetro 'artigo_nome' não fornecido"}), 400

        connection = create_connection_tinturaria()
        
        if not connection:
             return jsonify({"error": "Falha ao conectar ao banco de dados"}), 500

        cursor = connection.cursor()

        sql_query = '''
            SELECT TOP 1 
                G.[Gramatura] 
            FROM TbObj O
            LEFT JOIN Stik_PCP_GRAMATURA G 
                ON G.CdObj = O.CdObjMae
            WHERE O.[NmObj] LIKE ? -- AGORA SÓ BUSCA O FINAL DO NOME (EX: %nillo 16 mm)
            AND G.[Gramatura] IS NOT NULL
            ORDER BY O.[CdObj] DESC
        '''
        
        params = (f'%{artigo_nome.strip()}',)

        cursor.execute(sql_query, params)
        result = cursor.fetchone()

        if result and result[0] is not None:
            return jsonify({"Gramatura": result[0]}), 200
        else:
            return jsonify({"Gramatura": "0.00"}), 200

    except Exception as e:
        print(f"❌ Erro ao consultar gramatura por artigo: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()


# --- Blueprint para Consulta de Operador ---
tinturariaOperador_bp = Blueprint('tinturariaOperador', __name__)

@tinturariaOperador_bp.route('/consulta/operador', methods=['GET'])
def consultar_operador():
    connection = None
    try:
        # ... (código existente da consulta de operador)
        matricula = request.args.get('matricula')

        if matricula:
            try:
                matricula_int = int(matricula)
                matricula = str(matricula_int)
            except ValueError:
                return jsonify({"Operador": "Matrícula inválida ou não numérica"}), 400 

        connection = create_connection_tinturaria()
        
        if not connection:
            return jsonify({"error": "Falha ao conectar ao banco de dados"}), 500

        cursor = connection.cursor()
        
        sql_query = '''
            SELECT
                Matricula,
                Operador,
                Apelido
            FROM dbo.Stik_Tinturaria_Operador (NOLOCK)
        '''
        
        params = ()
        
        if matricula:
            sql_query += ' WHERE Matricula = ?' 
            params = (matricula,)
            
        cursor.execute(sql_query, params)
        
        
        if matricula:
            result = cursor.fetchone()

            if result:
                operador_info = {
                    "Matricula": result[0],
                    "Operador": result[1],
                    "Apelido": result[2]
                }
                return jsonify(operador_info), 200
            else:
                return jsonify({"Operador": "Operador não encontrado"}), 404
        
        else:
            registros = [
                dict(zip([column[0] for column in cursor.description], row))
                for row in cursor.fetchall()
            ]
            return jsonify(registros), 200

    except Exception as e:
        print(f"❌ Erro ao consultar operador: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()