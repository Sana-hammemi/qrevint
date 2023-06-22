# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wRating.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_rating(object):
    def setupUi(self, rating):
        rating.setObjectName("rating")
        rating.resize(556, 246)
        self.gridLayout_2 = QtWidgets.QGridLayout(rating)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.txt_rating_msg = QtWidgets.QLabel(rating)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.txt_rating_msg.setFont(font)
        self.txt_rating_msg.setWordWrap(True)
        self.txt_rating_msg.setObjectName("txt_rating_msg")
        self.verticalLayout_2.addWidget(self.txt_rating_msg)
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout_2.addItem(spacerItem1)
        self.Uncertainty_label = QtWidgets.QLabel(rating)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.Uncertainty_label.setFont(font)
        self.Uncertainty_label.setObjectName("Uncertainty_label")
        self.horizontalLayout_2.addWidget(self.Uncertainty_label)
        spacerItem2 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout_2.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem3 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout.addItem(spacerItem3)
        self.uncertainty_value = QtWidgets.QLabel(rating)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.uncertainty_value.setFont(font)
        self.uncertainty_value.setText("")
        self.uncertainty_value.setObjectName("uncertainty_value")
        self.horizontalLayout.addWidget(self.uncertainty_value)
        self.uncertainty_units = QtWidgets.QLabel(rating)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.uncertainty_units.setFont(font)
        self.uncertainty_units.setObjectName("uncertainty_units")
        self.horizontalLayout.addWidget(self.uncertainty_units)
        spacerItem4 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout.addItem(spacerItem4)
        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(3, 2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        spacerItem5 = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout_2.addItem(spacerItem5)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.gb_rating = QtWidgets.QGroupBox(rating)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.gb_rating.setFont(font)
        self.gb_rating.setObjectName("gb_rating")
        self.gridLayout = QtWidgets.QGridLayout(self.gb_rating)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.rb_excellent = QtWidgets.QRadioButton(self.gb_rating)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.rb_excellent.setFont(font)
        self.rb_excellent.setChecked(True)
        self.rb_excellent.setObjectName("rb_excellent")
        self.verticalLayout.addWidget(self.rb_excellent)
        self.rb_good = QtWidgets.QRadioButton(self.gb_rating)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.rb_good.setFont(font)
        self.rb_good.setObjectName("rb_good")
        self.verticalLayout.addWidget(self.rb_good)
        self.rb_fair = QtWidgets.QRadioButton(self.gb_rating)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.rb_fair.setFont(font)
        self.rb_fair.setObjectName("rb_fair")
        self.verticalLayout.addWidget(self.rb_fair)
        self.rb_poor = QtWidgets.QRadioButton(self.gb_rating)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.rb_poor.setFont(font)
        self.rb_poor.setObjectName("rb_poor")
        self.verticalLayout.addWidget(self.rb_poor)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.horizontalLayout_3.addWidget(self.gb_rating)
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(rating)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok
        )
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout_2.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(rating)
        self.buttonBox.accepted.connect(rating.accept)
        self.buttonBox.rejected.connect(rating.reject)
        QtCore.QMetaObject.connectSlotsByName(rating)

    def retranslateUi(self, rating):
        _translate = QtCore.QCoreApplication.translate
        rating.setWindowTitle(_translate("rating", "Rating"))
        self.txt_rating_msg.setText(
            _translate(
                "rating",
                '<html><head/><body><p><span style=" font-weight:600;">IMPORTANT:</span> The rating for a measurement should include the uncertainty of the stage associated with the measurement in addition to the uncertainty of the discharge.</p></body></html>',
            )
        )
        self.Uncertainty_label.setText(
            _translate("rating", "QRev Estimated Uncertainty")
        )
        self.uncertainty_units.setText(_translate("rating", "%"))
        self.gb_rating.setTitle(_translate("rating", "Rating:"))
        self.rb_excellent.setText(_translate("rating", "Excellent (< 3%)"))
        self.rb_good.setText(_translate("rating", "Good (3 - 5 %)"))
        self.rb_fair.setText(_translate("rating", "Fair (5 - 8 %)"))
        self.rb_poor.setText(_translate("rating", "Poor (> 8 %)"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    rating = QtWidgets.QDialog()
    ui = Ui_rating()
    ui.setupUi(rating)
    rating.show()
    sys.exit(app.exec_())
