from fpdf import FPDF
from ics import Calendar, Event
import datetime

def exportar_pdf(escala, filename):
    """
    Exports the schedule to a PDF file.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Simple table for now
    for i, row in escala.iterrows():
        pdf.cell(200, 10, txt=str(row.to_dict()), ln=True)

    pdf.output(filename)
    return True, f"Escala exportada para {filename}"

def exportar_ics(escala, filename):
    """
    Exports the schedule to an iCalendar (.ics) file.
    """
    c = Calendar()
    for i, row in escala.iterrows():
        e = Event()
        e.name = f"PibShift - {row.get('Função', '')}"
        # Assuming date is in dd/mm/yyyy format
        try:
            e.begin = datetime.datetime.strptime(row.get('Data', ''), '%d/%m/%Y')
        except (ValueError, TypeError):
            e.begin = datetime.datetime.now()
        c.events.add(e)
    
    with open(filename, 'w') as f:
        f.writelines(c)

    return True, f"Convite .ics gerado em {filename}"

def copiar_whatsapp(escala):
    """
    Formats the schedule as a string to be copied to WhatsApp.
    """
    whatsapp_string = "*Escala PibShift*\n\n"
    for i, row in escala.iterrows():
        whatsapp_string += f"*Data:* {row.get('Data', '')}\n"
        whatsapp_string += f"*Função:* {row.get('Função', '')}\n"
        whatsapp_string += f"*Voluntário:* {row.get('Voluntário', '')}\n\n"
    
    return whatsapp_string
