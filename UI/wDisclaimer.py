# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wDisclaimer.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Disclaimer(object):
    def setupUi(self, Disclaimer):
        Disclaimer.setObjectName("Disclaimer")
        Disclaimer.resize(879, 586)
        self.gridLayout = QtWidgets.QGridLayout(Disclaimer)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.disclaimer_title = QtWidgets.QLabel(Disclaimer)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.disclaimer_title.setFont(font)
        self.disclaimer_title.setObjectName("disclaimer_title")
        self.verticalLayout.addWidget(self.disclaimer_title)
        self.disclaimer_and_license_text = QtWidgets.QTextEdit(Disclaimer)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.disclaimer_and_license_text.setFont(font)
        self.disclaimer_and_license_text.setInputMethodHints(QtCore.Qt.ImhNone)
        self.disclaimer_and_license_text.setReadOnly(True)
        self.disclaimer_and_license_text.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.disclaimer_and_license_text.setObjectName("disclaimer_and_license_text")
        self.verticalLayout.addWidget(self.disclaimer_and_license_text)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtWidgets.QLabel(Disclaimer)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setItalic(False)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.buttonBox = QtWidgets.QDialogButtonBox(Disclaimer)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.No|QtWidgets.QDialogButtonBox.Yes)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(Disclaimer)
        self.buttonBox.accepted.connect(Disclaimer.accept)
        self.buttonBox.rejected.connect(Disclaimer.reject)
        QtCore.QMetaObject.connectSlotsByName(Disclaimer)

    def retranslateUi(self, Disclaimer):
        _translate = QtCore.QCoreApplication.translate
        Disclaimer.setWindowTitle(_translate("Disclaimer", "Disclaimer and License Acceptance"))
        self.disclaimer_title.setText(_translate("Disclaimer", "Disclaimer and License "))
        self.disclaimer_and_license_text.setHtml(_translate("Disclaimer", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">DISCLAIMER</span><br />This software (QRevInt) is a fork of QRev, which was originally approved for release by the U.S. Geological Survey (USGS), IP-118174. Genesis HydroTech LLC through funding from various international agencies is working to improve and expand the capabilities and features available in QRevInt. While Genesis HydroTech LLC makes every effort to deliver high quality products, Genesis HydroTech LLC does not guarantee that the product is free from defects. QRevInt is provided “as is,&quot; and you use the software at your own risk. Genesis HydroTech LLC and contributing agencies make no warranties as to performance, merchantability, fitness for a particular purpose, or any other warranties whether expressed or implied. No oral or written communication from or information provided by Genesis HydroTech LLC or contributing agencies shall create a warranty. Under no circumstances shall Genesis HydroTech LLC or the contributing agencies be liable for direct, indirect, special, incidental, or consequential damages resulting from the use, misuse, or inability to use this software, even if Genesis HydroTech LLC or the contributing agencies have been advised of the possibility of such damages.<br /><br /><span style=\" font-weight:600;\">LICENSE</span><br />Unless otherwise noted, this project is in the public domain in the United States because it contains materials that originally came from the United States Geological Survey, an agency of the United States Department of Interior. For more information, see the official USGS copyright policy at https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits. Additionally, Genesis HydroTech LLC waives copyright and related rights in the work worldwide through the CC0 1.0 Universal public domain dedication.<br /><br />QRevInt includes several open-source software packages. These open-source packages are governed by the terms and conditions of the applicable open-source license, and you are bound by the terms and conditions of the applicable open-source license in connection with your use and distribution of the open-source software in this product. <br /><br /><span style=\" font-weight:600;\">Copyright / License - CC0 1.0</span>: The person who associated a work with this deed has dedicated the work to the public domain by waiving all of his or her rights to the work worldwide under copyright law, including all related and neighboring rights, to the extent allowed by law. You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission. <br /><br />In no way are the patent or trademark rights of any person affected by CC0, nor are the rights that other persons may have in the work or in how the work is used, such as publicity or privacy rights.<br /><br />Unless expressly stated otherwise, the person who associated a work with this deed makes no warranties about the work, and disclaims liability for all uses of the work, to the fullest extent permitted by applicable law.<br /><br />When using or citing the work, you should not imply endorsement by the author or the affirmer.<br /><br /><span style=\" font-weight:600;\">Publicity or privacy</span>: The use of a work free of known copyright restrictions may be otherwise regulated or limited. The work or its use may be subject to personal data protection laws, publicity, image, or privacy rights that allow a person to control how their voice, image or likeness is used, or other restrictions or limitations under applicable law.<br /><br /><span style=\" font-weight:600;\">Endorsement</span>: In some jurisdictions, wrongfully implying that an author, publisher or anyone else endorses your use of a work may be unlawful. </p></body></html>"))
        self.label.setText(_translate("Disclaimer", "Do you agree to the disclaimer and license?"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Disclaimer = QtWidgets.QDialog()
    ui = Ui_Disclaimer()
    ui.setupUi(Disclaimer)
    Disclaimer.show()
    sys.exit(app.exec_())
