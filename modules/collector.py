import os
import json
from datetime import datetime
from modules.docker_utils import run_command
from modules.report import generate_html_report


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def collect_evidence(container_id, container_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_dir = f"evidence/{container_name}_{timestamp}"

    os.makedirs(evidence_dir, exist_ok=True)

    print(f"\n[+] Carpeta de evidencias creada: {evidence_dir}")

    commands = {
        "inspect.json": f"docker inspect {container_id}",
        "logs.json": f"docker logs {container_id}",
        "diff.json": f"docker diff {container_id}",
        "top.json": f"docker top {container_id}",
        "stats.json": f"docker stats {container_id} --no-stream"
    }

    collected_files = []

    for filename, command in commands.items():
        print(f"[+] Ejecutando: {command}")

        stdout, stderr = run_command(command)

        evidence_data = {
            "command": command,
            "container_id": container_id,
            "container_name": container_name,
            "acquisition_time": datetime.now().isoformat(),
            "stdout": stdout,
            "stderr": stderr
        }

        output_path = os.path.join(evidence_dir, filename)
        save_json(output_path, evidence_data)
        collected_files.append(filename)

    generate_html_report(evidence_dir, container_id, container_name, collected_files)

    print("\n[+] Recolección finalizada correctamente.")
    return evidence_dir