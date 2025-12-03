from log import logger
from historyUtils import load_history
from rich import print
from rich.table import Table as RichTable
from rich.panel import Panel


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