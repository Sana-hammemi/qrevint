# Error Log class as written in RIVRS.

import os
import datetime
import traceback
from PyQt5 import QtWidgets


class ErrorLog:

    def __init__(self, app_name, sub_app):
        """Initiate object.

        Parameters:
            app_name: str
                parent directory
            sub_app: str
                sub application name
        """

        app_path = os.path.join(os.getenv("APPDATA"), app_name)

        if not os.path.isdir(app_path):
            os.mkdir(app_path)

        self.parent_path = app_path

        self.log_file = os.path.join(app_path, sub_app + "log_file.txt")

    def custom_excepthook(self, *exc_traceback):
        """Method to write error to file.

        Parameters:
            *exc_traceback: traceback

        """
        dt = datetime.datetime.now()
        dt_str = dt.strftime("%Y%m%d %H:%M:%S") + "\n"

        txt = "".join(traceback.format_exception(*exc_traceback))

        with open(self.log_file, "w") as file:
            file.write(dt_str + "\n")
            file.write(txt)
            file.write("\n")

        self.show_error(txt)

    @staticmethod
    def show_error(txt):
        """Trigger message dialog to show exception.

        Parameters:
            txt: str
        """

        txt = "Fatal Error Occurred:\n" + txt

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setInformativeText(txt)
        msg.setWindowTitle("Error")
        msg.exec_()

    def clear_error_log(self):
        """Clears the error log file."""

        if os.path.isfile(self.log_file):
            os.remove(self.log_file)
