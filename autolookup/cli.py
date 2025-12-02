from rich import print
from rich.panel import Panel
from rich.table import Table
from rich.spinner import Spinner
from rich.console import Console
from rich.prompt import Prompt
from api import get_vin_data, VINDataError, validate_vin

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
        
    table = Table(title=f"VIN Data for {vin}")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    for key, value in data.items():
        table.add_row(key, str(value))

    print(table)

def document_export(vin: str, data: dict):
    date = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{vin}_data.txt"
    with open(filename, 'w') as f:
        f.write(f"Date requested: {date}\n")
        for key, value in data.items():
            f.write(f"{key}: {value}\n")
            
    print(f"[green]VIN data exported to {filename}[/green]")
    return main(firstUse=False)

def after_lookup(firstUse, vin:str, data:dict):
    firstUse = False

    text = """
            [bold cyan] Export to document [/bold cyan] Press [bold]D[/bold] to export the VIN data to a text document.
            [bold cyan] New Lookup [/bold cyan] Press[bold] N[/bold] to perform a new VIN lookup
            [bold red] Exit [/bold red] Press [bold]E[/bold[bold] B[/bold]to exit the application."""
    print(Panel.fit(text, border_style="white", padding=(1, 3)))

    choice = input("Enter your choice (D/N/E): ").strip().upper()

    if choice == 'D':
        print("[green]Exporting to document... (feature not implemented yet)[/green]")
        document_export(vin, data)
    elif choice == 'N':
        main(firstUse)
    elif choice == 'E':
        print("[green]Exiting VIN CLI. Goodbye![/green]")
        exit()
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


main(firstUse)