import os
import json
import hashlib
import stat
import zipfile
from datetime import datetime
from modules.docker_utils import run_command
from modules.report import generate_html_report


def save_output(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def calculate_sha256(path):
    sha256 = hashlib.sha256()

    with open(path, "rb") as file:
        for block in iter(lambda: file.read(4096), b""):
            sha256.update(block)

    return sha256.hexdigest()


def make_read_only(path):
    """
    Marca el archivo como solo lectura.
    No lo hace imposible de modificar, pero evita cambios accidentales.
    """
    os.chmod(path, stat.S_IREAD)


def create_case_zip(evidence_dir):
    zip_path = os.path.join(evidence_dir, "case_archive.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(evidence_dir):
            for file in files:
                file_path = os.path.join(root, file)

                if file_path == zip_path:
                    continue

                relative_path = os.path.relpath(file_path, evidence_dir)
                zip_file.write(file_path, relative_path)

    make_read_only(zip_path)
    return zip_path


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

    evidence_files = []

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
        save_output(output_path, evidence_data)
        evidence_files.append(output_path)

    hashes = {}

    for file_path in evidence_files:
        file_hash = calculate_sha256(file_path)
        hashes[os.path.basename(file_path)] = {
            "sha256": file_hash
        }

    hashes_path = os.path.join(evidence_dir, "hashes.json")
    save_output(hashes_path, hashes)

    chain_of_custody = {
        "case_name": f"{container_name}_{timestamp}",
        "container_name": container_name,
        "container_id": container_id,
        "acquisition_time": datetime.now().isoformat(),
        "tool": "ContainerTrace Forensics",
        "method": "Docker native commands",
        "integrity_algorithm": "SHA256",
        "evidence_format": "JSON",
        "observations": "Evidence files were exported in structured JSON format and marked as read-only after acquisition."
    }

    custody_path = os.path.join(evidence_dir, "chain_of_custody.json")
    save_output(custody_path, chain_of_custody)

    report_path = generate_html_report(
        evidence_dir=evidence_dir,
        container_id=container_id,
        container_name=container_name,
        hashes=hashes
    )

    all_files = evidence_files + [hashes_path, custody_path, report_path]

    for file_path in all_files:
        make_read_only(file_path)

    create_case_zip(evidence_dir)

    print("\n[+] Recolección finalizada correctamente.")
    return evidence_dir