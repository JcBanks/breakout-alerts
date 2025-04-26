def format_percentage(value):
    return f"{value:.2f}%" if value is not None else "N/A"

def format_currency(value):
    return f"${value:,.2f}" if value is not None else "N/A"