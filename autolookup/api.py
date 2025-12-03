import requests
from rich.spinner import Spinner
from rich.console import Console
API_URL = ("https://db.vin/api/v1/vin/{vin}")

class VINDataError(Exception):
    pass

def validate_vin(vin: str):
    vin = vin.strip().upper()

    if len(vin) != 17:
        raise VINDataError("VIN must be exactly 17 characters.")

    if any(c in "IOQ" for c in vin):
        raise VINDataError("VIN cannot contain I, O, or Q.")

    return vin

def get_vin_data(vin: str) -> dict:
    rich_console = Console()
    with rich_console.status("[bold green]Fetching VIN data...[/bold green]", spinner="dots"):
        response = requests.get(API_URL.format(vin=vin.strip()))
        if not response.ok:
            raise VINDataError(
                f"API error {response.status_code}: {response.text}"
            )
        return response.json()

