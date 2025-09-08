import datetime

def format_date(date_str):
    """
    Formats a date string from 'dd/mm/yyyy' to 'Day, dd/mm/yyyy'.
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y').date()
        return date_obj.strftime('%A, %d/%m/%Y')
    except (ValueError, TypeError):
        return date_str
