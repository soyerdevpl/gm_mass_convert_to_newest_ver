# gm_mass_convert_to_newest_ver
GameMaker mass project converter to newest version


Both scripts search the directory for projects, convert them using ProjectTool.exe, change file names, and save them in a new directory. Logging is done to the conversion_log.txt file, and the script with multiple processes uses ThreadPoolExecutor to speed up the conversion by processing multiple projects simultaneously. This tutorial should help you understand how the script works and how to customize it for your needs.

Supported extensions: yyz, yymps, yymp, yyp, gmz, gmx (yyp and gmx should be in the subfolder with project tree folders/files)

Set the path to this directory as you desire in the following line:

    projects_directory: Path to the directory containing projects to be converted.

The projects will be converted to the latest version of GameMaker and saved in the output_directory, which you can edit in the following line:

    output_directory: Path to the directory where converted projects will be saved.
