from datetime import datetime

from PyQt5 import QtCore
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from qrev.MiscLibs.local_time_utilities import utc_offset_to_tz

class PDFEdiReport:
    """Generate a PDF report for EDI tab."""

    def __init__(self, pdf_fullname, parent):
        """Construct EDI report doc.

        Parameters
        ----------
        pdf_fullname: str
            Filename of pdf file including path.
        parent: QRev
            Main object
        """

        self.parent = parent
        self.doc = SimpleDocTemplate(
            pdf_fullname,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=90,
            bottomMargin=36,
        )
        self.elements = []
        self.styles = getSampleStyleSheet()
        self.width, self.height = letter
        self.tr = self.parent.tr

        self.units = self.parent.units

        self.header_style = TableStyle(
            [
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.black,
                ),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )

        self.table_style = TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.black,
                ),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )

    def site_info(self):
        """Create the site info header table.

        Returns
        -------
        table : Table
            Site info table
        """
        start = self.parent.meas.transects[
            self.parent.meas.checked_transect_idx[0]
        ].date_time.start_serial_time
        tz_local = utc_offset_to_tz(self.parent.meas.checked_transect_idx[0].date_time.utc_time_offset)
        date = datetime.fromtimestamp(start, tz=tz_local).strftime(self.parent.date_format)

        data = [
            [self.tr("Station Name"), self.parent.meas.station_name],
            [self.tr("Station Number"), self.parent.meas.station_number],
            [self.tr("Measurement Date"), date],
            [self.tr("Person(s)"), self.parent.meas.persons],
            [
                self.parent.version.split(" ")[0],
                self.tr("Version") + " " + self.parent.version.split(" ")[1],
            ],
        ]

        table = Table(data, hAlign="LEFT")

        table.setStyle(self.header_style)

        return table

    def edi_transects_table(self):
        """Create the transects table.

        Returns
        -------
        table : Table
            Info from top table on EDI tab
        """
        tbl_edi_transect = self.parent.tbl_edi_transect

        data = [
            [
                " ",
                self.tr("Transect"),
                "Start",
                "Bank",
                "End",
                "Duration\n(sec)",
                "Total Q\n" + self.units["label_Q"],
                "Top Q\n" + self.units["label_Q"],
                "Meas Q\n" + self.units["label_Q"],
                "Bottom Q\n" + self.units["label_Q"],
                "Left Q\n" + self.units["label_Q"],
                "Right Q\n" + self.units["label_Q"],
            ]
        ]

        for row in range(tbl_edi_transect.rowCount()):
            if tbl_edi_transect.item(row, 0).checkState() == QtCore.Qt.Checked:
                marker = "X"
            else:
                marker = " "

            # Transect names can be long: split over multiple lines if too long
            transect_name_text = tbl_edi_transect.item(row, 0).text()
            transect_name = "\n".join(
                transect_name_text[i : i + 16]
                for i in range(0, len(transect_name_text), 16)
            )

            row_data = [tbl_edi_transect.item(row, col).text() for col in range(1, 11)]
            row_data.insert(0, transect_name)
            row_data.insert(0, marker)
            data.append(row_data)

        table = Table(data)

        table.setStyle(self.table_style)

        return table

    def edi_offset_text(self):
        """Create the EDI offset text.

        Returns
        -------
        sentence : str
            Text with offset and bank information
        """
        try:
            offset = float(self.parent.edi_offset.text())
        except ValueError:
            offset = 0

        edi_bank = self.parent.txt_edi_bank.text()
        edi_offset = self.parent.txt_edi_offset.text()

        sentence = edi_offset + ": " + str(offset) + " " + edi_bank
        return sentence

    def edi_results_table(self):
        """Create the results table.

        Returns
        -------
        table : Table
            Info from bottom table on EDI tab
        """
        tbl_edi_results = self.parent.tbl_edi_results

        data = [
            [
                self.tr("Percent Q"),
                self.tr("Target Q ") + self.units["label_Q"],
                "Actual Q " + self.units["label_Q"],
                "Distance " + self.units["label_L"],
                "Depth " + self.units["label_L"],
                "Velocity " + self.units["label_V"],
                "Latitude (D M.M)",
                "Longitude (D M.M)",
            ]
        ]

        for row in range(tbl_edi_results.rowCount()):
            row_data = [tbl_edi_results.item(row, col).text() for col in range(0, 8)]
            data.append(row_data)

        table = Table(data)

        table.setStyle(self.table_style)

        return table

    def header(self, page, doc):
        """Create header for each page of report.

        Parameters
        ----------
        page: Canvas
            Object of Canvas
        doc: SimpleDocTemplate
            Object of SimpleDocTemplate, required
        """

        qrev_icon = self.parent.get_icon()
        title_str = self.tr("EDI Results")

        logo = Image(qrev_icon, width=30, height=30)
        title = "<font size=14><b>" + title_str + "</b></font>"

        # Logo
        logo.wrapOn(page, self.width, self.height)
        logo.drawOn(page, 0.6 * inch, self.height - 0.65 * inch)

        # Title
        p = Paragraph(title, self.styles["Normal"])
        p.wrapOn(page, self.width, self.height)
        p.drawOn(page, 1.1 * inch, self.height - 0.5 * inch)

    def create(self):
        """Create pdf document using flowtables."""

        # styles = getSampleStyleSheet()

        # Header with site info
        self.elements.append(self.site_info())
        self.elements.append(Spacer(1, 14))

        # Transect information table
        self.elements.append(self.edi_transects_table())
        self.elements.append(Spacer(1, 14))

        # EDI results table
        offset_text = f"<para align=center>{self.edi_offset_text()}</para>"
        offset_para = Paragraph(offset_text)
        self.elements.append(offset_para)
        self.elements.append(Spacer(1, 14))
        self.elements.append(self.edi_results_table())

        self.save()

    def save(self):
        """Build and save pdf file."""

        self.doc.build(self.elements, onFirstPage=self.header, onLaterPages=self.header)
