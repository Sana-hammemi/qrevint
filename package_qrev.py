import pyinstaller_versionfile
import PyInstaller.__main__

from Classes import __version__, __app__

print('Updating version information')

pyinstaller_versionfile.create_versionfile(
    output_file="file_version_info.txt",
    version=__version__ + ".0",
    company_name="My Imaginary Company",
    file_description="",
    internal_name=__app__,
    legal_copyright="CC0 1.0",
    original_filename=__app__ + '.exe',
    product_name=__app__,
    translations=[1033, 1200],
)

print('Running pyinstaller...')

PyInstaller.__main__.run(["app.spec"])
