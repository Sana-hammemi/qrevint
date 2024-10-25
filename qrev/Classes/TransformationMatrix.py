import numpy as np


class TransformationMatrix(object):
    """Determines the transformation matrix and source for the specified ADCP
     model from the data provided.

    Attributes
    ----------
    source: str
        Source of transformation matrix, either Nominal or ADCP
    matrix: np.array
        One or more 4x4 transformation matrices.
    """

    def __init__(self):
        """Constructor initializes variable to None"""
        self.source = None
        self.matrix = None

    def populate_data(self, manufacturer, model=None, data_in=None):
        """Uses the manufacturer and model to determine how to parse the
        transformation matrix.

        Parameters
        ----------
        manufacturer: str
            Name of manufacturer (TRDI, SonTek)
        model: str
            Model of ADCP
        data_in:
            System test data or 'Nominal'
        """

        if manufacturer == "TRDI":
            self.trdi(model, data_in)
        elif manufacturer == "SonTek":
            self.sontek(data_in)
        elif manufacturer == "rsqst":
            self.rsqst(data_in)

    def trdi(self, model=None, data_in=None):
        """Processes the data to store the transformation matrix for
        TRDI ADCPs. If no transformation matrix information is available a nominal
        transformation matrix for that model is assumed.

        Parameters
        ----------
        model: str
            Model of ADCP
        data_in: np.array(float)
            System test data or 'Nominal'
        """

        adcp_model = model
        # Set nominal matrix based on model
        self.matrix = [
            [1.4619, -1.4619, 0, 0],
            [0, 0, -1.4619, 1.4619],
            [0.2661, 0.2661, 0.2661, 0.2661],
            [1.0337, 1.0337, -1.0337, -1.0337],
        ]
        self.source = "Nominal"

        if adcp_model == "RiverRay":
            self.matrix = [
                [1, -1, 0, 0],
                [0, 0, -1, 1],
                [0.2887, 0.2887, 0.2887, 0.2887],
                [0.7071, 0.7071, -0.7071, -0.7071],
            ]

        # Overwrite nominal transformation matrix with custom matrix from
        # test data, if available

        if data_in == "Nominal":
            self.source = "Nominal"
        elif adcp_model == "Rio Grande":
            self.riogrande(data_in)
        elif adcp_model == "StreamPro":
            self.streampro(data_in)
        elif adcp_model == "RiverRay":
            self.riverray(data_in)
        elif adcp_model == "RiverPro":
            self.riverpro(data_in)
        elif adcp_model == "RioPro":
            self.riopro(data_in)
        elif adcp_model == "pd0":
            self.matrix = data_in.Inst.t_matrix
            self.source = "ADCP"

        if np.array(self.matrix).size < 16:
            self.trdi(model=model, data_in=None)

        # Save matrix as np array
        self.matrix = np.array(self.matrix)[0:4, 0:4]

    def riogrande(self, data_in):
        """Process Rio Grande test data for transformation matrix.

        Parameters
        ----------
        data_in:
            System test data
        """
        if data_in is not None:
            idx = data_in.find("Instrument Transformation Matrix (Down):")
            if idx != -1:
                cell_matrix = np.fromstring(
                    data_in[idx + 50 : idx + 356], dtype=np.float64, sep=" "
                )
                try:
                    self.matrix = np.reshape(cell_matrix, (-1, 8))[:, 0:4]

                    self.source = "ADCP"
                except ValueError:
                    pass

    def streampro(self, data_in):
        """Process StreamPro test data for transformation matrix.

        Parameters
        ----------
        data_in:
            System test data
        """

        if data_in is not None:
            idx = data_in.find(">PS3")
            if idx != -1:
                temp_str = data_in[idx + 5 : idx + 138]
                temp_str = temp_str.replace("-", " -")
                temp_str = temp_str[: temp_str.find(">")]
                cell_matrix = np.fromstring(temp_str, dtype=np.float64, sep=" ")
                try:
                    self.matrix = cell_matrix.reshape(4, 4)
                    self.source = "ADCP"
                except ValueError:
                    pass

    def riverray(self, data_in):
        """Process RiverRay test data for transformation matrix.

        Parameters
        ----------
        data_in: str
            System test data
        """
        if data_in is not None:
            idx = data_in.find("Instrument Transformation Matrix")
            if idx != -1:
                idx2 = data_in[idx:].find(":")
                idx3 = idx + idx2 + 1
                if idx2 != -1:
                    idx4 = data_in[idx3:].find(">")
                    idx5 = idx3 + idx4 - 2
                    if idx4 != -1:
                        cell_matrix = np.fromstring(
                            data_in[idx3:idx5], dtype=np.float64, sep=" "
                        )
                        self.matrix = cell_matrix.reshape(4, 4)
                        self.source = "ADCP"

    def riverpro(self, data_in):
        """Process RiverPro test data for transformation matrix.

        Parameters
        ----------
        data_in: str
            System test data
        """
        if data_in is not None:
            idx = data_in.find("Instrument Transformation Matrix")
            if idx != -1:
                idx2 = data_in[idx:].find(":")
                idx3 = idx + idx2
                if idx2 != -1:
                    idx4 = data_in[idx3:].find("Has V-Beam")
                    idx5 = idx3 + idx4 - 2
                    if idx4 != -1:
                        self.matrix = float(data_in[idx3:idx5])
                        self.source = "ADCP"

    def riopro(self, data_in):
        """Process RioPro test data for transformation matrix.

        Parameters
        ----------
        data_in:
            System test data
        """

        if data_in is not None:
            idx = data_in.find("Instrument Transformation Matrix")
            if idx != -1:
                idx2 = data_in[idx:].find(":")
                idx3 = idx + idx2
                if idx2 != -1:
                    idx4 = data_in[idx3:].find("Has V-Beam")
                    idx5 = idx3 + idx4 - 2
                    if idx4 != -1:
                        self.matrix = float(data_in[idx3:idx5])
                        self.source = "ADCP"

    def sontek(self, data_in):
        """Store SonTek transformation matrix data.

        Parameters
        ----------
        data_in:
            System test data
        """

        if data_in is not None:
            self.source = "ADCP"
            # Note: for M9 this is a 4x4x3 matrix (300,500,1000)
            # Note: for S5 this is a 4x4x2 matrix (3000,1000)
            self.matrix = data_in

    def populate_from_qrev_mat(self, tmatrix):
        self.matrix = tmatrix.matrix
        self.source = tmatrix.source
    
    def rsqst(self, data_in):
        """Coordinates creation of transformation matrices from raw data from RSQ.

        Parameters
        ----------
        data_in: tuple
            Tuple containing beam elevation and beam azimuth
        """

        beam_elev = data_in[0]
        beam_azimuth = data_in[1]

        self.matrix = np.zeros((4, 4, len(beam_elev)))
        for n in range(len(beam_elev)):
            if beam_elev[n][0] == 0:
                self.matrix[2, 0, n] = -1
            else:
                self.create_matrix(n, beam_elev[n], beam_azimuth[n])

    def create_matrix(self, n, beam_elev, beam_azimuth):
        """Code provided by SonTek to create beam matrix.

        Parameters
        ----------
        n: int
            3rd index for final transformation matrix
        beam_elev: list
            Beam elevations in radians
        beam_azimuth: list
            Beam azimuths in radians
        """

        beam_count = len(beam_elev)
        beam_matrix = np.zeros((beam_count, beam_count))
        bdc = np.zeros((beam_count, 3))

        for beam in range(beam_count):
            bdc[beam, 0] = np.sin(beam_elev[beam]) * np.cos(beam_azimuth[beam])
            bdc[beam, 1] = -1 * np.sin(beam_elev[beam]) * np.sin(beam_azimuth[beam])
            bdc[beam, 2] = -1 * np.cos(beam_elev[beam])

        bdct = bdc.T

        am = np.linalg.inv(np.matmul(bdct, bdc))

        b_2_instrument = np.matmul(am, bdct)

        z2 = np.zeros((1, beam_count))

        if beam_count == 4:
            bdc24i = np.zeros((3, 3))
            err24 = np.zeros((1, 3))
            for row in range(3):
                for col in range(3):
                    bdc24i[row, col] = bdc[row + 1, col]
                err24[0, row] = bdc[0, row]

            bdc24i = np.linalg.inv(bdc24i)
            err24 = -1 * np.matmul(err24, bdc24i)
            err = np.zeros((1, 4))
            err[0, 0] = 1
            err[0, 1] = err24[0, 0]
            err[0, 2] = err24[0, 1]
            err[0, 3] = err24[0, 2]

            t1 = 0
            t2 = 0

            for col in range(4):
                t1 = t1 + b_2_instrument[2, col] * b_2_instrument[2, col]
                t2 = t2 + err[0, col] * err[0, col]

            err_norm = np.sqrt(t1) / np.sqrt(t2)

            for col in range(4):
                z2[0, col] = err_norm * err[0, col] * 2

        k = 0

        for row in range(beam_count):
            for col in range(beam_count):
                if row <= 2:
                    beam_matrix[row, col] = b_2_instrument[row, col]
                else:
                    beam_matrix[row, col] = z2[0, col]
                k = k + 1
        self.matrix[:, :, n] = beam_matrix
