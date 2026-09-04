import os
import json
import tarfile
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

    elif filename.endswith(".html"):
        html_path = os.path.abspath(file_path)
        st.iframe(f"file://{html_path}", height=700)

    else:
        content = read_file(file_path)
        st.code(content)


def show_case_summary(case_path):
    """
    Muestra un resumen inicial del caso.
    """
    st.subheader("Resumen del caso")

    files = os.listdir(case_path)

    json_files = [f for f in files if f.endswith(".json")]
    tar_files = [f for f in files if f.endswith(".tar")]
    html_files = [f for f in files if f.endswith(".html")]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Archivos generados", len(files))
    col2.metric("Archivos JSON", len(json_files))
    col3.metric("Copias TAR", len(tar_files))
    col4.metric("Informes HTML", len(html_files))

    st.markdown("### Archivos del caso")

    for file in sorted(files):
        st.write(f"- `{file}`")

    if "filesystem.tar" in files:
        st.success("Copia del sistema de archivos generada correctamente.")

    if "hashes.json" in files:
        st.success("Archivo de hashes generado correctamente.")

    if "chain_of_custody.json" in files:
        st.success("Cadena de custodia generada correctamente.")

    if "forensic_report.html" in files:
        st.success("Informe HTML generado correctamente.")


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

    container_labels = list(container_options.keys())

    with st.sidebar.form("acquisition_form"):
        selected_label = st.selectbox(
            "Selecciona un contenedor",
            container_labels,
            key="selected_container_for_acquisition"
        )

        submitted = st.form_submit_button("Recolectar evidencias")

    if submitted:
        selected_container = container_options[selected_label]

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
        "Hashes",
        "Cadena de custodia",
        "Sistema de archivos",
        "Informe HTML"
    ])

    with tabs[0]:
        show_evidence_file(case_path, "inspect.json")

    with tabs[1]:
        show_evidence_file(case_path, "logs.json")

    with tabs[2]:
        show_evidence_file(case_path, "diff.json")

    with tabs[3]:
        show_evidence_file(case_path, "top.json")

    with tabs[4]:
        show_evidence_file(case_path, "stats.json")

    with tabs[5]:
        show_evidence_file(case_path, "hashes.json")

    with tabs[6]:
        show_evidence_file(case_path, "chain_of_custody.json")

    with tabs[7]:
        filesystem_browser(case_path)

    with tabs[8]:
        show_evidence_file(case_path, "forensic_report.html")


def show_file_from_tar(tar, selected_file):
    """
    Muestra el contenido de un archivo seleccionado dentro del filesystem.tar.
    """
    try:
        selected_member = tar.getmember(selected_file)
    except KeyError:
        st.error("No se ha encontrado el archivo seleccionado dentro del TAR.")
        return

    st.markdown("---")
    st.markdown("### Archivo seleccionado")

    st.json({
        "ruta": selected_member.name,
        "tamaño_bytes": selected_member.size,
        "modo": oct(selected_member.mode),
        "uid": selected_member.uid,
        "gid": selected_member.gid,
        "mtime": selected_member.mtime
    })

    if selected_member.size > 1024 * 1024:
        st.warning(
            "El archivo es demasiado grande para mostrarlo en pantalla. "
            "Se recomienda analizarlo externamente."
        )
        return

    extracted_file = tar.extractfile(selected_member)

    if extracted_file is None:
        st.warning("No se pudo leer el archivo seleccionado.")
        return

    content = extracted_file.read()

    try:
        decoded_content = content.decode("utf-8")
        st.markdown("### Contenido del archivo")
        st.code(decoded_content)
    except UnicodeDecodeError:
        st.markdown("### Vista hexadecimal parcial")
        st.code(content[:4096].hex())


def get_direct_children(members, current_dir):
    """
    Devuelve carpetas y archivos que cuelgan directamente de current_dir.
    """
    current_dir = current_dir.strip("/")
    prefix = "" if current_dir == "" else current_dir + "/"

    directories = set()
    files = []

    for member in members:
        path = member.name.strip("/")

        if not path:
            continue

        if not path.startswith(prefix):
            continue

        relative_path = path[len(prefix):]

        if not relative_path:
            continue

        parts = relative_path.split("/")

        if len(parts) > 1:
            directory_path = f"{current_dir}/{parts[0]}".strip("/")
            directories.add(directory_path)
        else:
            if member.isdir():
                directories.add(path)
            elif member.isfile():
                files.append(member)

    return sorted(directories), sorted(files, key=lambda x: x.name)


def toggle_directory(directory):
    """
    Abre o cierra una carpeta del árbol.
    """
    if "opened_fs_dirs" not in st.session_state:
        st.session_state["opened_fs_dirs"] = set()

    if directory in st.session_state["opened_fs_dirs"]:
        st.session_state["opened_fs_dirs"].remove(directory)
    else:
        st.session_state["opened_fs_dirs"].add(directory)


