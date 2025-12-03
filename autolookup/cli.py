import os
import time
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.prompt import Prompt
from rich.progress import Progress

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table as PDFTable,
    TableStyle,
)

from api import get_vin_data, validate_vin, retry, VINDataError

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

### History manager functions ###
HISTORY_PATH = os.path.join(os.getcwd(), "autolookup_history.json")

def save_vin_lookup(data):
    history = load_history()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "vin": data.get("vin"),
        "data": data
    }

    history.append(entry)
    save_history(history)
def load_history():
    if not os.path.exists(HISTORY_PATH):
        logger.info("History file not found. Creating new one.")
        print("[yellow]No history file found. A new one will be created upon first save.[/yellow]")
        return []

    try:
        with open(HISTORY_PATH, "r") as f:
            content = f.read().strip()

            if not content:
                logger.warning("History file is empty.")
                return []

            return json.loads(content)

    except json.JSONDecodeError as e:
        logger.error(f"History file is corrupted: {e}")
        print("[red]History file is corrupted. Starting with an empty history.[/red]")
        return []

    except Exception as e:
        logger.exception("Unexpected error while loading history:")
        print(f"[red]Unexpected error loading history: {e}[/red]")
        return []   
def save_history(history):
    try:
        with open(HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=2)
        logger.info("History saved successfully.")
    except Exception as e:
        logger.exception("Failed to save VIN history:")
        print(f"[red]Failed to save to history: {e}[/red]")


### CLI Functions ###
console = Console()

# Prints welcome message
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

# Batch VIN lookup function
def batch_vin_lookup():
    file_path = Prompt.ask("[bold yellow]Enter the path to the VIN file[/bold yellow]").strip()
    logger.info(f"Batch lookup started using file: {file_path}")
    if not os.path.exists(file_path):
        print(f"[red]File not found: {file_path}[/red]")
        return

    with open(file_path, "r") as f:
        vins = [line.strip() for line in f.readlines() if line.strip()]
        
    if not vins:
        print("[red]No VINs found in the file.[/red]")
        return

    all_results = []
    failed_vins = []

    with Progress() as progress:
        task = progress.add_task("[cyan]Processing VINs...", total=len(vins))

        for vin in vins:
            try:
                vin = validate_vin(vin)
                data = retry(lambda: get_vin_data(vin), attempts=3, delay=2, backoff=2, exceptions=(Exception,))
                print_vin_data(vin, data)
                save_vin_lookup(data)
                all_results.append({"vin": vin, "data": data})
            except VINDataError as e:
                print(f"[red]Invalid VIN {vin}: {e}[/red]")
                logger.warning(f"Invalid VIN during batch lookup: {vin} - {e}")
                failed_vins.append(vin)
            except Exception as e:
                print(f"[red]Error fetching data for {vin}: {e}[/red]")
                logger.error(f"Error fetching data for VIN {vin}: {e}")
                failed_vins.append(vin)

            progress.update(task, advance=1)

    print(f"\n[bold green]Batch lookup completed![/bold green] {len(all_results)} successful, {len(failed_vins)} failed.\n")
    logger.info(f"Batch lookup complete. Success: {len(all_results)}, Failed: {len(failed_vins)}")

    # Ask user to export all results
    export_choice = Prompt.ask("[bold yellow]Export all results? TXT (T) / PDF (P) / Skip (S)[/bold yellow]").strip().upper()

    if export_choice == 'T':
        filename = f"batch_vin_lookup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            for entry in all_results:
                f.write(f"VIN: {entry['vin']}\n")
                for key, value in entry['data'].items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
        print(f"[green]All results exported to {filename}[/green]")

    elif export_choice == 'P':
        filename = f"batch_vin_lookup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table as PDFTable, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"<b>Batch VIN Lookup Report</b>", styles["Title"]))
        story.append(Spacer(1, 12))
        for entry in all_results:
            vin = entry['vin']
            data = entry['data']
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
            story.append(Paragraph(f"<b>VIN: {vin}</b>", styles["Heading3"]))
            story.append(table)
            story.append(Spacer(1, 12))

        doc.build(story)
        print(f"[green]All results exported to {filename}[/green]")

    else:
        print("[yellow]Export skipped.[/yellow]")

    if failed_vins:
        print("[red]The following VINs failed:[/red]")
        for vin in failed_vins:
            print(f" - {vin}")

