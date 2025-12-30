import os
import qrev_docs
from qrev import translation

__author__ = "USGS"
__company__ = "USGS"
__version__ = "4.41.2"
__app__ = "QRev"
__qrev_version__ = __app__ + " " + __version__

__sphinx_path__ = os.path.abspath(os.path.join(os.path.dirname(
    qrev_docs.__file__)))

__doc_path__ = os.path.abspath(os.path.join(__sphinx_path__, "_build", "html")
)
__icon_path__ = os.path.abspath(
    os.path.join(__sphinx_path__, "source", "assets", "files", "*"
    )
)

__translation_files__ = os.path.abspath(os.path.join(os.path.dirname(
    translation.__file__)))


# Fix for Windows users to propagate the UI icon to the Taskbar. This is
# needed because Windows is presuming that Python is the application, but
# actually, python is just hosting the application. By telling Windows
# the "Application User Model" for the UI, the correct icon will be used.
# See: https://stackoverflow.com/a/1552105
myappid = "{}.{}.{}.{}.{}".format(
    __company__, __app__, __app__, __version__, __author__
)
