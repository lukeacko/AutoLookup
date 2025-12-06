import os

from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress
from rich.table import Table as RichTable

from api import get_vin_data, get_recall_data, validate_vin, retry, VINDataError
from historyUtils import save_vin_lookup, get_cached_vin
from manageHistory import manage_history
from exports import export_batch_txt, export_batch_pdf, export_batch_excel, export_document, export_pdf, export_comparison_txt, export_comparison_pdf, export_comparison_excel
from display import print_vin_data, show_history, show_comparison, show_recall_table
from log import logger

## Input fields / prompts ##
def batch_vin_prompt():
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
            cached_data = get_cached_vin(vin)
            if cached_data:
                print(f"[green]Using cached data for VIN: {vin}[/green]")
                data = cached_data
                all_results.append({"vin": vin, "data": data})
                progress.update(task, advance=1)
                continue
            else:
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
        cached_data = get_cached_vin(vin)
        if cached_data:
            print(f"[green]Using cached data for VIN: {vin}[/green]")
            data = cached_data
        else:
            try:
                data = retry(lambda: get_vin_data(vin), attempts=3, delay=2, backoff=2, exceptions=(Exception,))
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

def compare_vins_prompt():
    vin1 = Prompt.ask("[bold yellow]Enter first VIN[/bold yellow]").strip()
    vin2 = Prompt.ask("[bold yellow]Enter second VIN[/bold yellow]").strip()

    # Validate
    try:
        vin1 = validate_vin(vin1)
        vin2 = validate_vin(vin2)
    except VINDataError as e:
        print(f"[red]Invalid VIN:[/red] {e}")
        return compare_vins_prompt()

    # Fetch data from cache or API
    data1 = get_cached_vin(vin1) or retry(lambda: get_vin_data(vin1), attempts=3)
    data2 = get_cached_vin(vin2) or retry(lambda: get_vin_data(vin2), attempts=3)

    # Save to history/cache
    save_vin_lookup(data1)
    save_vin_lookup(data2)

    show_comparison(vin1, data1, vin2, data2)
    # Export option
    export_choice = Prompt.ask("[bold yellow]Export comparison? TXT (T) / PDF (P) / Excel (E) / Skip (S)[/bold yellow]").strip().upper()
    if export_choice == 'T':
        export_comparison_txt(data1, data2, vin1, vin2)
    elif export_choice == 'P':
        export_comparison_pdf(data1,data2, vin1, vin2)
    elif export_choice == 'E':
        export_comparison_excel(data1, data2, vin1, vin2)

## Input sections / menus ##
def after_lookup(vin: str, data: dict):
    while True:
        menu_text = """
        [bold cyan]Export TXT[/bold cyan]  - Press [bold]D[/bold]
        [bold cyan]Export PDF[/bold cyan]  - Press [bold]P[/bold]
        [bold cyan]Check Recalls[/bold cyan] - Press [bold]R[/bold]
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
            return initOptions()
        elif choice == 'R':
            recalls = retry(lambda: get_recall_data(vin), attempts=3, delay=2, backoff=2, exceptions=(Exception,))
            show_recall_table(vin, recalls)
        elif choice == 'E':
            print("[green]Exiting VIN CLI. Goodbye![/green]")
            exit()

        else:
            print("[red]Invalid choice. Please try again.[/red]")

def initOptions():
    while True:
        options_text = """
        [bold cyan]New Lookup[/bold cyan] - Press [bold]N[/bold]
        [bold cyan]Batch Lookup[/bold cyan] - Press [bold]B[/bold]

        [bold cyan]Compare VINs[/bold cyan] - Press [bold]C[/bold]

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
        elif choice == 'C':
            compare_vins_prompt()
        elif choice == 'B':
            batch_vin_prompt()
        elif choice == 'M':
            manage_history()
        elif choice == 'E':
            print("[green]Exiting VIN CLI. Goodbye![/green]")
            exit()
        else:
            print("[red]Invalid choice. Please try again.[/red]")
