from rich import print
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.spinner import Spinner
from rich.console import Console
from rich.prompt import Prompt
from api import get_vin_data, VINDataError, validate_vin
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, TableStyle
from reportlab.platypus import Table as PDFTable, TableStyle
from reportlab.lib import colors

firstUse = True


def show_welcome():
    ascii_car = r"""
        ______
       /|_||_\`.__
      (   _    _ _\
       =`-(_)--(_)-'
    """

    welcome_text = f"""
{ascii_car}

[bold cyan]Welcome to VIN CLI![/bold cyan]

A fast and elegant tool for decoding vehicle VIN numbers.
"""
    print(Panel.fit(welcome_text, border_style="cyan", padding=(1, 3)))

def print_vin_data(vin: str):      
    console = Console()
    with console.status("[cyan]Fetching VIN data...[/cyan]", spinner="dots"):
        try:
            data = get_vin_data(vin)
        except VINDataError as e:
            print(f"[red]Error fetching VIN data:[/red] {e}")
            return main(firstUse=False)
        
    table = RichTable(show_header=True, header_style="bold cyan")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    for key, value in data.items():
        table.add_row(key, str(value))

    print(Panel(table, title=f"VIN Data for {vin}", border_style="cyan"))

def export_document(vin: str, data: dict):
    date = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{vin}_data.txt"
    with open(filename, 'w') as f:
        f.write(f"Date requested: {date}\n")
        for key, value in data.items():
            f.write(f"{key}: {value}\n")
            
    print(f"[green]VIN data exported to {filename}[/green]")
    return main(firstUse=False)

def export_pdf(vin: str, data: dict):
    filename = f"{vin}_data.pdf"

    # Create PDF document
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=18,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    title = f"<para alignment='center'><b>VIN Report: {vin}</b></para>"
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    # Timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Date Generated:</b> {timestamp}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # VIN Data Table
    table_data = [["Field", "Value"]]
    for key, value in data.items():
        table_data.append([key, str(value)])

    table = PDFTable(table_data, colWidths=[150, 350])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    story.append(table)

    # Build PDF
    doc.build(story)

    print(f"[green]PDF exported to {filename}[/green]")
    return main(firstUse=False)

def after_lookup(firstUse, vin:str, data:dict):
    firstUse = False

    menu_text = """
    [bold cyan]Export TXT[/bold cyan]  - Press [bold]D[/bold]
    [bold cyan]Export PDF[/bold cyan]  - Press [bold]P[/bold]
    [bold cyan]Show data again[/bold cyan] - Press [bold]S[/bold]
    [bold green]New Lookup[/bold green] - Press [bold]N[/bold]
    [bold red]Exit[/bold red] - Press [bold]E[/bold]
    """
    print(Panel.fit(menu_text, border_style="white", padding=(1, 3)))

    choice = input("Enter your choice): ").strip().upper()

    if choice == 'D':
        export_document(vin, data)
    elif choice == 'N':
        main(firstUse)
    elif choice == 'E':
        print("[green]Exiting VIN CLI. Goodbye![/green]")
        exit()
    elif choice == 'S':
        print_vin_data(vin)
        after_lookup(firstUse, vin, data)
    elif choice == 'P':
        export_pdf(vin, data)
    else:
        print("[red]Invalid choice. Please try again.[/red]")
        after_lookup(firstUse, vin, data)

def main(firstUse):
   if firstUse == True:
    show_welcome()

   vin = Prompt.ask("[bold yellow]Please enter VIN number[/bold yellow]")
   try:
       vin = validate_vin(vin)
       try:
            data = get_vin_data(vin)
       except VINDataError as e:
            print(f"[red]Error fetching VIN data:[/red] {e}")
            return main(firstUse=False)
   except VINDataError as e:
       print(f"[red]Invalid VIN:[/red] {e}")
       return main(firstUse=False)
  

   print_vin_data(vin)
   print("\n[green]Thank you for using VIN CLI![/green]")

   after_lookup(firstUse, vin, data)


main(firstUse=True)