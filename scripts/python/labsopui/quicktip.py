import hou
import csv
import random

from hutil.Qt import QtCore, QtWidgets

class Tip_Dialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super(Tip_Dialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Quick Tips")

        self.csvfile = hou.text.expandString("$SIDEFXLABS/misc/tips/Tip_Data.csv")
        self.numtips = 0
        self.currenttip = 0
        self.build_ui()
        self.Randomize()
        self.UpdateTip()

    def Randomize(self):
        with open(self.csvfile,"r") as data:
            self.numtips = sum(1 for row in data)
        self.currenttip = random.randint(0, self.numtips)


    def TipAtIndex(self, index):
        with open(self.csvfile,"r") as data:
            csv_reader = csv.reader(data)
            tips = list(csv_reader)
            return tips[index][0]

    def UpdateTip(self):
        self.tip_label.setText("({0}/{1}) {2}".format(self.currenttip+1, self.numtips, self.TipAtIndex(self.currenttip) ))

    def closeEvent(self, event):
        pass

    def RandomTip(self):
        self.Randomize()
        self.UpdateTip()


    def PrevTip(self):
        self.currenttip = max(0, self.currenttip-1)
        self.UpdateTip()

    def NextTip(self):
        self.currenttip = min(self.numtips-1, self.currenttip+1)
        self.UpdateTip()


    def build_ui(self):

        self.setMinimumSize(650, 100)

        layout = QtWidgets.QVBoxLayout()

        self.tip_label = QtWidgets.QLabel("Some Tip")
        tip_label_layout = QtWidgets.QHBoxLayout()
        tip_label_layout.addWidget(self.tip_label)
        self.tip_label.setWordWrap(True)

        Prev_btn = QtWidgets.QPushButton("Previous")
        Prev_btn.clicked.connect(self.PrevTip)

        Next_btn = QtWidgets.QPushButton("Next")
        Next_btn.clicked.connect(self.NextTip)

        Random_btn = QtWidgets.QPushButton("Random")
        Random_btn.clicked.connect(self.RandomTip)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(Prev_btn)
        buttons_layout.addWidget(Next_btn)
        buttons_layout.addWidget(Random_btn)

        layout.addLayout(tip_label_layout)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)


def ShowQuickTip():
    dialog = Tip_Dialog(hou.qt.mainWindow())
    dialog.show()
