from rich import print
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.prompt import Prompt
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Table as PDFTable, TableStyle
from reportlab.lib import colors
import logging
from logging.handlers import RotatingFileHandler
from api import get_vin_data, validate_vin, retry, VINDataError
import time


### Logging Setup ###
logger = logging.getLogger("vin_cli")
logger.setLevel(logging.DEBUG)

# Log file rotates at 1MB, keeps 5 backups
handler = RotatingFileHandler("vin_cli.log", maxBytes=1_000_000, backupCount=5)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)

logger.addHandler(handler)

                    
### Welcome Function ###
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

### Output Function ###
def print_vin_data(vin: str, data: dict):
    try:
        table = RichTable(show_header=True, header_style="bold cyan")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        for key, value in data.items():
            table.add_row(key, str(value))

        print(Panel(table, title=f"VIN Data for {vin}", border_style="cyan"))
    except Exception as e:
        logger.error(f"Error displaying VIN data: {e}")
        print("[red]Error displaying VIN data.[/red]")
        return

### Export Functions ###
def export_document(vin: str, data: dict):
    try:
        date = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"{vin}_data.txt"
        with open(filename, 'w') as f:
            f.write(f"Date requested: {date}\n")
            for key, value in data.items():
                f.write(f"{key}: {value}\n")
                
        print(f"[green]VIN data exported to {filename}[/green]")
    except Exception as e:
        logger.error(f"Error exporting VIN data to TXT: {e}")
        print("[red]Error exporting VIN data to TXT.[/red]")
        return
def export_pdf(vin: str, data: dict):
    filename = f"{vin}_data.pdf"

    try: 
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
        table_data = [["Data", "Value"]]
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
        return 
    except Exception as e:
        logger.error(f"Error exporting VIN data to PDF: {e}")
        print("[red]Error exporting VIN data to PDF.[/red]")
        return
### CLI Functions ###
def after_lookup(vin: str, data: dict):
    while True:
        menu_text = """
        [bold cyan]Export TXT[/bold cyan]  - Press [bold]D[/bold]
        [bold cyan]Export PDF[/bold cyan]  - Press [bold]P[/bold]
        [bold cyan]Show data again[/bold cyan] - Press [bold]S[/bold]
        [bold green]New Lookup[/bold green] - Press [bold]N[/bold]
        [bold red]Exit[/bold red] - Press [bold]E[/bold]
        """
        print(Panel.fit(menu_text, border_style="white", padding=(1, 3)))

        choice = input("Enter your choice: ").strip().upper()

        if choice == 'D':
            export_document(vin, data)

        elif choice == 'P':
            export_pdf(vin, data)

        elif choice == 'S':
            print_vin_data(vin, data)   

        elif choice == 'N':
            return

        elif choice == 'E':
            print("[green]Exiting VIN CLI. Goodbye![/green]")
            exit()

        else:
            print("[red]Invalid choice. Please try again.[/red]")

def main(firstUse=True):
    if firstUse:
        show_welcome()

    while True:
        vin = Prompt.ask("[bold yellow]Please enter VIN number[/bold yellow]")

        # Validate VIN
        
        try:
            vin = validate_vin(vin)
        except VINDataError as e:
            print(f"[red]Invalid VIN:[/red] {e}")
            continue

        # Fetch data once
        try:
            data = retry(lambda: get_vin_data(vin), attempts=3, delay=2, backoff=2, exceptions=(Exception))
            logger.info(f"User entered VIN: {vin}")
            logger.info(f"Data from VIN: {data}")
        except VINDataError as e:
            print(f"[red]Error fetching VIN data:[/red] {e}")
            continue
        except Exception as e:
            print(f"[red]Unexpected error occurred:[/red] {e}")
            continue

        # Display VIN data
        print_vin_data(vin, data)

        print("\n[green]Thank you for using VIN CLI![/green]")

        # Menu loop
        after_lookup(vin, data)
    
if __name__ == "__main__":
    main(firstUse=True)