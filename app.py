import os
import sys
from PyQt5.QtWidgets import QApplication

from qrev.UI.QRev import QRev
from qrev.UI.errorlog import ErrorLog

# Set the environment variable for PyQt5
os.environ["QT_API"] = "pyqt5"


if __name__ == '__main__':
    # Initialize the UI
    log = ErrorLog("QRev", "QRev")
    app = QApplication(sys.argv)
    w = QRev()
    sys.excepthook = log.custom_excepthook
    sys.exit(app.exec_())