# Show VIN history 
def show_history():
    history = load_history()
    if not history:
        print("[yellow]No VIN history found.[/yellow]")
        return

    table = RichTable(show_header=True, header_style="bold cyan")
    table.add_column("No.", style="cyan", width=4)
    table.add_column("VIN", style="magenta")
    table.add_column("Make", style="green")
    table.add_column("Model", style="green")
    table.add_column("Year", style="green")
    table.add_column("Date & Time", style="yellow")

    for idx, entry in enumerate(history, start=1):
        vin = entry.get("vin") or "N/A"
        data = entry.get("data") or {}
        make = data.get("brand") or data.get("make") or "N/A"
        model = data.get("model") or "N/A"
        year = str(data.get("year") or "N/A")
        timestamp = entry.get("timestamp") or "N/A"

        # Optionally format timestamp nicely
        try:
            timestamp = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

        table.add_row(str(idx), vin, make, model, year, timestamp)

    print(Panel(table, title="[bold cyan]VIN Lookup History[/bold cyan]", border_style="cyan"))  

# Show initial options
def initOptions():
    while True:
        options_text = """
        [bold cyan]New Lookup[/bold cyan] - Press [bold]N[/bold]
        [bold cyan]Batch Lookup[/bold cyan] - Press [bold]B[/bold]
        [bold cyan]View History[/bold cyan] - Press [bold]H[/bold]
        [bold red]Exit[/bold red] - Press [bold]E[/bold]
        """
        print(Panel.fit(options_text, border_style="cyan", padding=(1, 3)))
        choice = Prompt.ask("[bold yellow]Please enter your choice[/bold yellow]").strip().upper()
        if choice == 'N':
            vin_prompt()
        elif choice == 'H':
            show_history()
        elif choice == 'B':
            batch_vin_lookup()
        elif choice == 'E':
            print("[green]Exiting VIN CLI. Goodbye![/green]")
            exit()
        else:
            print("[red]Invalid choice. Please try again.[/red]")

#Enter VIN prompt and process
def vin_prompt():
       
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

        # Save to history
        save_vin_lookup(data)
        # Menu loop
        after_lookup(vin, data)  

# Post-lookup menu
def after_lookup(vin: str, data: dict):
    while True:
        menu_text = """
        [bold cyan]Export TXT[/bold cyan]  - Press [bold]D[/bold]
        [bold cyan]Export PDF[/bold cyan]  - Press [bold]P[/bold]
        [bold cyan]Show data again[/bold cyan] - Press [bold]S[/bold]
        [bold green]New Lookup / Main menu[/bold green] - Press [bold]N[/bold]
        [bold red]Exit[/bold red] - Press [bold]E[/bold]
        """
        print(Panel.fit(menu_text, border_style="white", padding=(1, 3)))

        choice = Prompt.ask("[bold yellow]Please enter your choice[/bold yellow]").strip().upper()

        if choice == 'D':
            export_document(vin, data)

        elif choice == 'P':
            export_pdf(vin, data)

        elif choice == 'S':
            print_vin_data(vin, data)   

        elif choice == 'N':
            return main(firstUse=False)

        elif choice == 'E':
            print("[green]Exiting VIN CLI. Goodbye![/green]")
            exit()

        else:
            print("[red]Invalid choice. Please try again.[/red]")

### Main Function ###
def main(firstUse=True):
    if firstUse:
        show_welcome()

    while True:
        initOptions()

    
if __name__ == "__main__":
    try:
        main(firstUse=True)
    except Exception as e:  
        logger.exception("Unhandled exception caused program crash:")
        print("\n[red]A critical error has occurred. Check vin_cli.log for details.[/red]")