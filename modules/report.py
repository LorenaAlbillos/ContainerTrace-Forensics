import os
from datetime import datetime


def generate_report(evidence_dir, container_id, container_name, files):
    """
    Genera un informe básico de la adquisición forense.
    """

    report_path = os.path.join(evidence_dir, "report.txt")

    with open(report_path, "w", encoding="utf-8") as report:
        report.write("INFORME FORENSE DE CONTENEDOR DOCKER\n")
        report.write("====================================\n\n")

        report.write(f"Fecha de adquisición: {datetime.now()}\n")
        report.write(f"Nombre del contenedor: {container_name}\n")
        report.write(f"ID del contenedor: {container_id}\n\n")

        report.write("Evidencias recogidas:\n")

        for file in files:
            report.write(f"- {file}\n")

        report.write("\nObservaciones:\n")
        report.write("Las evidencias han sido obtenidas mediante comandos Docker locales.\n")
        report.write("Esta versión inicial no realiza todavía cálculo de hashes ni cadena de custodia.\n")