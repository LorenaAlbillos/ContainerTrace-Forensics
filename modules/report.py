import os
from datetime import datetime


def generate_html_report(evidence_dir, container_id, container_name, hashes):
    report_path = os.path.join(evidence_dir, "forensic_report.html")

    rows = ""

    for filename, data in hashes.items():
        rows += f"""
        <tr>
            <td>{filename}</td>
            <td>{data["sha256"]}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>ContainerTrace Forensic Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                background-color: #f4f6f8;
                color: #222;
            }}

            .container {{
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}

            h1 {{
                color: #0b3d91;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}

            th, td {{
                border: 1px solid #ccc;
                padding: 10px;
                text-align: left;
                word-break: break-all;
            }}

            th {{
                background-color: #0b3d91;
                color: white;
            }}

            .note {{
                margin-top: 20px;
                padding: 15px;
                background-color: #eef3ff;
                border-left: 5px solid #0b3d91;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ContainerTrace Forensics Report</h1>

            <h2>Información general</h2>
            <p><strong>Fecha de adquisición:</strong> {datetime.now()}</p>
            <p><strong>Nombre del contenedor:</strong> {container_name}</p>
            <p><strong>ID del contenedor:</strong> {container_id}</p>
            <p><strong>Herramienta:</strong> ContainerTrace Forensics</p>

            <h2>Evidencias generadas</h2>
            <table>
                <tr>
                    <th>Archivo</th>
                    <th>SHA256</th>
                </tr>
                {rows}
            </table>

            <div class="note">
                <p>
                    Las evidencias han sido exportadas en formato JSON y se ha calculado
                    un hash SHA256 para cada archivo con el objetivo de verificar su integridad.
                    Los archivos han sido marcados como solo lectura tras la adquisición.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    with open(report_path, "w", encoding="utf-8") as file:
        file.write(html)

    return report_path