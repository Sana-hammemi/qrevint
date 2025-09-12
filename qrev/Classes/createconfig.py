import json
import os


class Config:
    """Creates default config file in json format.

    Attributes
    ----------
    config: dict
        Default config view and processing options.
    """

    def __init__(self):
        """Initiate attributes"""

        self.config = {
            "Units": {"show": True, "default": "SI"},
            "ColorMap": {"show": True, "default": "viridis"},
            "RatingPrompt": {"show": True, "default": False},
            "SaveStyleSheet": {"show": True, "default": False},
            "ExtrapWeighting": {"show": True, "default": False},
            "FilterUsingMeasurement": {"show": True, "default": False},
            "Uncertainty": {"show": False, "default": "QRev"},
            "MovingBedObservation": {"show": False, "default": False},
            "ExportCrossSection": {"show": True, "default": True},
            "MAP": {"show": True},
            "AutonomousGPS": {"allow": False},
            "QDigits": {"method": "fixed", "digits": 2},
            "SNR": {"Use3Beam": False},
            "ExtrapolatedSpeed": {"ShowIcon": True},
            "Excluded": {"RioPro": 0.25, "M9": 0.16},
            "QA": {"MinTransects": 2, "MinDuration": 720},
            "LeftRightFlowDirDiff": {"threshold": 8.1},
            "PDFSummary": {"show": True, "default": False},
            "DateFormat": {"show": True, "default": "y.m.d"},
            "TimeZone": {"required": False},
            "PercentMeasured": {"show": True},
            "Area": {"projection": "ParallAC"}
        }

    def export_config(self, output_path=None):
        """Export default configuration files.

        Parameters:
            output_path: str
        """

        if output_path is None:
            path = os.path.join(os.getcwd(), "QRev.cfg")
        else:
            path = os.path.join(output_path, "QRev.cfg")

        with open(path, "w") as file:
            json.dump(self.config, file, indent=4)

    def export_international_config(self):
        int_config = {
            "Units": {"show": True, "default": "SI"},
            "ColorMap": {"show": True, "default": "viridis"},
            "RatingPrompt": {"show": True, "default": False},
            "SaveStyleSheet": {"show": True, "default": True},
            "ExtrapWeighting": {"show": True, "default": True},
            "FilterUsingMeasurement": {"show": True, "default": False},
            "Uncertainty": {"show": True, "default": "Oursin"},
            "MovingBedObservation": {"show": False, "default": False},
            "ExportCrossSection": {"show": True, "default": True},
            "MAP": {"show": True},
            "AutonomousGPS": {"allow": False},
            "QDigits": {"method": "sigfig", "digits": 3},
            "SNR": {"Use3Beam": False},
            "ExtrapolatedSpeed": {"ShowIcon": True},
            "Excluded": {"RioPro": 0.25, "M9": 0.16},
            "QA": {"MinTransects": 2, "MinDuration": 720},
            "LeftRightFlowDirDiff": {"threshold": 8.1},
            "PDFSummary": {"show": True, "default": "Prompt"},
            "DateFormat": {"show": True, "default": "y.m.d"},
            "TimeZone": {"required": False},
            "PercentMeasured": {"show": False},
            "Area": {"projection": "ParallAC"}
        }
        path = os.path.join(os.getcwd(), "QRev.cfg")

        with open(path, "w") as file:
            json.dump(int_config, file, indent=4)
