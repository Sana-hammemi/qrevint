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
            "ExtrapWeighting": {"show": True, "default": True},
            "FilterUsingMeasurement": {"show": True, "default": False},
            "Uncertainty": {"show": False, "default": "QRev Original"},
            "MovingBedObservation": {"show": False, "default": False},
            "ExportCrossSection": {"show": True, "default": True},
            "MAP": {"show": True},
            "AutonomousGPS": {"allow": False},
            "QDigits": {"method": "sigfig", "digits": 3},
            "SNR": {"Use3Beam": True},
            "ExtrapolatedSpeed": {"ShowIcon": True},
            "QA": {"MinTransects": 2, "MinDuration": 720},
        }

    def export_config(self):

        path = os.path.join(os.getcwd(), "QRev.cfg")

        with open(path, "w") as file:
            json.dump(self.config, file)
