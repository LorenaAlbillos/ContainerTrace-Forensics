import subprocess


def run_command(command):
    """
    Ejecuta un comando del sistema y devuelve su salida.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)


def list_containers():
    """
    Lista todos los contenedores Docker, estén activos o detenidos.
    """
    command = "docker ps -a --format '{{.ID}}|{{.Names}}|{{.Status}}'"
    stdout, stderr = run_command(command)

    containers = []

    if stderr:
        print(f"[!] Error ejecutando Docker: {stderr}")
        return containers

    for line in stdout.strip().split("\n"):
        if line:
            parts = line.split("|")
            containers.append({
                "id": parts[0],
                "name": parts[1],
                "status": parts[2]
            })

    return containers