import os
import json
import logging
from datetime import datetime
from log import logger


HISTORY_PATH = os.path.join(os.getcwd(), "autolookup_history.json")
## save VIN lookup to history ##
def save_vin_lookup(data):
    history = load_history()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "vin": data.get("vin"),
        "data": data
    }

    history.append(entry)
    save_history(history)
## load VIN history ##
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
## save VIN history ##
def save_history(history):
    try:
        with open(HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=2)
        logger.info("History saved successfully.")
    except Exception as e:
        logger.exception("Failed to save VIN history:")
        print(f"[red]Failed to save to history: {e}[/red]")
    history = load_history()
## get cached VIN data ##
def get_cached_vin(vin: str) -> dict | None:
    history = load_history()  # Your existing function
    for entry in reversed(history):  # Search latest first
        if entry.get("vin") == vin:
            print(f"[green]Found cached data for VIN: {vin}[/green]")
            logger.info(f"Using cached data for VIN: {vin}")
            return entry.get("data")
    return None


