from flask import Blueprint, jsonify, request
from database.server import create_connection

embalagem_bp = Blueprint('embalagem', __name__)

@embalagem_bp.route('/consulta/embalagem', methods=['GET', 'POST'])
def gerenciar_embalagem():
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor()

        if request.method == 'POST':
            data = request.get_json()

            if not data:
                return jsonify({"error": "Dados JSON não fornecidos ou inválidos"}), 400

            Data = data.get('Data')
            Nrordem = data.get('NrOrdem')
            Artigo = data.get('Artigo')
            Cor = data.get('Cor')
            Quantidade = data.get('Quantidade')
            Peso = data.get('Peso')
            Conferente = data.get('Conferente')
            Turno = data.get('Turno')
            Metros = data.get('Metros')
            DataTingimento = data.get('DataTingimento')
            NumCorte = data.get('NumCorte')
            VolumeProg = data.get('VolumeProg') 
            campos_obrigatorios = [Data, Nrordem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, Metros, VolumeProg]

            if any(campo is None for campo in campos_obrigatorios):
                return jsonify({"error": "Todos os campos obrigatórios devem ser fornecidos"}), 400

            # 2. Incluir o novo campo VolumeProg na query INSERT
            insert_sql = """
                INSERT INTO TbRegEmbalagem (Data, NrOrdem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, Metros, DataTingimento, NumCorte, VolumeProg)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
            """

            cursor.execute(
                insert_sql,
                (Data, Nrordem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, Metros, DataTingimento, NumCorte, VolumeProg) # <--- NOVO CAMPO VolumeProg adicionado aqui
            )
            connection.commit()

            print(f"✅ Registro criado com sucesso: {data}")
            
            # Se a requisição for POST e bem-sucedida, você pode retornar uma resposta de sucesso mais concisa
            return jsonify({"message": "Registro de embalagem criado com sucesso!"}), 201


        # Se a requisição for GET, o código de consulta continua o mesmo,
        # mas você deve adicionar 'VolumeProg' ao SELECT se ele estiver no banco
        cursor.execute('''
            SELECT
                ID = Emb.ID,
                Data = Emb.Data,
                NrOrdem = Emb.NrOrdem,
                Artigo = Emb.Artigo,
                Cor = Emb.Cor,
                Quantidade = Emb.Quantidade,
                Peso = Emb.Peso,
                Conferente = Emb.Conferente,
                Turno = Emb.Turno,
                Metros = Emb.Metros,
                DataTingimento = Emb.DataTingimento,
                NumCorte = Emb.NumCorte,
                VolumeProg = Emb.VolumeProg  
            FROM TbRegEmbalagem Emb (nolock)
            ORDER BY Emb.ID ASC
        ''')

        embalagens = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

        return jsonify(embalagens)

    except Exception as e:
        print(f"❌ Erro ao gerenciar embalagem: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()