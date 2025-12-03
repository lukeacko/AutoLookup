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
from datetime import datetime
import rich
from rich import print
import pandas as pd

from historyUtils import load_history
from log import logger



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
    

def export_batch_pdf(all_results: list):
    try:
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
    except Exception as e:
        logger.error(f"Error exporting batch PDF: {e}")
        print("[red]Error exporting batch PDF.[/red]")
def export_batch_txt(all_results: list):
    try:
        filename = f"batch_vin_lookup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            for entry in all_results:
                vin = entry['vin']
                data = entry['data']
                f.write(f"VIN: {vin}\n")
                for key, value in data.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
        print(f"[green]All results exported to {filename}[/green]")
    except Exception as e:
        logger.error(f"Error exporting batch TXT: {e}")
        print("[red]Error exporting batch TXT.[/red]")
def export_batch_excel(all_results: list):
    try:

        filename = f"batch_vin_lookup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        all_data = []
        for entry in all_results:
            vin = entry['vin']
            data = entry['data']
            data_row = {"VIN": vin}
            data_row.update(data)
            all_data.append(data_row)
        df = pd.DataFrame(all_data)
        df.to_excel(filename, index=False)
        print(f"[green]All results exported to {filename}[/green]")
    except Exception as e:
        logger.error(f"Error exporting batch Excel: {e}")
        print("[red]Error exporting batch Excel.[/red]")

def export_history_to_excel():
    history = load_history()
    if not history:
        print("[yellow]No history to export.[/yellow]")
        return

    try:
        filename = f"vin_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        all_data = []
        for entry in history:
            vin = entry.get("vin") or "N/A"
            data = entry.get("data") or {}
            data_row = {"VIN": vin}
            data_row.update(data)
            all_data.append(data_row)

        df = pd.DataFrame(all_data)
        df.to_excel(filename, index=False)
        print(f"[green]History exported to {filename}[/green]")
    except Exception as e:
        logger.error(f"Error exporting history to Excel: {e}")
        print("[red]Error exporting history to Excel.[/red]")
def export_history_to_txt():
    history = load_history()
    if not history:
        print("[yellow]No history to export.[/yellow]")
        return

    try:
        filename = f"vin_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            for entry in history:
                vin = entry.get("vin") or "N/A"
                data = entry.get("data") or {}
                f.write(f"VIN: {vin}\n")
                for key, value in data.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
        print(f"[green]History exported to {filename}[/green]")
    except Exception as e:
        logger.error(f"Error exporting history to TXT: {e}")
        print("[red]Error exporting history to TXT.[/red]")
def export_history_to_pdf():
    history = load_history()
    if not history:
        print("[yellow]No history to export.[/yellow]")
        return

    try:
        filename = f"vin_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table as PDFTable, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"<b>VIN History Report</b>", styles["Title"]))
        story.append(Spacer(1, 12))
        for entry in history:
            vin = entry.get("vin") or "N/A"
            data = entry.get("data") or {}
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
        print(f"[green]History exported to {filename}[/green]")
    except Exception as e:
        logger.error(f"Error exporting history to PDF: {e}")
        print("[red]Error exporting history to PDF.[/red]")
    