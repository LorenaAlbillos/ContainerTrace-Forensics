import os
import json
import streamlit as st

from modules.docker_utils import list_containers
from modules.collector import collect_evidence


EVIDENCE_DIR = "evidence"


def get_evidence_cases():
    """
    Obtiene las carpetas de evidencias existentes.
    """
    if not os.path.exists(EVIDENCE_DIR):
        return []

    cases = []

    for item in os.listdir(EVIDENCE_DIR):
        path = os.path.join(EVIDENCE_DIR, item)

        if os.path.isdir(path):
            cases.append(item)

    return sorted(cases, reverse=True)


def read_file(path):
    """
    Lee archivos de texto generados como evidencia.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as file:
            return file.read()
    except Exception as e:
        return f"Error leyendo el archivo: {e}"


def read_json(path):
    """
    Lee archivos JSON generados como evidencia.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        return {"error": str(e)}


def show_evidence_file(case_path, filename):
    """
    Muestra una evidencia concreta en pantalla.
    """
    file_path = os.path.join(case_path, filename)

    if not os.path.exists(file_path):
        st.warning(f"No se ha encontrado el archivo {filename}")
        return

    st.subheader(filename)

    if filename.endswith(".json"):
        data = read_json(file_path)
        st.json(data)
    else:
        content = read_file(file_path)
        st.code(content)


def show_case_summary(case_path):
    """
    Muestra un resumen inicial del caso.
    """
    report_path = os.path.join(case_path, "report.txt")

    st.subheader("Resumen del caso")

    if os.path.exists(report_path):
        report_content = read_file(report_path)
        st.text_area("Informe generado", report_content, height=220)
    else:
        st.info("Este caso no contiene report.txt")


def acquisition_panel():
    """
    Panel lateral para lanzar una nueva adquisición.
    """
    st.sidebar.header("Nueva adquisición")

    try:
        containers = list_containers()
    except Exception as e:
        st.sidebar.error(f"Error obteniendo contenedores: {e}")
        return

    if not containers:
        st.sidebar.warning("No se han encontrado contenedores Docker.")
        return

    container_options = {}

    for container in containers:
        label = f"{container['name']} | {container['id']} | {container['status']}"
        container_options[label] = container

    selected_label = st.sidebar.selectbox(
        "Selecciona un contenedor",
        list(container_options.keys())
    )

    selected_container = container_options[selected_label]

    if st.sidebar.button("Recolectar evidencias"):
        with st.spinner("Recolectando evidencias del contenedor..."):
            collect_evidence(
                selected_container["id"],
                selected_container["name"]
            )

        st.success("Evidencias recolectadas correctamente.")
        st.rerun()


def evidence_viewer():
    """
    Visor principal de evidencias.
    """
    cases = get_evidence_cases()

    st.header("Visor de evidencias")

    if not cases:
        st.warning("Todavía no hay evidencias generadas.")
        return

    selected_case = st.selectbox(
        "Selecciona un caso de evidencias",
        cases
    )

    case_path = os.path.join(EVIDENCE_DIR, selected_case)

    st.markdown("---")
    show_case_summary(case_path)
    st.markdown("---")

    tabs = st.tabs([
        "Inspect",
        "Logs",
        "Diff",
        "Procesos",
        "Stats",
        "Informe"
    ])

    with tabs[0]:
        show_evidence_file(case_path, "inspect.json")

    with tabs[1]:
        show_evidence_file(case_path, "logs.txt")

    with tabs[2]:
        show_evidence_file(case_path, "diff.txt")

    with tabs[3]:
        show_evidence_file(case_path, "top.txt")

    with tabs[4]:
        show_evidence_file(case_path, "stats.txt")

    with tabs[5]:
        show_evidence_file(case_path, "report.txt")


def main():
    st.set_page_config(
        page_title="ContainerTrace Forensics",
        page_icon="assets/whale_skeleton.png",
        layout="wide"
    )

    st.image("assets/whale_skeleton.png", width=160)

    st.title("ContainerTrace Forensics")
    st.markdown(
        "Aplicación para la adquisición y visualización de evidencias "
        "forenses en contenedores Docker."
    )

    acquisition_panel()

    st.sidebar.markdown("---")
    st.sidebar.info(
        "La herramienta permite seleccionar un contenedor Docker, "
        "extraer evidencias y visualizarlas de forma estructurada."
    )

    evidence_viewer()


if __name__ == "__main__":
    main()