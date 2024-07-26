import subprocess
import sys
import re
import os
import requests
import zipfile
import shutil

def run_command(command):
    """Ejecutar un comando en el sistema y verificar si fue exitoso."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return e

def gradient_text(text, colors):
    length = len(text)
    num_colors = len(colors)
    result = ""
    for i, char in enumerate(text):
        color_index = (i * (num_colors - 1)) // length
        t = (i * (num_colors - 1)) / length - color_index
        color1 = colors[color_index]
        color2 = colors[color_index + 1] if color_index + 1 < num_colors else colors[color_index]
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        result += f'\033[38;2;{r};{g};{b}m{char}'
    return result + '\033[0m'

def get_remote_info():
    remote_info = run_command(["git", "remote", "-v"])
    if isinstance(remote_info, subprocess.CalledProcessError):
        raise ValueError("No se encontró la URL del repositorio remoto.")
    match = re.search(r'origin\s+([^\s]+)\s+\(fetch\)', remote_info)
    if match:
        return match.group(1)
    else:
        raise ValueError("No se encontró la URL del repositorio remoto.")

def create_commit_tree():
    """Crear un nuevo commit tree desde el estado actual del índice."""
    commit_tree = run_command(["git", "write-tree"])
    commit_message = "Branch para guardar tu server_minecraft"
    commit = run_command(["git", "commit-tree", commit_tree, "-m", commit_message])
    return commit

def clean_branch():
    """Eliminar todos los archivos y carpetas del índice de Git."""
    run_command(["git", "rm", "-r", "--cached", "."])

def add_specific_files():
    """Añadir específicamente la carpeta 'servidor_minecraft' y el archivo 'configuracion.json'."""
    run_command(["git", "add", "--force", "servidor_minecraft"])
    run_command(["git", "add", "--force", "configuracion.json"])

def force_push(branch_name, commit):
    """Forzar el push al repositorio remoto en la rama especificada."""
    print(gradient_text(f"Realizando push forzado en la rama {branch_name}", [(0, 255, 0), (0, 128, 255)]))
    try:
        run_command(["git", "update-ref", f"refs/heads/{branch_name}", commit])
        run_command(["git", "push", "--force", "origin", branch_name])
        print(gradient_text(f"Push forzado realizado con éxito en la rama {branch_name}.", [(0, 255, 0), (0, 128, 255)]))
    except subprocess.CalledProcessError as e:
        print(gradient_text(f"Error en el push forzado: {e.stderr}", [(255, 0, 0), (255, 128, 0)]))
        sys.exit(1)

def branch():
    new_branch_name = "Minecraft_branch"

    # Obtener la URL del repositorio
    print(gradient_text("Obteniendo la URL del repositorio remoto", [(0, 255, 0), (0, 128, 255), (255, 0, 255)]))
    repo_url = get_remote_info()

    # Eliminar la rama remota si existe
    print(gradient_text(f"Eliminando la rama remota '{new_branch_name}'", [(0, 255, 0), (0, 128, 255), (255, 0, 255)]))
    run_command(["git", "push", "origin", "--delete", new_branch_name])

    # Limpiar el índice de Git
    clean_branch()

    # Añadir específicamente los archivos requeridos
    add_specific_files()

    # Crear un commit tree y obtener el commit SHA
    commit = create_commit_tree()

    # Push forzado
    force_push(new_branch_name, commit)

    # Generar la URL de descarga del ZIP
    user_name, repo_name = repo_url.split('/')[-2], repo_url.split('/')[-1].replace('.git', '')
    zip_url = f"https://codeload.github.com/{user_name}/{repo_name}/zip/refs/heads/{new_branch_name}"
    print(gradient_text(f"\nBranch creado/actualizado localmente: {new_branch_name}\nEnlace al branch para descargar en ZIP: {zip_url}", [(0, 255, 0), (0, 128, 255), (255, 0, 255)]))

    input(gradient_text("\nPresiona cualquier tecla para continuar...", [(0, 255, 0), (0, 128, 255), (255, 0, 255)]))

    sys.exit(0)
    
def download_and_extract_zip(url, extract_to='.'):
    local_zip_file = "repo.zip"
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_zip_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        with zipfile.ZipFile(local_zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    finally:
        if os.path.exists(local_zip_file):
            os.remove(local_zip_file)

def link():
    zip_url2 = input(gradient_text("Introduce el enlace directo del archivo ZIP: ", [(0, 255, 0), (0, 128, 255)])).strip()

    # Descargar y extraer el archivo zip
    download_and_extract_zip(zip_url2, os.getcwd())

    # Obtener el nombre del repositorio y el branch del enlace
    repo_name2 = zip_url2.split('/')[-5]
    branch_name2 = zip_url2.split('/')[-1]

    # Formatear el nombre esperado del directorio extraído
    expected_dir_name = f"{repo_name2}-{branch_name2}"

    # Verificar si la carpeta existe
    if not os.path.isdir(expected_dir_name):
        print(gradient_text("Error: No se pudo encontrar la carpeta extraída correctamente.", [(255, 0, 0), (255, 128, 0)]))
        sys.exit(1)

    # Mover archivos del directorio extraído al directorio principal
    extracted_dir = os.path.join(os.getcwd(), expected_dir_name)
    for item in os.listdir(extracted_dir):
        source_path = os.path.join(extracted_dir, item)
        target_path = os.path.join(os.getcwd(), item)
        if os.path.exists(target_path):
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)
        shutil.move(source_path, target_path)
    
    shutil.rmtree(extracted_dir)

    print(gradient_text("\n¡Repositorio descargado y extraído exitosamente!", [(0, 255, 0), (0, 128, 255)]))
    print(gradient_text("\nDirectorio actualizado con el contenido del archivo ZIP.", [(0, 255, 0), (0, 128, 255)]))
