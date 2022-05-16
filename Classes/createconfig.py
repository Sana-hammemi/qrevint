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

        self.config = {'Units': {'show': True, 'default': "SI"},
                       'ColorMap': {'show': True, 'default': 'viridis'},
                       'RatingPrompt': {'show': True, 'default': 'false'},
                       'SaveStyleSheet': {'show': True, 'default': 'false'},
                       'ExtrapWeighting': {'show': True, 'default': True},
                       'FilterUsingMeasurement': {'show': True,
                                                  'default': False},
                       'Uncertainty': {'show': False,
                                       'default': 'QRev Original'},
                       'MovingBedObservation': {'show': False,
                                                'default': False},
                       'QA': {'MinTransects': 2, 'MinDuration': 720}}

    def export_config(self):

        path = os.path.join(os.getcwd(), 'QRev.cfg')

        with open(path, 'w') as file:
            json.dump(self.config, file)
