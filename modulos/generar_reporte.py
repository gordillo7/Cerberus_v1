from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os
import sys

def generar_reporte(target):
    reporte_dir = f"logs/{target}/reporte"

    if not os.path.exists(reporte_dir):
        print(f"Error: La carpeta {reporte_dir} no existe.")
        return

    output_path = f"{reporte_dir}/{target}.pdf"

    # Eliminar el archivo si ya existe
    if os.path.exists(output_path):
        os.remove(output_path)

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []

    # Añadir título con target y fecha/hora
    styles = getSampleStyleSheet()
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    titulo = f"Reporte para {target} - {fecha_hora}"
    elements.append(Paragraph(titulo, styles['Title']))
    elements.append(Spacer(1, 12))

    try:
        for filename in os.listdir(reporte_dir):
            filepath = os.path.join(reporte_dir, filename)
            if os.path.isfile(filepath):
                if filename == "nmap.txt":
                    elements.append(Paragraph("Servicios abiertos", styles['Heading2']))
                    elements.append(Spacer(1, 8))
                    elements.append(create_nmap_table(filepath))
                    elements.append(Spacer(1, 24))
                    elements.append(Paragraph("Vulnerabilidades", styles['Heading2']))
                    elements.append(Spacer(1, 8))
                else:
                    elements.extend(create_text_paragraph(filepath))
    except Exception as e:
        print(f"Error al generar el reporte: {e}")
        return

    try:
        doc.build(elements)
        print(f"Reporte generado: {output_path}")
    except Exception as e:
        print(f"Error al guardar el reporte: {e}")

def create_nmap_table(filepath):
    data = [["Port", "State", "Service", "Version"]]
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            if "open" in line:
                parts = line.split()
                port = parts[0]
                state = parts[1]
                service = parts[2]
                version = " ".join(parts[3:])  # Unir el resto de las partes como versión
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
            content += line.strip() + "<br/>"
    paragraph = Paragraph(content, styles['Normal'])
    return [paragraph, Spacer(1, 12)]

# main
if __name__ == "__main__":
    target = sys.argv[1]
    generar_reporte(target)