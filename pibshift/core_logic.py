import re
import pandas as pd
import datetime
from collections import Counter

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

def extrair_nome_sobrenome(nome_completo):
    """
    Extrai o primeiro e o último nome de um nome completo.
    Se houver apenas um nome, retorna o próprio nome.
    Também reconhece apelidos para nomes específicos.
    """
    nome_lower = nome_completo.lower().strip()

    # Mapeamento de apelidos para nomes padronizados
    apelidos_para_nomes = {
        "gb marques": "Gabriel Marques",
        "lay": "Laysa",
        "layy": "Laysa",
    }

    # Verifica se o nome completo (em minúsculas) ou uma parte corresponde a um apelido
    for apelido, nome_padronizado in apelidos_para_nomes.items():
        if apelido in nome_lower:
            return nome_padronizado

    # Lógica original para extrair primeiro e último nome
    partes = nome_completo.split()
    return " ".join([partes[0], partes[-1]]) if len(partes) > 1 else partes[0]


def verifica_dias_consecutivos(escala, nome, data):
    """
    Verifica se um servidor trabalhará 3 ou mais dias consecutivos, incluindo a data atual.
    Retorna False se houver 3 ou mais dias consecutivos, True caso contrário.
    """
    dias_sequenciais = []
    for dia in escala:
        # Adicionado para garantir que dia é um dicionário e o valor é uma string
        if isinstance(dia, dict):
            for val in dia.values():
                if isinstance(val, str) and nome in val:
                    dias_sequenciais.append(dia.get('Data'))
                    break # Evita adicionar a mesma data múltiplas vezes

    dias_sequenciais.append(data)
    dias_sequenciais.sort()

    # Convertendo a lista para datetime objects para fácil comparação
    datas_dt = []
    # Usar um ano fixo (ex: 2000) para permitir a comparação de dias, ignorando o ano real
    fixed_year = 2000
    for dt_str in dias_sequenciais:
        if not dt_str: continue
        # Usar regex para encontrar o padrão DD/MM na string
        match = re.search(r'\b(\d{1,2}/\d{1,2})\b', dt_str)
        if match:
            date_part = match.group(1)
            try:
                # Adicionar o ano fixo e parsear
                full_date_str = f"{date_part}/{fixed_year}"
                datas_dt.append(datetime.datetime.strptime(full_date_str, '%d/%m/%Y').date())
            except ValueError:
                pass
        else:
            pass

    datas_dt.sort()

    count = 0
    for i in range(1, len(datas_dt)):
        if (datas_dt[i] - datas_dt[i-1]).days == 1:
            count += 1
        else:
            count = 0
        if count >= 3:
            return False
    return True

def verificar_conflitos(escala_df):
    """Verifica conflitos em uma escala e retorna um dicionário com os status."""
    conflitos = {}
    # Verificar voluntários duplicados no mesmo dia
    for data, group in escala_df.groupby('Data'):
        counts = group['Voluntário'].value_counts()
        conflitos_dia = counts[counts > 1].index.tolist()
        if conflitos_dia:
            conflitos[data] = conflitos_dia
    return conflitos

def gerar_rascunho(df):
    """Gera um rascunho de escala a partir de um DataFrame."""
    if 'ÁREA DE ATUAÇÃO' not in df.columns:
        return None, None, "A coluna 'ÁREA DE ATUAÇÃO' não foi encontrada."
    
    num_servidores_por_area = {
        'PRODUÇÃO': 1,
        'FILMAGEM': 3,
        'PROJEÇÃO': 1,
        'TAKE': 2,
    }

    shifts_count = {}
    max_shifts_per_person = 2
    priority_pair = ("Laysa", "Gabriel Marques")
    laysa_name, gabriel_name = priority_pair
    excluded_pair = ("Laysa", "Gabriel Nevile")

    colunas_datas = [col for col in df.columns if col not in ['CARIMBO DE DATA/HORA', 'ENDEREÇO DE E-MAIL', 'CELULAR (WHATSAPP)', 'NOME', 'ÁREA DE ATUAÇÃO']]
    
    escala_final = []
    available_servers_per_day = {}

    for coluna in colunas_datas:
        dia_df = df[df[coluna] == 'SIM']
        alocacao_dia = {'Data': coluna}
        
        daily_available_servers = {}
        for area_key in num_servidores_por_area.keys():
            servidores_disponiveis_raw_nomes = dia_df[dia_df['ÁREA DE ATUAÇÃO'].str.contains(area_key, case=False)]['NOME'].tolist()
            current_area_available = []
            for nome_servidor in servidores_disponiveis_raw_nomes:
                nome_normalizado = extrair_nome_sobrenome(nome_servidor)
                if shifts_count.get(nome_normalizado, 0) < max_shifts_per_person and \
                   verifica_dias_consecutivos(escala_final, nome_normalizado, coluna):
                    current_area_available.append(nome_normalizado)
            daily_available_servers[area_key] = current_area_available
        
        available_servers_per_day[coluna] = daily_available_servers

        if laysa_name in [s for sublist in daily_available_servers.values() for s in sublist]:
            for area_key in daily_available_servers:
                if excluded_pair[1] in daily_available_servers[area_key]:
                    daily_available_servers[area_key].remove(excluded_pair[1])
        elif excluded_pair[1] in [s for sublist in daily_available_servers.values() for s in sublist]:
            for area_key in daily_available_servers:
                if laysa_name in daily_available_servers[area_key]:
                    daily_available_servers[area_key].remove(laysa_name)

        allocated_for_day = set()
        temp_alocacao = {}

        laysa_can_be_filmag_cross = laysa_name in daily_available_servers.get('FILMAGEM', [])
        gabriel_can_be_prod_cross = gabriel_name in daily_available_servers.get('PRODUÇÃO', [])
        
        if laysa_can_be_filmag_cross and gabriel_can_be_prod_cross:
            temp_alocacao['FILMAGEM'] = [laysa_name]
            allocated_for_day.add(laysa_name)
            
            temp_alocacao['PRODUÇÃO'] = [gabriel_name]
            allocated_for_day.add(gabriel_name)

        for area, num_servidores in num_servidores_por_area.items():
            alocados = temp_alocacao.get(area, [])
            num_to_fill = num_servidores - len(alocados)

            if num_to_fill > 0:
                pool_disponivel = [s for s in daily_available_servers.get(area, []) if s not in allocated_for_day]
                novos_alocados = pool_disponivel[:num_to_fill]
                alocados.extend(novos_alocados)
                allocated_for_day.update(novos_alocados)
            
            temp_alocacao[area] = alocados

        for area, nomes in temp_alocacao.items():
            num_needed = num_servidores_por_area[area]
            if len(nomes) < num_needed:
                nomes.extend(['Não designado'] * (num_needed - len(nomes)))
            alocacao_dia[area] = '\n'.join(nomes)

        for nome in allocated_for_day:
            shifts_count[nome] = shifts_count.get(nome, 0) + 1

        escala_final.append(alocacao_dia)
    
    return escala_final, available_servers_per_day, None