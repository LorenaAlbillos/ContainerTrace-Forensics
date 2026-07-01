from modules.docker_utils import list_containers
from modules.collector import collect_evidence


def main():
    print("===================================")
    print("     ContainerTrace Forensics")
    print("===================================")

    containers = list_containers()

    if not containers:
        print("[!] No se han encontrado contenedores Docker.")
        return

    print("\nContenedores disponibles:\n")

    for index, container in enumerate(containers, start=1):
        print(f"{index}. {container['name']} | {container['id']} | {container['status']}")

    try:
        option = int(input("\nSelecciona un contenedor: "))
        selected = containers[option - 1]
    except (ValueError, IndexError):
        print("[!] Opción no válida.")
        return

    print(f"\n[+] Contenedor seleccionado: {selected['name']}")
    collect_evidence(selected["id"], selected["name"])


if __name__ == "__main__":
    main()