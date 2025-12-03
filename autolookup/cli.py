import os
from datetime import datetime
from turtle import clear

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress

from api import get_vin_data, validate_vin, retry, VINDataError
from log import logger
from historyUtils import save_vin_lookup, load_history, save_history
from exports import (export_document,  export_pdf, export_batch_pdf, export_batch_txt, 
                     export_batch_excel, export_history_to_excel, export_history_to_txt, export_history_to_pdf)

from display import print_vin_data, show_welcome, show_history

console = Console()


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
    export_choice = Prompt.ask("[bold yellow]Export all results? TXT (T) / PDF (P) / EXCEL (E) / Skip (S)[/bold yellow]").strip().upper()

    if export_choice == 'T':
        export_batch_txt(all_results)
        return
    elif export_choice == 'P':
        export_batch_pdf(all_results)
        return
    elif export_choice == 'E':
        export_batch_excel(all_results)
        return
    else:
        print("[yellow]Export skipped.[/yellow]")

    if failed_vins:
        print("[red]The following VINs failed:[/red]")
        for vin in failed_vins:
            print(f" - {vin}")

# Delete history entry
def delete_history_entry():
    history = load_history()
        
    if not history:
        print("[yellow]No history to delete.[/yellow]")
        return

    entry_no = Prompt.ask("[bold yellow]Enter the entry number to delete[/bold yellow]").strip()
    try:
        entry_idx = int(entry_no) - 1
        if 0 <= entry_idx < len(history):
            deleted_entry = history.pop(entry_idx)
            save_history(history)
            print(f"[green]Deleted entry for VIN: {deleted_entry.get('vin')}[/green]")
        else:
            print("[red]Invalid entry number.[/red]")
    except ValueError:
        print("[red]Please enter a valid number.[/red]")

# Clear all history after confirmation
def clear_history():
    confirm = Prompt.ask("[bold red]Are you sure you want to clear all history? (Y/N)[/bold red]").strip().upper()
    if confirm == 'Y':
        save_history([])
        print("[green]All history cleared.[/green]")
    else:
        print("[yellow]Clear history cancelled.[/yellow]")

# Manage history (export/delete)
def manage_history():
     while True:
        options_text = """
        [bold cyan]View history[/bold cyan] - Press [bold]V[/bold]
        [bold cyan]Delete entry[/bold cyan] - Press [bold]D[/bold]
        [bold cyan]Clear all history[/bold cyan] - Press [bold]C[/bold]
        [bold green]Export to excel[/bold green] - Press [bold]E[/bold]
        [bold white]Export to .txt[/bold white] - Press [bold]T[/bold]
        [bold red]Export to pdf (export/delete) [/bold red] - Press [bold]P[/bold]

        [bold yellow]Back to Main Menu[/bold yellow] - Press [bold]B[/bold]
         
        """
        print(Panel.fit(options_text, border_style="cyan", padding=(1, 3)))
        choice = Prompt.ask("[bold yellow]Please enter your choice[/bold yellow]").strip().upper()

        if choice == 'V':
            show_history()
        elif choice == 'D':
            delete_history_entry()
        elif choice == 'C':
            clear_history()
        elif choice == 'E':
            export_history_to_excel()
        elif choice == 'T':
            export_history_to_txt()
        elif choice == 'P':
            export_history_to_pdf()
        elif choice == 'B':
            return
        else:
            print("[red]Invalid choice. Please try again.[/red]")
           
# Show initial options
def initOptions():
    while True:
        options_text = """
        [bold cyan]New Lookup[/bold cyan] - Press [bold]N[/bold]
        [bold cyan]Batch Lookup[/bold cyan] - Press [bold]B[/bold]

        [bold cyan]View History[/bold cyan] - Press [bold]H[/bold]
      [bold cyan]Manage history (export/delete) [/bold cyan] - Press [bold]M[/bold]

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
        elif choice == 'M':
            manage_history()
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