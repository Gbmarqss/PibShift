import re
import pandas as pd
import datetime

def extrair_nome_sobrenome(nome_completo):
    """Extrai o primeiro e o último nome de um nome completo."""
    nome_lower = nome_completo.lower().strip()

    apelidos_para_nomes = {
        "gb marques": "Gabriel Marques",
        "gabriel": "Gabriel Marques",
        "lay": "Laysa",
        "layy": "Laysa",
    }

    for apelido, nome_padronizado in apelidos_para_nomes.items():
        if apelido in nome_lower:
            return nome_padronizado

    partes = nome_completo.split()
    return " ".join([partes[0], partes[-1]]) if len(partes) > 1 else partes[0]

def verificar_conflitos(escala_df):
    """Verifica conflitos em uma escala."""
    conflitos = set()

    if 'Voluntario' not in escala_df.columns:
        for col in escala_df.columns:
            if 'volunt' in col.lower():
                escala_df.rename(columns={col: 'Voluntario'}, inplace=True)
                break
        else:
            return conflitos
    
    escala_df['Voluntario'] = escala_df['Voluntario'].astype(str)
    df_sem_nao_designado = escala_df[escala_df['Voluntario'] != 'Não designado']

    duplicados_dia = df_sem_nao_designado[df_sem_nao_designado.duplicated(
        subset=['Data', 'Voluntario'], keep=False)]
    
    for index, row in duplicados_dia.iterrows():
        conflitos.add((row['Data'], row['Voluntario']))

    return conflitos

