from inputs import initOptions
from display import show_welcome
from log import logger

### Main Function ###
def main(firstUse=True):
    if firstUse:
        logger.info("Application started.")
        show_welcome()
    while True:
        initOptions()

    
if __name__ == "__main__":
    try:
        main(firstUse=True)    
    except Exception as e:  
        logger.exception("Unhandled exception caused program crash:")
        print("\n[red]A critical error has occurred. Check vin_cli.log for details.[/red]")