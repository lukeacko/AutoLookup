import requests
import time
from rich.spinner import Spinner
from rich.live import Live
from rich.console import Console
from rich import print
VIN_API_URL = ("https://db.vin/api/v1/vin/{vin}")

class VINDataError(Exception):
    pass


### Retry Logic ####
def retry(func, attempts=3, delay=1, backoff=2, exceptions=(Exception)):
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except exceptions as e:
            if attempt == attempts:
                # Last attempt → re-raise
                raise
            print(f"[yellow]Attempt {attempt}/{attempts} failed: {e}[/yellow]")

            with Live(refresh_per_second=10) as live:
                for remaining in range(delay, 0, -1):
                    live.update(
                        Spinner("dots", text=f"Retrying in {remaining} seconds...")
                    )
                    time.sleep(1)

            delay *= backoff

### Validation Logic ####
def validate_vin(vin: str):
    vin = vin.strip().upper()

    if len(vin) != 17:
        raise VINDataError("VIN must be exactly 17 characters.")

    if any(c in "IOQ" for c in vin):
        raise VINDataError("VIN cannot contain I, O, or Q.")

    return vin

### API Interaction ###
def get_vin_data(vin: str) -> dict:
    rich_console = Console()
    with rich_console.status("[bold green]Fetching VIN data...[/bold green]", spinner="dots"):
        response = requests.get(VIN_API_URL.format(vin=vin.strip()))
        if not response.ok:
            raise VINDataError(
                f"API error {response.status_code}: {response.text}"
            )
        return response.json()