def gerar_rascunho(df, ministerios_ativos=None):
    """Gera um rascunho de escala a partir de um DataFrame."""
    if 'ÁREA DE ATUAÇÃO' not in df.columns:
        return None, None, "A coluna 'ÁREA DE ATUAÇÃO' não foi encontrada."
    
    # Ministérios padrão se não for especificado
    if ministerios_ativos is None:
        ministerios_ativos = ['PRODUÇÃO', 'FILMAGEM', 'PROJEÇÃO', 'TAKE', 'ILUMINAÇÃO']
    
    num_servidores_por_area = {
        'PRODUÇÃO': 1,
        'FILMAGEM': 3,
        'PROJEÇÃO': 1,
        'TAKE': 2,
        'ILUMINAÇÃO': 1,
    }
    
    # Filtrar apenas ministérios ativos
    num_servidores_por_area = {k: v for k, v in num_servidores_por_area.items() 
                              if k in ministerios_ativos}

    shifts_count = {}
    max_shifts_per_person = 2

    colunas_ignorar = ['CARIMBO DE DATA/HORA', 'ENDEREÇO DE E-MAIL', 
                      'CELULAR (WHATSAPP)', 'NOME', 'ÁREA DE ATUAÇÃO']
    colunas_datas = [col for col in df.columns if col not in colunas_ignorar]
    
    escala_final_slots = []
    available_servers_per_day = {}

    for coluna_data in colunas_datas:
        dia_df = df[df[coluna_data] == 'SIM']
        daily_available_servers = {}

        # CORREÇÃO: Detecção mais precisa das áreas
        for area_key in num_servidores_por_area.keys():
            # Buscar correspondência exata ou por palavra inteira
            servidores_area = []
            
            for idx, row in dia_df.iterrows():
                area_atuacao = str(row['ÁREA DE ATUAÇÃO']).upper()
                
                # Verificar se a área de atuação contém a área_key como palavra completa
                if pd.isna(area_atuacao) or area_atuacao == 'NAN':
                    continue
                    
                # Dividir a área de atuação em palavras e verificar correspondências
                palavras_areas = area_atuacao.split()
                
                # CORREÇÃO: Busca mais precisa
                if area_key == 'PRODUÇÃO':
                    # Para produção, buscar exatamente "PRODUÇÃO"
                    if 'PRODUÇÃO' in palavras_areas or 'PRODUCAO' in palavras_areas:
                        servidores_area.append(row['NOME'])
                elif area_key == 'FILMAGEM':
                    # Para filmagem, buscar "FILMAGEM" ou "FILMA"
                    if any(palavra.startswith('FILM') for palavra in palavras_areas):
                        servidores_area.append(row['NOME'])
                elif area_key == 'PROJEÇÃO':
                    # Para projeção, buscar exatamente "PROJEÇÃO" ou "PROJET"
                    if any(palavra.startswith('PROJE') for palavra in palavras_areas):
                        servidores_area.append(row['NOME'])
                elif area_key == 'TAKE':
                    # Para take, buscar "TAKE" ou "FOTO"
                    if any(palavra in ['TAKE', 'FOTO', 'FOTOGRAF'] for palavra in palavras_areas):
                        servidores_area.append(row['NOME'])
                elif area_key == 'ILUMINAÇÃO':
                    # Para iluminação, buscar "ILUMINA" ou "LUZ"
                    if any(palavra.startswith('ILUMIN') or palavra == 'LUZ' for palavra in palavras_areas):
                        servidores_area.append(row['NOME'])
            
            # Filtrar por máximo de turnos
            current_area_available = []
            for nome_servidor in servidores_area:
                nome_normalizado = extrair_nome_sobrenome(nome_servidor)
                if shifts_count.get(nome_normalizado, 0) < max_shifts_per_person:
                    current_area_available.append(nome_normalizado)
            
            daily_available_servers[area_key] = list(set(current_area_available))
        
        available_servers_per_day[coluna_data] = daily_available_servers

        allocated_for_day = set()
        area_counters = {area: 0 for area in num_servidores_por_area.keys()}
        
        gabriel = "Gabriel Marques"
        laysa = "Laysa"

        for area, num_servidores in num_servidores_por_area.items():
            area_pool = daily_available_servers.get(area, [])
            
            # Só alocar se houver voluntários disponíveis para esta área
            if not area_pool:
                # Preencher com "Não designado" se não houver voluntários
                for i in range(num_servidores):
                    funcao = area
                    if area == 'TAKE':
                        funcao = "Fotografo" if i == 0 else "Suporte"
                    
                    escala_final_slots.append({
                        "Data": coluna_data,
                        "Funcao": funcao,
                        "Voluntario": "Não designado"
                    })
                continue
            
            if (gabriel in area_pool and laysa in area_pool and 
                num_servidores >= 2 and 
                gabriel not in allocated_for_day and laysa not in allocated_for_day):
                
                for nome in [gabriel, laysa]:
                    funcao = area
                    if area == 'TAKE':
                        funcao = "Fotografo" if area_counters[area] == 0 else "Suporte"
                    
                    escala_final_slots.append({
                        "Data": coluna_data,
                        "Funcao": funcao,
                        "Voluntario": nome
                    })
                    allocated_for_day.add(nome)
                    shifts_count[nome] = shifts_count.get(nome, 0) + 1
                    area_pool.remove(nome)
                    area_counters[area] += 1
            
            for i in range(area_counters[area], num_servidores):
                funcao = area
                if area == 'TAKE':
                    funcao = "Fotografo" if i == 0 else "Suporte"
                
                voluntario = None
                for v in area_pool:
                    if v not in allocated_for_day:
                        voluntario = v
                        break
                
                if voluntario:
                    allocated_for_day.add(voluntario)
                    shifts_count[voluntario] = shifts_count.get(voluntario, 0) + 1
                    area_pool.remove(voluntario)
                else:
                    voluntario = "Não designado"
                
                escala_final_slots.append({
                    "Data": coluna_data,
                    "Funcao": funcao,
                    "Voluntario": voluntario
                })
                
                area_counters[area] += 1

    return escala_final_slots, available_servers_per_day, None

def ler_planilha(filepath):
    """Lê um arquivo .xlsx e retorna um DataFrame do pandas."""
    try:
        df = pd.read_excel(filepath)
        df.columns = df.columns.str.upper().str.strip()
        return df, None
    except FileNotFoundError:
        return None, "Arquivo não encontrado. Verifique o caminho do arquivo."
    except Exception as e:
        return None, f"Erro ao ler o arquivo: {e}"