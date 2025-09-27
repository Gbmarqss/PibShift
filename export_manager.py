from fpdf import FPDF
from ics import Calendar, Event
import datetime
import pandas as pd
import re

def exportar_pdf(escala_df, filename):
    """
    Exports the schedule to a PDF file with a table format.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Escala PibShift", 0, 1, 'C')
        pdf.ln(10)

        # Verificar se o DataFrame não está vazio
        if escala_df.empty:
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, "Nenhuma escala para exportar", 0, 1, 'C')
            pdf.output(filename)
            return True, "PDF criado (sem dados)"

        pdf.set_font("Arial", "B", 12)
        # Cabeçalhos da tabela
        col_widths = [40, 60, 80]  # Larguras das colunas
        headers = ["Data", "Função", "Voluntário"]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
        pdf.ln()

        pdf.set_font("Arial", size=10)
        # Linhas da tabela
        for index, row in escala_df.iterrows():
            data = str(row.get('Data', ''))[:20]  # Limitar tamanho
            funcao = str(row.get('Funcao', ''))[:25]
            voluntario = str(row.get('Voluntario', ''))[:30]
            
            pdf.cell(col_widths[0], 8, data, 1, 0, 'L')
            pdf.cell(col_widths[1], 8, funcao, 1, 0, 'L')
            pdf.cell(col_widths[2], 8, voluntario, 1, 1, 'L')

        pdf.output(filename)
        return True, f"PDF exportado com sucesso: {filename}"
    except Exception as e:
        return False, f"Erro ao gerar PDF: {str(e)}"

def exportar_ics(escala_df, filename):
    """
    Exports the schedule to an iCalendar (.ics) file.
    """
    try:
        if escala_df.empty:
            return False, "Nenhum evento para exportar"

        c = Calendar()
        eventos_criados = 0
        
        for i, row in escala_df.iterrows():
            if row.get('Voluntario') == 'Não designado':
                continue
                
            e = Event()
            e.name = f"PibShift - {row.get('Funcao', 'Serviço')}"
            e.description = f"Voluntário: {row.get('Voluntario', '')}"
            
            # Parse da data
            data_str = str(row.get('Data', ''))
            
            # Extrair data usando regex (DD/MM/YYYY ou DD/MM)
            match = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{4}))?', data_str)
            if match:
                dia, mes, ano = match.groups()
                ano = ano or datetime.datetime.now().year
                
                try:
                    event_date = datetime.datetime(int(ano), int(mes), int(dia), 19, 0)  # 19:00
                    e.begin = event_date
                    e.end = event_date.replace(hour=22, minute=0)  # 3 horas de duração
                    
                    c.events.add(e)
                    eventos_criados += 1
                except ValueError:
                    continue
        
        if eventos_criados == 0:
            return False, "Nenhum evento válido encontrado"
            
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(c.serialize_iter())

        return True, f"ICS exportado com {eventos_criados} eventos: {filename}"
    except Exception as e:
        return False, f"Erro ao gerar ICS: {str(e)}"

def copiar_whatsapp(escala_df):
    """
    Formats the schedule as a string to be copied to WhatsApp.
    """
    try:
        if escala_df.empty:
            return "📋 *Escala PibShift*\n\nNenhuma escala disponível"
        
        whatsapp_string = "📋 *Escala PibShift*\n\n"
        
        # Agrupar por data
        for data, grupo in escala_df.groupby('Data'):
            whatsapp_string += f"📅 *{data}*\n"
            for i, row in grupo.iterrows():
                funcao = row.get('Funcao', 'N/A')
                voluntario = row.get('Voluntario', 'Vazio')
                emoji = "✅" if voluntario != "Não designado" else "❌"
                whatsapp_string += f"{emoji} *{funcao}:* {voluntario}\n"
            whatsapp_string += "\n"
        
        return whatsapp_string
    except Exception as e:
        return f"❌ Erro ao formatar: {str(e)}"

def exportar_xlsx(escala_df, filename):
    """Exports the schedule to an Excel (.xlsx) file."""
    try:
        if escala_df.empty:
            # Criar DataFrame vazio com colunas
            df_to_export = pd.DataFrame(columns=['Data', 'Funcao', 'Voluntario'])
        else:
            df_to_export = escala_df[['Data', 'Funcao', 'Voluntario']].copy()
        
        df_to_export.to_excel(filename, index=False, engine='openpyxl')
        return True, f"Excel exportado: {filename}"
    except Exception as e:
        return False, f"Erro ao exportar Excel: {str(e)}"