import sys
from PyQt5.QtWidgets import QApplication

from UI.QRev import QRev


class run_qrev:


    def run_qrev(self):
        app = QRev()

        # set icon

        # set window title or pass version?

        app.show()

    def run_qrev_int(self):

        # Read sticky settings, Call disclaimer if needed

        # start application
        app = QRev()

        # set icon

        # set stylesheet

        # set window title or pass version?

        app.show()

if __name__ == '__main__':
    # Initialize the UI
    app = QApplication(sys.argv)
    w = run_qrev()
    sys.exit(app.exec_())
