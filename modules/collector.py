import os
from datetime import datetime
from modules.docker_utils import run_command
from modules.report import generate_report


def save_output(path, content):
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def collect_evidence(container_id, container_name):
    """
    Recoge evidencias básicas de un contenedor Docker.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_dir = f"evidence/{container_name}_{timestamp}"

    os.makedirs(evidence_dir, exist_ok=True)

    print(f"\n[+] Carpeta de evidencias creada: {evidence_dir}")

    commands = {
        "inspect.json": f"docker inspect {container_id}",
        "logs.txt": f"docker logs {container_id}",
        "diff.txt": f"docker diff {container_id}",
        "top.txt": f"docker top {container_id}",
        "stats.txt": f"docker stats {container_id} --no-stream"
    }

    collected_files = []

    for filename, command in commands.items():
        print(f"[+] Ejecutando: {command}")

        stdout, stderr = run_command(command)

        output_path = os.path.join(evidence_dir, filename)

        if stderr:
            content = f"ERROR:\n{stderr}\n\nOUTPUT:\n{stdout}"
        else:
            content = stdout

        save_output(output_path, content)
        collected_files.append(filename)

    generate_report(evidence_dir, container_id, container_name, collected_files)

    print("\n[+] Recolección finalizada correctamente.")