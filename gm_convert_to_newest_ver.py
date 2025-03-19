import os
import subprocess
import logging
import shutil
import sys
from datetime import datetime

GM_PROJECT_FOLDERS = {
    'sprites', 'sounds', 'scripts', 'paths', 'objects', 'rooms', 
    'timelines', 'fonts', 'notes', 'datafiles', 'extensions', 
    'options', 'configs', 'tilesets', 'animcurves', 'sequences', 
    'shaders', 'particles', 'views', 'mvc', 'background', 'sound'
 }
 
# Configure logging
logging.basicConfig(
    filename='conversion_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)

# Paths
projecttool_path = r"C:\Program Files\GameMaker\ProjectTool\ProjectTool.exe"
prefabs_folder = os.path.join(os.getenv("APPDATA"), "GameMakerStudio2", "Prefabs")

def log_message(message):
    """Loguje wiadomość do pliku i konsoli"""
    logging.info(message)
    print(message)

def process_project(project_path, new_project_path, projecttool_executable, prefabs_folder):
    """Przetwarza projekt używając ProjectTool"""
    try:
        log_message(f"Processing project: {project_path}")

        save_command = [
            projecttool_executable,
            "PROJECT", "SAVE",
            f"SOURCE={project_path}",
            f"DESTINATION={new_project_path}",
            f"PREFABSFOLDER={prefabs_folder}",
            "FORMAT=VERSIONED",
            "CLEANUP=TRUE"
        ]
        
        log_message(f"Running command: {' '.join(save_command)}")
        save_process = subprocess.Popen(
            save_command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        save_stdout, save_stderr = save_process.communicate()
        log_message(f"SAVE stdout: {save_stdout}")
        log_message(f"SAVE stderr: {save_stderr}")

        if "ProjectTool Successful" not in save_stdout:
            log_message("Saving project failed")
            return False

        return True
    except Exception as e:
        log_message(f"Exception occurred: {e}")
        return False

def get_shortened_project_name(project_name):
    """Funkcja pomocnicza do skracania nazwy projektu poprzez usunięcie 'nazwa użytkownika - '"""
    if " - " in project_name:
        return project_name.split(" - ", 1)[1]
    return project_name
    
def convert_single_project(project_path, projecttool_executable, prefabs_folder):
    """Konwertuje pojedynczy projekt"""
    try:
        current_dir = os.path.dirname(project_path)
        project_name = os.path.basename(project_path)
        log_message(f"\n=== Starting conversion of: {project_name} ===")
        log_message(f"Converting project in directory: {current_dir}")

        if project_name.endswith((".yymp", ".yymps", ".yyz", ".gmez", ".gmz")):
            # Dla plików .yymp, .yymps .yyz, .gmez i .gmz
            is_gms1 = project_name.endswith((".gmez", ".gmz"))
            
            # Pobieramy nazwę pliku bez rozszerzenia
            if project_name.endswith(".yymps"):
                project_folder_name = project_name[:-6]  # usuwamy całe '.yymps'
                file_extension = ".yymps"
            elif project_name.endswith((".yymp", ".gmez")):
                project_folder_name = project_name[:-5]  # usuwamy '.yymp', '.gmez'
                file_extension = ".yymp" if project_name.endswith(".yymp") else ".gmez"
            elif project_name.endswith((".gmz", ".yyz")):
                project_folder_name = project_name[:-4]  # usuwamy '.gmz', '.yyz'
                file_extension = ".gmz" if project_name.endswith(".gmz") else ".yyz"
            
            # Skracamy nazwę projektu (usuwamy "nazwa użytkownika - ")
            shortened_name = get_shortened_project_name(project_folder_name)
            
            # Sprawdzamy, czy nazwa już jest skrócona
            if shortened_name == project_folder_name:
                # Jeśli nazwa jest już skrócona, używamy oryginalnego pliku
                temp_project_path = project_path
            else:
                # W przeciwnym razie przenosimy plik do tymczasowej lokalizacji ze skróconą nazwą
                temp_project_path = os.path.join(current_dir, shortened_name + file_extension)
                shutil.move(project_path, temp_project_path)
            
            # Dla .gmez i .gmz dodajemy " gmx" do nazwy folderu docelowego
            if is_gms1:
                project_folder_name += " gmx"
                
            project_folder_path = os.path.join(current_dir, project_folder_name)
            
            # Uruchamiamy konwersję
            save_command = [
                projecttool_executable,
                "PROJECT", "SAVE",
                f"SOURCE={temp_project_path}",
                f"DESTINATION={project_folder_path}",
                f"PREFABSFOLDER={prefabs_folder}",
                "FORMAT=VERSIONED",
                "CLEANUP=TRUE"
            ]
            
            log_message(f"Running command: {' '.join(save_command)}")
            save_process = subprocess.Popen(
                save_command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            save_stdout, save_stderr = save_process.communicate()
            log_message(f"SAVE stdout: {save_stdout}")
            log_message(f"SAVE stderr: {save_stderr}")

            if "ProjectTool Successful" in save_stdout:
                log_message(f"Successfully converted project: {project_name}")
                
                # Czekamy chwilę na utworzenie wszystkich plików
                import time
                time.sleep(2)
                
                # Usuwanie pliku tymczasowego
                if temp_project_path != project_path and os.path.exists(temp_project_path):
                    try:
                        os.remove(temp_project_path)
                        log_message(f"Removed temporary file: {temp_project_path}")
                    except Exception as e:
                        log_message(f"Error removing temporary file: {str(e)}")
                elif os.path.exists(project_path):
                    try:
                        os.remove(project_path)
                        log_message(f"Removed original file: {project_path}")
                    except Exception as e:
                        log_message(f"Error removing original file: {str(e)}")

                # Usuwamy niepotrzebne foldery
                folders_to_remove = [
                    ("options", os.path.join(project_folder_path, "options")),
                    ("options_dir", os.path.join(project_folder_path, "options_dir")),
                    ("mvc", os.path.join(current_dir, "mvc")),
                    ("_gmx", os.path.join(project_folder_path, "_gmx")),
                    ("_old", os.path.join(current_dir, "_old"))
                ]

                for folder_name, folder_path in folders_to_remove:
                    if os.path.exists(folder_path):
                        try:
                            shutil.rmtree(folder_path)
                            log_message(f"Removed {folder_name} folder from: {folder_path}")
                        except Exception as e:
                            log_message(f"Error removing {folder_name} folder: {str(e)}")
                
                return True
            else:
                log_message(f"Conversion failed for: {project_name}")
                log_message(f"ProjectTool output: {save_stdout}")
                # Przywracamy oryginalną nazwę pliku w przypadku błędu
                if temp_project_path != project_path and os.path.exists(temp_project_path):
                    shutil.move(temp_project_path, project_path)
                return False

        else:
            # Standardowa obsługa dla innych typów plików
            if project_name.endswith(".project.gmx"):
                old_dir = os.path.join(current_dir, "_gmx")
                new_project_name = get_shortened_project_name(project_name.replace('.project.gmx', '.yyp'))
            else:
                old_dir = os.path.join(current_dir, "_old")
                new_project_name = get_shortened_project_name(project_name)
            
            new_project_path = os.path.join(current_dir, new_project_name)
            
            # Create old directory
            os.makedirs(old_dir, exist_ok=True)
            
            # Create paths
            old_project_path = os.path.join(old_dir, project_name)
            
            # Move project file and associated folders to old directory
            folders_to_move = []
            for item in os.listdir(current_dir):
                item_path = os.path.join(current_dir, item)
                item_lower = item.lower()
                if (os.path.isdir(item_path) and 
                    item != os.path.basename(old_dir) and 
                    item_lower in GM_PROJECT_FOLDERS):
                    folders_to_move.append(item)
                elif item.endswith('.resource_order'):  # Usuwamy stary plik .resource_order
                    try:
                        os.remove(item_path)
                        log_message(f"Removed old .resource_order file: {item}")
                    except Exception as e:
                        log_message(f"Error removing .resource_order file: {str(e)}")
            
            # Move the project file
            shutil.move(project_path, old_project_path)
            
            # Move only GameMaker project folders
            for folder in folders_to_move:
                source = os.path.join(current_dir, folder)
                destination = os.path.join(old_dir, folder)
                shutil.move(source, destination)
            
            # Process the project
            success = process_project(old_project_path, new_project_path, 
                                   projecttool_executable, prefabs_folder)
            
            if success:
                # Usuwamy niepotrzebne foldery
                folders_to_remove = [
                    ("options", os.path.join(current_dir, "options")),
                    ("options_dir", os.path.join(current_dir, "options_dir")),
                    ("mvc", os.path.join(current_dir, "mvc")),
                    ("_gmx", os.path.join(current_dir, "_gmx")),
                    ("_old", os.path.join(current_dir, "_old"))
                    
                ]

                for folder_name, folder_path in folders_to_remove:
                    if os.path.exists(folder_path):
                        try:
                            shutil.rmtree(folder_path)
                            log_message(f"Removed {folder_name} folder from: {folder_path}")
                        except Exception as e:
                            log_message(f"Error removing {folder_name} folder: {str(e)}")
                
                return True
            else:
                # If failed, move everything back
                if os.path.exists(new_project_path):
                    os.remove(new_project_path)
                for folder in folders_to_move:
                    source = os.path.join(old_dir, folder)
                    destination = os.path.join(current_dir, folder)
                    shutil.move(source, destination)
                shutil.move(old_project_path, project_path)
                return False

    except Exception as e:
        log_message(f"Error during conversion of {project_name}: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        log_message("Usage: python gm_convert_to_newest_ver.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    convert_single_project(project_path, projecttool_path, prefabs_folder)