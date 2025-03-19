import os
import subprocess
import logging
import concurrent.futures
import shutil
from datetime import datetime, timezone

# Configure logging to a file with thread safety
logging.basicConfig(
    filename='conversion_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)

# Lista standardowych folderów GameMaker
GM_PROJECT_FOLDERS = {
    'sprites', 'sounds', 'scripts', 'paths', 'objects', 'rooms', 
    'timelines', 'fonts', 'notes', 'datafiles', 'extensions', 
    'options', 'configs', 'tilesets', 'animcurves', 'sequences', 
    'shaders', 'particles', 'views', 'mvc', 'background', 'sound'
}

# Paths to directories and ProjectTool.exe file
#projects_directory = r"C:\Users\micha\Downloads\itch\_yyp_to_convert"
#output_directory = r"C:\Users\micha\Downloads\itch\_yyp24"
projects_directory = r"D:\Projects\maartenjensen.com_uniqc (uniqc indiedb)\gms2 z gm8"
output_directory = r"D:\Projects\maartenjensen.com_uniqc (uniqc indiedb)\_gm24"
projecttool_path = r"C:\Program Files\GameMaker\ProjectTool\ProjectTool.exe"
prefabs_folder = os.path.join(os.getenv("APPDATA"), "GameMakerStudio2", "Prefabs")

def log_message(message):
    logging.info(message)
    print(message)

def get_shortened_project_name(project_name):
    """Funkcja pomocnicza do skracania nazwy projektu poprzez usunięcie 'nazwa użytkownika - '"""
    if " - " in project_name:
        return project_name.split(" - ", 1)[1]
    return project_name

def process_project(project_path, new_project_dest_path, projecttool_executable, prefabs_folder):
    try:
        log_message(f"Processing project: {project_path}")

        source_dir = os.path.dirname(project_path)
        project_name = os.path.basename(project_path)
        destination_dir = os.path.dirname(new_project_dest_path)

        # Ensure the destination directory exists
        os.makedirs(destination_dir, exist_ok=True)

        # Tworzenie pliku tymczasowego ze skróconą nazwą jeśli potrzebne
        base_name = os.path.splitext(project_name)[0]
        extension = os.path.splitext(project_name)[1]
        
        shortened_name = get_shortened_project_name(base_name)
        
        # Używamy copy2 zamiast move
        if shortened_name != base_name:
            temp_project_path = os.path.join(source_dir, shortened_name + extension)
            if os.path.exists(temp_project_path):
                os.remove(temp_project_path)
            shutil.copy2(project_path, temp_project_path)  # Zmiana z move na copy2
            log_message(f"Created temporary file with shortened name: {os.path.basename(temp_project_path)}")
        else:
            temp_project_path = project_path

        # Convert the project
        save_command = [
            projecttool_executable,
            "PROJECT", "SAVE",
            f"SOURCE={temp_project_path}",
            f"DESTINATION={new_project_dest_path}",
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

        # Usuwamy tylko tymczasowy plik, jeśli był utworzony
        if temp_project_path != project_path:
            if os.path.exists(temp_project_path):
                os.remove(temp_project_path)
                log_message(f"Removed temporary file: {temp_project_path}")

        if "ProjectTool Successful" not in save_stdout:
            log_message("Saving project failed")
            return False

# Usuwamy folder options po udanej konwersji
        options_path = os.path.join(destination_dir, "options")
        if os.path.exists(options_path):
            try:
                shutil.rmtree(options_path)
                log_message(f"Removed options folder from: {options_path}")
            except Exception as e:
                log_message(f"Error removing options folder: {str(e)}")

        # Usuwamy folder options_dir po udanej konwersji
        options_dir_path = os.path.join(destination_dir, "options_dir")
        if os.path.exists(options_dir_path):
            try:
                shutil.rmtree(options_dir_path)
                log_message(f"Removed options_dir folder from: {options_dir_path}")
            except Exception as e:
                log_message(f"Error removing options_dir folder: {str(e)}")

            # Usuń stary folder mvc jeśli istnieje (przed konwersją)
            old_mvc_path = os.path.join(source_dir, "mvc")
            if os.path.exists(old_mvc_path):
                try:
                    shutil.rmtree(old_mvc_path)
                    log_message(f"Removed old mvc folder from source directory: {old_mvc_path}")
                except Exception as e:
                    log_message(f"Error removing old mvc folder: {str(e)}")

        # Sprawdź i przenieś dodatkowe pliki/foldery
        for item in os.listdir(source_dir):
            source_item_path = os.path.join(source_dir, item)
            item_lower = item.lower()
            
            # Pomijamy pliki projektu, .resource_order i standardowe foldery GameMaker
            if (not item.endswith(('.yyp', '.resource_order', '.yy')) and
                item_lower not in GM_PROJECT_FOLDERS and 
                source_item_path != project_path and
                source_item_path != temp_project_path):
                
                try: # shutil.move czy copy2?
                    destination_item_path = os.path.join(destination_dir, item)
                    shutil.copy2(source_item_path, destination_item_path)
                    log_message(f"Moved additional item: {item}")
                except Exception as e:
                    log_message(f"Error moving additional item {item}: {str(e)}")

        return True
    
    except Exception as e:
        log_message(f"Exception occurred: {e}")
        # Usuwamy tylko tymczasowy plik w przypadku błędu
        if 'temp_project_path' in locals() and temp_project_path != project_path and os.path.exists(temp_project_path):
            os.remove(temp_project_path)
        return False

def process_single_file(project_path, new_project_dest_path, projecttool_executable, prefabs_folder):
    """
    Przetwarza pojedyncze pliki (.yyz, .gmez, .gmz, .yymp, .yymps)
    """
    try:
        log_message(f"Processing single file: {project_path}")
        
        # Upewnij się, że katalog docelowy istnieje
        destination_dir = os.path.dirname(new_project_dest_path)
        os.makedirs(destination_dir, exist_ok=True)

        # Przygotuj nazwę pliku tymczasowego ze skróconą nazwą
        source_name = os.path.basename(project_path)
        base_name = os.path.splitext(source_name)[0]
        extension = os.path.splitext(source_name)[1]
        shortened_name = get_shortened_project_name(base_name)
        
        # Utwórz plik tymczasowy ze skróconą nazwą jeśli potrzebne
        if shortened_name != base_name:
            temp_project_path = os.path.join(os.path.dirname(project_path), shortened_name + extension)
            if os.path.exists(temp_project_path):
                os.remove(temp_project_path)
            shutil.copy2(project_path, temp_project_path)
            log_message(f"Created temporary file: {temp_project_path}")
        else:
            temp_project_path = project_path

        # Konwertuj projekt
        save_command = [
            projecttool_executable,
            "PROJECT", "SAVE",
            f"SOURCE={temp_project_path}",
            f"DESTINATION={new_project_dest_path}",
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

        # Usuń plik tymczasowy jeśli był utworzony
        if temp_project_path != project_path and os.path.exists(temp_project_path):
            os.remove(temp_project_path)
            log_message(f"Removed temporary file: {temp_project_path}")

        if "ProjectTool Successful" not in save_stdout:
            log_message("Saving project failed")
            return False

    # Usuwamy folder options po udanej konwersji
        options_path = os.path.join(destination_dir, "options")
        if os.path.exists(options_path):
            try:
                shutil.rmtree(options_path)
                log_message(f"Removed options folder from: {options_path}")
            except Exception as e:
                log_message(f"Error removing options folder: {str(e)}")

        # Usuwamy folder options_dir po udanej konwersji
        options_dir_path = os.path.join(destination_dir, "options_dir")
        if os.path.exists(options_dir_path):
            try:
                shutil.rmtree(options_dir_path)
                log_message(f"Removed options_dir folder from: {options_dir_path}")
            except Exception as e:
                log_message(f"Error removing options_dir folder: {str(e)}")

        # Usuń stary folder mvc jeśli istnieje (przed konwersją)
        old_mvc_path = os.path.join(source_dir, "mvc")
        if os.path.exists(old_mvc_path):
            try:
                shutil.rmtree(old_mvc_path)
                log_message(f"Removed old mvc folder from source directory: {old_mvc_path}")
            except Exception as e:
                log_message(f"Error removing old mvc folder: {str(e)}")

        return True

    except Exception as e:
        log_message(f"Error processing single file: {str(e)}")
        # Usuń plik tymczasowy w przypadku błędu
        if 'temp_project_path' in locals() and temp_project_path != project_path and os.path.exists(temp_project_path):
            os.remove(temp_project_path)
        return False

def convert_project_wrapper(args):
    return process_project(*args)

def convert_projects(projects_dir, output_dir, projecttool_executable, prefabs_folder):
    project_tasks = []
    
    # Najpierw zbieramy pojedyncze pliki z głównego katalogu
    for file in os.listdir(projects_dir):
        if file.endswith((".gmez", ".gmz", ".yymp", ".yyz", ".yymps")):
            project_path = os.path.join(projects_dir, file)
            if os.path.isfile(project_path):
                # Dla plików .gmez i .gmz dodajemy " gmx" do nazwy folderu
                is_gms1 = file.endswith((".gmez", ".gmz"))
                base_name = os.path.splitext(file)[0]
                new_folder_name = base_name + " gmx" if is_gms1 else base_name
                
                # Tworzymy folder docelowy z pełną nazwą (nie skróconą)
                new_folder_path = os.path.join(output_dir, new_folder_name)
                os.makedirs(new_folder_path, exist_ok=True)
                
                # Ale plik projektowy będzie miał skróconą nazwę
                shortened_base_name = get_shortened_project_name(base_name)
                new_project_dest_path = os.path.join(new_folder_path, shortened_base_name + '.yyp')
                # Używamy process_single_file dla pojedynczych plików
                project_tasks.append((project_path, new_project_dest_path, projecttool_executable, prefabs_folder))

# Następnie zbieramy projekty z podfolderów (używamy oryginalnej funkcji process_project)
    for folder_name in os.listdir(projects_dir):
        folder_path = os.path.join(projects_dir, folder_name)
        
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith((".yyp", ".project.gmx")):
                    project_path = os.path.join(folder_path, file)
                    
                    # Sprawdzamy czy w nazwie folderu lub pliku jest "gm8"
                    contains_gm8 = "gm8" in folder_name.lower() or "gm8" in file.lower()
                    
                    # Dla .gmx dodajemy " gmx" do nazwy folderu TYLKO jeśli nie ma "gm8"
                    if file.endswith(".gmx") and not contains_gm8:
                        new_folder_name = folder_name + " gmx"
                    else:
                        new_folder_name = folder_name
                        
                    new_folder_path = os.path.join(output_dir, new_folder_name)
                    os.makedirs(new_folder_path, exist_ok=True)

                    if file.endswith(".project.gmx"):
                        base_name = file.replace('.project.gmx', '')
                        shortened_base_name = get_shortened_project_name(base_name)
                    else:
                        base_name = os.path.splitext(file)[0]
                        shortened_base_name = get_shortened_project_name(base_name)

                    new_project_dest_path = os.path.join(new_folder_path, shortened_base_name + '.yyp')
                    # Używamy oryginalnej funkcji process_project dla projektów w folderach
                    project_tasks.append((project_path, new_project_dest_path, projecttool_executable, prefabs_folder))

    # Przetwarzamy wszystkie zadania równolegle
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for task in project_tasks:
            if os.path.splitext(task[0])[1] in ['.gmez', '.gmz', '.yymp', '.yyz', '.yymps']:
                futures.append(executor.submit(process_single_file, *task))
            else:
                futures.append(executor.submit(process_project, *task))
            
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if result:
                    log_message("Project processed successfully.")
                else:
                    log_message("Project processing failed.")
            except Exception as e:
                log_message(f"Project processing failed with exception: {e}")

if __name__ == "__main__":
    # Call the conversion function
    convert_projects(projects_directory, output_directory, projecttool_path, prefabs_folder)