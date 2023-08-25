import os
import pyinstaller_versionfile
import PyInstaller.__main__
import shutil

from Classes import __version__, __app__, __company__

print("Updating version information")
pyinstaller_versionfile.create_versionfile(
    output_file="file_version_info.txt",
    version=__version__ + ".0.0",
    company_name=__company__,
    file_description="",
    internal_name=__app__,
    legal_copyright="CC0 1.0",
    original_filename=__app__ + ".exe",
    product_name=__app__,
    translations=[1033, 1200],
)

print("Running pyinstaller...")
PyInstaller.__main__.run(["app.spec"])

print("Verifying QRev.EXE was created.")
path = os.path.join(os.getcwd(), "dist", __app__ + ".exe")
if os.path.exists(path):
    print("QRev was packaged, creating compressed distribution package.")
    about = os.path.join(os.getcwd(), "Help", "QRev_About.pdf")
    change_log = os.path.join(os.getcwd(), "Help", "QRev_Change_Log.pdf")
    tech_man = os.path.join(os.getcwd(), "Help", "QRev_Tech.pdf")
    user_man = os.path.join(os.getcwd(), "Help", "QRev_Users.pdf")

    qrev_package = __app__ + __version__.replace(".", "")
    qrev_dir = os.path.join(os.getcwd(), "dist", qrev_package)
    help_folder = os.path.join(os.getcwd(), "dist", qrev_package, "Help")

    os.mkdir(qrev_dir)
    os.mkdir(help_folder)

    # copy in help docs
    shutil.copy(about, os.path.join(help_folder, "QRev_About.pdf"))
    shutil.copy(change_log, os.path.join(help_folder, "QRev_Change_Log.pdf"))
    shutil.copy(tech_man, os.path.join(help_folder, "QRev_Tech.pdf"))
    shutil.copy(user_man, os.path.join(help_folder, "QRev_Users.pdf"))

    # copy QRev exe
    shutil.copy(
        os.path.join(os.getcwd(), "dist", "QRev.exe"),
        os.path.join(qrev_dir, "QRev.exe"),
    )

    # Copy cfg file
    shutil.copy(
        os.path.join(os.getcwd(), "QRev.cfg"), os.path.join(qrev_dir, "QRev.cfg")
    )
    # Copy icon
    shutil.copy(
        os.path.join(os.getcwd(), "QRev.ico"), os.path.join(qrev_dir, "QRev.ico")
    )
    # copy stylesheets
    shutil.copy(
        os.path.join(os.getcwd(), "UI", "QRevStylesheet_english.xsl"),
        os.path.join(qrev_dir, "QRevStylesheet_english.xsl"),
    )
    shutil.copy(
        os.path.join(os.getcwd(), "UI", "QRevStylesheet_si.xsl"),
        os.path.join(qrev_dir, "QRevStylesheet_si.xsl"),
    )

    print("Please sign QRev.EXE before zipping the directory. Packaging " "Complete")
