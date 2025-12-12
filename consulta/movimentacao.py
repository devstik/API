from dateutil import parser # <<< ISTO DEVE ESTAR NO TOPO DO SEU ARQUIVO!
from flask import Blueprint, jsonify, request
from database.server import create_connection
import datetime
import pyodbc

movimentacao_bp = Blueprint('movimentacao', __name__)

@movimentacao_bp.route('/consulta/movimentacao', methods=['GET', 'POST', 'PUT'])
def gerenciar_movimentacao():
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor()

        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"error": "Dados JSON não fornecidos ou inválidos"}), 400

            # Campos de STRING
            Artigo = data.get('Artigo', '')
            Cor = data.get('Cor', '')
            Conferente = data.get('Conferente', '')
            Turno = data.get('Turno', '')
            Localizacao = data.get('Localizacao', '')
            NumCorte = data.get('NumCorte', '')

            # Campos NUMÉRICOS
            try:
                NrOrdem = int(data.get('NrOrdem', 0))
            except (ValueError, TypeError):
                return jsonify({"error": "NrOrdem inválido ou ausente"}), 400

            try:
                Quantidade = int(data.get('Quantidade', 0))
            except (ValueError, TypeError):
                Quantidade = 0

            Peso = float(data.get('Peso', 0.0)) if data.get('Peso') is not None else 0.0
            Metros = float(data.get('Metros', 0.0)) if data.get('Metros') is not None else 0.0
            VolumeProg = float(data.get('VolumeProg', 0.0)) if data.get('VolumeProg') is not None else 0.0
            
            DataEntrada = data.get('DataEntrada')

            # Validação obrigatória
            if not all([NrOrdem > 0, Artigo, Cor, Conferente, Turno, Localizacao, DataEntrada]):
                return jsonify({"error": "NrOrdem, Artigo, Cor, Conferente, Turno, Localizacao e DataEntrada são obrigatórios"}), 400

            # Execução SQL
            insert_sql = """
                INSERT INTO Pedidos (
                    NrOrdem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, Metros, 
                    NumCorte, VolumeProg, Localizacao, DataEntrada
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(
                insert_sql,
                (NrOrdem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, Metros,
                 NumCorte, VolumeProg, Localizacao, DataEntrada)
            )
            connection.commit()
            return jsonify({"message": "Registro de Movimentação criado com sucesso!"}), 201

        elif request.method == 'PUT':
            
            data = request.get_json()
            NrOrdem = data.get('NrOrdem')
            LocalizacaoNova = data.get('Localizacao')
            Conferente = data.get('Conferente')
            DataMov_str = data.get('DataSaida')
            TipoMovimentacao = data.get('TipoMovimentacao')
            LocalizacaoAnterior = data.get('LocalizacaoAnterior')
            
            # 💡 Captura o valor de MetrosMovidos
            MetrosMovidos = float(data.get('MetrosMovidos', 0.0)) if data.get('MetrosMovidos') is not None else 0.0

            # Validação dos campos obrigatórios
            campos_obrigatorios = [NrOrdem, LocalizacaoNova, Conferente, DataMov_str, TipoMovimentacao, LocalizacaoAnterior]
            if any(campo is None for campo in campos_obrigatorios):
                return jsonify({"error": "Campos obrigatórios para PUT ausentes"}), 400

            # Converte a string ISO 8601 para datetime
            try:
                DataMov = parser.isoparse(DataMov_str)
            except Exception:
                return jsonify({"error": f"Data inválida: {DataMov_str}"}), 400

            # Busca o registro ATIVO e ESPECÍFICO (com DataSaida IS NULL) que está sendo movido
            fetch_active_record_sql = """
                SELECT 
                    ID, Artigo, Cor, Quantidade, Peso, Turno, Metros, NumCorte, VolumeProg, Localizacao
                FROM Pedidos
                WHERE NrOrdem = ? AND Localizacao = ? AND DataSaida IS NULL
            """
            cursor.execute(fetch_active_record_sql, (NrOrdem, LocalizacaoAnterior))
            detalhes = cursor.fetchone()

            if not detalhes:
                return jsonify({"error": f"Nenhum registro ativo encontrado para OP {NrOrdem} em {LocalizacaoAnterior}"}), 404

            # Desempacota os detalhes do registro ATIVO
            ID_Origem, Artigo, Cor, Quantidade, Peso, Turno, Metros, NumCorte, VolumeProg, LocalizacaoAtual = detalhes
            
            LocalizacaoAnterior_DB = LocalizacaoAtual
            
            # Variável para a quantidade que será registrada no histórico
            quantidade_hist = 0.0
            
            # A quantidade total do registro de origem que será movida/consolidada
            metros_a_mover = Metros 

            # --- LÓGICA DE MOVIMENTAÇÃO CONDICIONAL ---

            if TipoMovimentacao == 'PARCIAL' and MetrosMovidos > 0.0:
                
                if MetrosMovidos >= Metros:
                    return jsonify({"error": "A quantidade movida (MetrosMovidos) não pode ser maior ou igual ao saldo atual."}), 400
                    
                # 1. ATUALIZAÇÃO DO SALDO ORIGINAL (Origem) - APENAS SUBTRAÇÃO DE METROS
                # Quantidade, Peso e VolumeProg são mantidos inalterados, conforme solicitado.
                update_origem_sql = """
                    UPDATE Pedidos
                    SET 
                        Metros = Metros - ?
                    WHERE ID = ?
                """
                cursor.execute(update_origem_sql, (MetrosMovidos, ID_Origem))
                
                # 2. INSERÇÃO DO NOVO REGISTRO (Destino) - CRIAÇÃO
                insert_destino_sql = """
                    INSERT INTO Pedidos (
                        NrOrdem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, Metros,
                        NumCorte, VolumeProg, Localizacao, DataEntrada
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                # Usa MetrosMovidos para o campo Metros e herda Quantidade, Peso e VolumeProg totais.
                cursor.execute(insert_destino_sql, (
                    NrOrdem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, MetrosMovidos, 
                    NumCorte, VolumeProg, LocalizacaoNova, DataMov 
                ))
                
                quantidade_hist = MetrosMovidos # Metros movidos para o histórico

            else: # TipoMovimentacao é 'NORMAL' ou COMPLETA
                
                # ----------------------------------------------------------------------
                # PASSO 1: NOVO - Tenta CONSOLIDAR o estoque na Localização de Destino
                # ----------------------------------------------------------------------
                
                # 1a. Busca por um registro ATIVO (DataSaida IS NULL) no destino com as mesmas chaves (OP, Artigo, Cor)
                fetch_target_sql = """
                    SELECT ID, Metros 
                    FROM Pedidos
                    WHERE NrOrdem = ? AND Artigo = ? AND Cor = ? AND Localizacao = ? AND DataSaida IS NULL
                """
                cursor.execute(fetch_target_sql, (NrOrdem, Artigo, Cor, LocalizacaoNova))
                registro_destino = cursor.fetchone()

                if registro_destino:
                    # Se encontrou um registro ativo: CONSOLIDAÇÃO (SOMA)
                    ID_Destino, Metros_Destino_Atual = registro_destino
                    
                    update_destino_sql = """
                        UPDATE Pedidos
                        SET Metros = Metros + ?
                        WHERE ID = ?
                    """
                    # Soma os metros do registro de origem ao registro de destino
                    cursor.execute(update_destino_sql, (metros_a_mover, ID_Destino))
                    
                    # 2. FECHA REGISTRO ORIGINAL (Origem) - Apenas encerra o registro que foi movido
                    update_origem_sql = """
                        UPDATE Pedidos
                        SET DataSaida = ?
                        WHERE ID = ?
                    """
                    cursor.execute(update_origem_sql, (DataMov, ID_Origem))
                    
                    quantidade_hist = metros_a_mover # O total movido para o histórico
                    
                else: 
                    # Se NÃO encontrou um registro ativo: CRIA NOVO REGISTRO (Comportamento anterior)

                    # 1. FECHA REGISTRO ORIGINAL (Origem) - DataSaida é preenchida
                    update_sql = """
                        UPDATE Pedidos
                        SET DataSaida = ?
                        WHERE ID = ?
                    """
                    cursor.execute(update_sql, (DataMov, ID_Origem))

                    # 2. CRIA NOVO REGISTRO (Destino) com a QUANTIDADE COMPLETA (Metros)
                    if LocalizacaoNova == 'Expedição':
                        insert_sql = """
                            INSERT INTO Pedidos (
                                NrOrdem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, Metros,
                                NumCorte, VolumeProg, Localizacao, DataEntrada, DataSaida
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        cursor.execute(insert_sql, (
                            NrOrdem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, Metros,
                            NumCorte, VolumeProg, LocalizacaoNova, DataMov, DataMov
                        ))
                    else:
                        insert_sql = """
                            INSERT INTO Pedidos (
                                NrOrdem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, Metros,
                                NumCorte, VolumeProg, Localizacao, DataEntrada
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        cursor.execute(insert_sql, (
                            NrOrdem, Artigo, Cor, Quantidade, Peso, Conferente, Turno, Metros,
                            NumCorte, VolumeProg, LocalizacaoNova, DataMov
                        ))
                    
                    quantidade_hist = Metros
                
            # --- INSERÇÃO NO HISTÓRICO (AGORA COM QUANTIDADE) ---
            insert_hist_sql = """
                INSERT INTO HistoricoMovimentacoes (
                    NrOrdem, LocalizacaoDestino, DataMovimentacao, Conferente, TipoMovimentacao, LocalizacaoOrigem, QuantidadeMovida
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            # Usa a LocalizacaoAnterior_DB (LocalizacaoAtual) que foi lida do banco
            cursor.execute(insert_hist_sql, (
                NrOrdem, LocalizacaoNova, DataMov, Conferente, TipoMovimentacao, LocalizacaoAnterior_DB, quantidade_hist
            ))

            connection.commit()
            return jsonify({"message": f"OP {NrOrdem} movida de {LocalizacaoAnterior_DB} para {LocalizacaoNova}. Tipo: {TipoMovimentacao}"}), 200

        else: # GET
            localizacao_filtro = request.args.get('localizacao')
            query = "SELECT * FROM Pedidos WHERE DataSaida IS NULL"
            params = []

            # Se está filtrando por Expedição, mostra registros mesmo com DataSaida preenchida
            if localizacao_filtro == 'Expedição':
                query = "SELECT * FROM Pedidos WHERE Localizacao = ?"
                params = [localizacao_filtro]
            elif localizacao_filtro:
                query += " AND Localizacao = ?"
                params.append(localizacao_filtro)

            query += " ORDER BY ID DESC"
            cursor.execute(query, params)

            registros = []
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                item = dict(zip(columns, row))
                for key in ['DataEntrada', 'DataSaida']:
                    if item[key] and isinstance(item[key], datetime.datetime):
                        item[key] = item[key].isoformat() + 'Z'
                registros.append(item)

            return jsonify(registros)

    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        return jsonify({"error": f"Erro de Banco de Dados: {sqlstate}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()

movimentacao_historico_bp = Blueprint('movimentacao_historico', __name__)

@movimentacao_historico_bp.route('/consulta/movimentacao_historico', methods=['GET'])
def buscar_historico():
    """Busca TODO o histórico de movimentações, IGNORANDO qualquer filtro de nrOrdem."""
    connection = None
    try:
        # A leitura de nrOrdem (request.args.get('nrOrdem')) AGORA É IGNORADA.
        
        connection = create_connection()
        cursor = connection.cursor()
        
        # A QUERY É MONTADA SEM O WHERE para buscar todos os registros
        query = """
            SELECT 
                ID,
                NrOrdem,
                LocalizacaoOrigem,
                LocalizacaoDestino,
                DataMovimentacao,
                Conferente,
                TipoMovimentacao
            FROM HistoricoMovimentacoes
            ORDER BY DataMovimentacao DESC
        """
        
        # Executa a query, que agora sempre busca TUDO
        cursor.execute(query)
        
        historico = []
        columns = [col[0] for col in cursor.description]
        
        for row in cursor.fetchall():
            item = dict(zip(columns, row))
            
            # Conversão de datetime
            if item.get('DataMovimentacao') and isinstance(item['DataMovimentacao'], datetime.datetime):
                item['DataMovimentacao'] = item['DataMovimentacao'].isoformat() + 'Z'
            
            historico.append(item)
        
        return jsonify(historico), 200
        
    except pyodbc.Error as ex:
        # ... (tratamento de erro)
        return jsonify({"error": f"Erro de Banco de Dados: {ex.args[0]}"}), 500
    
    except Exception as e:
        # ... (tratamento de erro)
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection:
            connection.close()