import sys
from PyQt5.QtWidgets import QApplication

from qrev.UI.QRev import QRev


if __name__ == '__main__':
    # Initialize the UI
    app = QApplication(sys.argv)
    w = QRev()
    sys.exit(app.exec_())