def render_windows_tree(tar, members, current_dir="", level=0, prefix=""):
    """
    Renderiza el sistema de archivos como árbol estilo explorador,
    usando caracteres de árbol en vez de desplazar los elementos con CSS.
    """
    if "opened_fs_dirs" not in st.session_state:
        st.session_state["opened_fs_dirs"] = set()

    if "selected_fs_file" not in st.session_state:
        st.session_state["selected_fs_file"] = None

    st.markdown(
        """
        <style>
        div[data-testid="stButton"] {
            margin-top: -8px;
            margin-bottom: -8px;
        }

        div[data-testid="stButton"] button {
            background: transparent;
            border: none;
            box-shadow: none;
            text-align: left;
            justify-content: flex-start;
            padding: 0px 4px;
            min-height: 24px;
            height: 24px;
            font-weight: normal;
            font-size: 15px;
            font-family: monospace;
        }

        div[data-testid="stButton"] button:hover {
            background-color: rgba(120, 120, 120, 0.12);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    directories, files = get_direct_children(members, current_dir)

    items = []

    for directory in directories:
        items.append(("directory", directory))

    for file_member in files:
        items.append(("file", file_member))

    for index, item in enumerate(items):
        is_last = index == len(items) - 1

        connector = "└── " if is_last else "├── "
        child_prefix = prefix + ("    " if is_last else "│   ")

        item_type, value = item

        if item_type == "directory":
            directory = value
            folder_name = os.path.basename(directory)
            is_open = directory in st.session_state["opened_fs_dirs"]

            arrow = "⌄" if is_open else "›"
            icon = "📂" if is_open else "📁"

            button_label = f"{prefix}{connector}{arrow} {icon} {folder_name}/"

            if st.button(button_label, key=f"toggle_dir_{directory}"):
                toggle_directory(directory)
                st.rerun()

            if is_open:
                render_windows_tree(
                    tar=tar,
                    members=members,
                    current_dir=directory,
                    level=level + 1,
                    prefix=child_prefix
                )

        else:
            file_member = value
            file_name = os.path.basename(file_member.name)
            file_path = file_member.name

            selected = st.session_state.get("selected_fs_file") == file_path
            selected_marker = "▶ " if selected else "  "

            button_label = f"{prefix}{connector}{selected_marker}📄 {file_name}"

            if st.button(button_label, key=f"view_file_{file_path}"):
                st.session_state["selected_fs_file"] = file_path
                st.rerun()


def filesystem_browser(case_path):
    """
    Permite navegar por la copia exportada del sistema de archivos del contenedor
    en forma de árbol tipo explorador, sin ejecutar comandos dentro del contenedor original.
    """
    st.subheader("Copia del sistema de archivos del contenedor")

    tar_path = os.path.join(case_path, "filesystem.tar")

    if not os.path.exists(tar_path):
        st.warning("No se ha encontrado el archivo filesystem.tar")
        return

    st.info(
        "Esta vista permite explorar una copia exportada del sistema de archivos "
        "del contenedor. No se ejecutan comandos dentro del contenedor original."
    )

    try:
        with tarfile.open(tar_path, "r") as tar:
            members = tar.getmembers()

            all_files = [member for member in members if member.isfile()]
            all_directories = [member for member in members if member.isdir()]

            col1, col2, col3 = st.columns(3)

            col1.metric("Archivos", len(all_files))
            col2.metric("Directorios", len(all_directories))
            col3.metric("Total elementos", len(members))

            st.markdown("---")

            view_mode = st.radio(
                "Modo de visualización",
                [
                    "Árbol de directorios",
                    "Buscar archivo"
                ],
                horizontal=True
            )

            if view_mode == "Árbol de directorios":
                if "opened_fs_dirs" not in st.session_state:
                    st.session_state["opened_fs_dirs"] = set()

                if "selected_fs_file" not in st.session_state:
                    st.session_state["selected_fs_file"] = None

                st.markdown("### Explorador del sistema de archivos")

                col_reset, col_open = st.columns(2)

                with col_reset:
                    if st.button("Cerrar árbol completo"):
                        st.session_state["opened_fs_dirs"] = set()
                        st.session_state["selected_fs_file"] = None
                        st.rerun()

                with col_open:
                    if st.button("Abrir carpetas principales"):
                        root_directories, _ = get_direct_children(members, "")
                        for directory in root_directories:
                            st.session_state["opened_fs_dirs"].add(directory)
                        st.rerun()

                st.markdown("")

                root_is_open = "__root__" in st.session_state["opened_fs_dirs"]

                root_arrow = "⌄" if root_is_open else "›"

                if st.button(
                    f"{root_arrow} 🖥️ Sistema de archivos",
                    key="toggle_root_fs"
                ):
                    if root_is_open:
                        st.session_state["opened_fs_dirs"].remove("__root__")
                    else:
                        st.session_state["opened_fs_dirs"].add("__root__")

                    st.rerun()

                if root_is_open:
                    render_windows_tree(
                        tar=tar,
                        members=members,
                        current_dir="",
                        level=0,
                        prefix=""
                    )

                selected_file = st.session_state.get("selected_fs_file")

                if selected_file:
                    show_file_from_tar(tar, selected_file)

            else:
                st.markdown("### Búsqueda dentro de la copia")

                file_paths = sorted([file.name for file in all_files])

                search = st.text_input(
                    "Buscar archivo o ruta",
                    placeholder="Ejemplo: passwd, logs, apache, nginx, shadow..."
                )

                if search:
                    filtered_paths = [
                        path for path in file_paths
                        if search.lower() in path.lower()
                    ]
                else:
                    filtered_paths = file_paths[:500]

                if not filtered_paths:
                    st.warning("No se encontraron archivos con ese criterio.")
                    return

                selected_file = st.selectbox(
                    "Selecciona un archivo para visualizar",
                    filtered_paths
                )

                show_file_from_tar(tar, selected_file)

    except Exception as e:
        st.error(f"Error leyendo filesystem.tar: {e}")


def main():
    st.set_page_config(
        page_title="ContainerTrace Forensics",
        page_icon="assets/Logo_App.png",
        layout="wide"
    )

    st.image("assets/Logo_App.png", width=160)

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