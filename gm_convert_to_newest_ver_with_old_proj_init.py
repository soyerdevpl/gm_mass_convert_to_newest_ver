import os
import subprocess
import logging
import shutil
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='conversion_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levellevelname)s - %(message)s',
    filemode='w'
)

# Paths
projecttool_path = r"C:\Program Files\GameMaker\ProjectTool\ProjectTool.exe"
prefabs_folder = os.path.join(os.getenv("APPDATA"), "GameMakerStudio2", "Prefabs")

def log_message(message):
    """Loguje wiadomość do pliku i konsoli"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('conversion_log.txt', 'a', encoding='utf-8') as log_file:
        log_file.write(f"{timestamp} - {message}\n")
    print(f"{timestamp} - {message}")

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
                extension = ".yymps"
            elif project_name.endswith((".yymp", ".gmez")):
                project_folder_name = project_name[:-5]  # usuwamy '.yymp', '.gmez'
                extension = ".yymp" if project_name.endswith(".yymp") else ".gmez"
            elif project_name.endswith((".gmz", ".yyz")):
                project_folder_name = project_name[:-4]  # usuwamy '.gmz', '.yyz'
                extension = ".gmz" if project_name.endswith(".gmz") else ".yyz"
            
            # Skracamy nazwę dla nowego pliku projektowego
            shortened_name = get_shortened_project_name(project_folder_name)
            
            # Tworzymy tymczasowy plik ze skróconą nazwą
            temp_project_path = project_path
            if shortened_name != project_folder_name:
                temp_project_path = os.path.join(current_dir, shortened_name + extension)
                shutil.copy2(project_path, temp_project_path)
                log_message(f"Created temporary file: {os.path.basename(temp_project_path)}")
            
            # Dla .gmez i .gmz dodajemy " gmx" do nazwy folderu
            if is_gms1:
                project_folder_name += " gmx"
                
            project_folder_path = os.path.join(current_dir, project_folder_name)
            
            # Uruchamiamy konwersję używając pliku tymczasowego
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
                time.sleep(1)
                
                # Usuwamy plik tymczasowy jeśli był utworzony
                if temp_project_path != project_path and os.path.exists(temp_project_path):
                    try:
                        os.remove(temp_project_path)
                        log_message(f"Removed temporary file: {temp_project_path}")
                    except Exception as e:
                        log_message(f"Error removing temporary file: {str(e)}")
                              
                # 1. Sprawdzamy czy folder projektu istnieje
                if os.path.exists(project_folder_path):
                    # 2. Przenosimy oryginalny plik do folderu projektowego
                    if os.path.exists(project_path):
                        try:
                            destination_path = os.path.join(project_folder_path, project_name)
                            shutil.move(project_path, destination_path)
                            log_message(f"Moved original file to: {destination_path}")
                            
                            # 3. Usuwamy folder options zaraz po przeniesieniu pliku
                            options_path = os.path.join(project_folder_path, "options")
                            if os.path.exists(options_path):
                                shutil.rmtree(options_path)
                                log_message(f"Removed options folder from: {options_path}")
                            
                        except Exception as e:
                            log_message(f"Error moving original file: {str(e)}")
                            return False
                    else:
                        log_message("Warning: Original file not found")
                else:
                    log_message(f"Error: Project folder was not created at {project_folder_path}")
                    return False
            else:
                log_message(f"Conversion failed for: {project_name}")
                log_message(f"ProjectTool output: {save_stdout}")
                # Usuwamy plik tymczasowy w przypadku błędu
                if temp_project_path != project_path and os.path.exists(temp_project_path):
                    os.remove(temp_project_path)
                return False

        else:
            # Standardowa obsługa dla innych typów plików
            if project_name.endswith(".project.gmx"):
                old_dir = os.path.join(current_dir, "_old gmx")
                base_name = project_name.replace('.project.gmx', '')
                shortened_base_name = get_shortened_project_name(base_name)
                new_project_name = shortened_base_name + '.yyp'
            else:
                old_dir = os.path.join(current_dir, "_old")
                base_name = os.path.splitext(project_name)[0]
                shortened_base_name = get_shortened_project_name(base_name)
                new_project_name = shortened_base_name + os.path.splitext(project_name)[1]
            
            new_project_path = os.path.join(current_dir, new_project_name)
            
            # Create old directory
            os.makedirs(old_dir, exist_ok=True)
            
            # Create paths
            old_project_path = os.path.join(old_dir, project_name)
            
            # Move project file and associated folders to old directory
            folders_to_move = []
            for item in os.listdir(current_dir):
                item_path = os.path.join(current_dir, item)
                if os.path.isdir(item_path) and item != os.path.basename(old_dir):
                    folders_to_move.append(item)
            
            # Move the project file
            shutil.move(project_path, old_project_path)
            
            # Move associated folders
            for folder in folders_to_move:
                source = os.path.join(current_dir, folder)
                destination = os.path.join(old_dir, folder)
                shutil.move(source, destination)
            
            # Process the project
            success = process_project(old_project_path, new_project_path, 
                                   projecttool_executable, prefabs_folder)
            
            if success:
                # Usuwamy folder options z nowego folderu projektu
                options_path = os.path.join(os.path.dirname(new_project_path), "options")
                if os.path.exists(options_path):
                    try:
                        shutil.rmtree(options_path)
                        log_message(f"Removed options folder from {os.path.dirname(new_project_path)}")
                    except Exception as e:
                        log_message(f"Error removing options folder: {str(e)}")
            else:
                # If failed, move everything back
                if os.path.exists(new_project_path):
                    os.remove(new_project_path)
                for folder in folders_to_move:
                    source = os.path.join(old_dir, folder)
                    destination = os.path.join(current_dir, folder)
                    shutil.move(source, destination)
                shutil.move(old_project_path, project_path)
    
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