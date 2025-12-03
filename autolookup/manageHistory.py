from exports import (export_history_to_excel, export_history_to_txt, export_history_to_pdf)
from historyUtils import load_history, save_history
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
from display import show_history
from log import logger

# Delete history entry
def delete_history_entry():
    history = load_history()
        
    if not history:
        print("[yellow]No history to delete.[/yellow]")
        logger.info("No history available for deletion.")
        return

    entry_no = Prompt.ask("[bold yellow]Enter the entry number to delete[/bold yellow]").strip()
    try:
        entry_idx = int(entry_no) - 1
        if 0 <= entry_idx < len(history):
            deleted_entry = history.pop(entry_idx)
            save_history(history)
            print(f"[green]Deleted entry for VIN: {deleted_entry.get('vin')}[/green]")
            logger.info(f"Deleted history entry for VIN: {deleted_entry.get('vin')}")
        else:
            print("[red]Invalid entry number.[/red]")
    except ValueError:
        print("[red]Please enter a valid number.[/red]")

# Clear all history after confirmation
def clear_history():
    confirm = Prompt.ask("[bold red]Are you sure you want to clear all history? (Y/N)[/bold red]").strip().upper()
    if confirm == 'Y':
        save_history([])
        logger.info("All history cleared by user.")
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
           