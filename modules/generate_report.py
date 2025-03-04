from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os
import sys

def generate_report(target):
    report_dir = f"logs/{target}/report"

    if not os.path.exists(report_dir):
        print(f"[-] Error: The folder {report_dir} does not exist.")
        return

    output_path = f"reports/{target}.pdf"

    # Delete the file if it already exists
    if os.path.exists(output_path):
        os.remove(output_path)

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []

    # Add title with target and date/time
    styles = getSampleStyleSheet()
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    titulo = f"Report for {target} - {fecha_hora}"
    elements.append(Paragraph(titulo, styles['Title']))
    elements.append(Spacer(1, 12))

    try:
        for filename in os.listdir(report_dir):
            filepath = os.path.join(report_dir, filename)
            if os.path.isfile(filepath):
                if filename == "nmap.txt":
                    elements.append(Paragraph("Open services", styles['Heading2']))
                    elements.append(Spacer(1, 8))
                    elements.append(create_nmap_table(filepath))
                    elements.append(Spacer(1, 24))
                    break

        elements.append(Paragraph("Vulnerabilities", styles['Heading2']))
        elements.append(Spacer(1, 8))
        for filename in sorted(os.listdir(report_dir)):
            filepath = os.path.join(report_dir, filename)
            if os.path.isfile(filepath):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    elements.append(Paragraph("Website screenshot", styles['Heading3']))
                    elements.append(Spacer(1, 8))
                    elements.append(Image(filepath, width=400, height=300))
                    elements.append(Spacer(1, 12))
                elif filename != "nmap.txt":
                    elements.extend(create_text_paragraph(filepath))
    except Exception as e:
        print(f"[-] Error generating report: {e}")
        return

    try:
        doc.build(elements)
        print(f"[+] Report generated: {output_path}")
    except Exception as e:
        print(f"[-] Error saving report: {e}")

def create_nmap_table(filepath):
    data = [["Port", "State", "Service", "Version"]]
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            if "open" in line:
                parts = line.split()
                port = parts[0]
                state = parts[1]
                service = parts[2]
                version = " ".join(parts[3:])  # Join the remaining parts as version
                data.append([port, state, service, version])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    return table

def create_text_paragraph(filepath):
    styles = getSampleStyleSheet()
    content = ""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            content += f"{line.strip()}<br/>"
    paragraph = Paragraph(content, styles['Normal'])
    return [paragraph, Spacer(1, 12)]

def run_generate_report(target):
    generate_report(target)

# main
if __name__ == "__main__":
    target = sys.argv[1]
    run_generate_report(target)
