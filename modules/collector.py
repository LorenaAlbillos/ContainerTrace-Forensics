import os
import json
import hashlib
import subprocess
from datetime import datetime
from modules.docker_utils import run_command
from modules.report import generate_html_report


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as file:
        for block in iter(lambda: file.read(4096), b""):
            sha256_hash.update(block)

    return sha256_hash.hexdigest()
    
def export_container_filesystem(container_id, evidence_dir):
    export_path = os.path.join(evidence_dir, "filesystem.tar")

    command = [
        "docker",
        "export",
        container_id,
        "-o",
        export_path
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    return export_path, result.stderr

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
        
    filesystem_path, filesystem_error = export_container_filesystem(
        container_id,
        evidence_dir
    )

    if filesystem_error:
        print(f"[!] Error exportando sistema de archivos: {filesystem_error}")
    else:
        collected_files.append("filesystem.tar")

    hashes = {}

    for filename in collected_files:
        file_path = os.path.join(evidence_dir, filename)

        if os.path.exists(file_path):
            hashes[filename] = {
                "sha256": calculate_sha256(file_path),
                "algorithm": "SHA256",
                "file": filename
            }

    hashes_path = os.path.join(evidence_dir, "hashes.json")
    
    chain_of_custody = {
        "case_name": f"{container_name}_{timestamp}",
        "container_name": container_name,
        "container_id": container_id,
        "acquisition_time": datetime.now().isoformat(),
        "tool": "ContainerTrace Forensics",
        "method": "Evidence acquisition using native Docker commands",
        "evidence_format": "JSON",
        "integrity_algorithm": "SHA256",
        "collected_files": collected_files,
        "observations": "Evidence generated in a controlled Docker forensic analysis environment."
    }

    custody_path = os.path.join(evidence_dir, "chain_of_custody.json")
    save_json(custody_path, chain_of_custody)
    collected_files.append("chain_of_custody.json")

    with open(hashes_path, "w", encoding="utf-8") as file:
        json.dump(hashes, file, indent=4, ensure_ascii=False)

    collected_files.append("hashes.json")

    generate_html_report(evidence_dir, container_id, container_name, collected_files)

    print("\n[+] Recolección finalizada correctamente.")
    return evidence_dir