import hou
import os
import csv
import random
from hutil.Qt.QtCore import *
from hutil.Qt.QtGui import *
from hutil.Qt.QtWidgets import *


class Tip_Dialog(QDialog):
    def __init__(self, parent):
        super(Tip_Dialog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Quick Tips!")

        self.csvfile = hou.expandString("$SIDEFXLABS/misc/tips/Tip_Data.csv")

        self.build_ui()
        self.NextTip()
        

    def closeEvent(self, event):
        pass
        
    def NextTip(self):
        with open(self.csvfile,"r") as data:
            csv_reader = csv.reader(data)
            tips = list(csv_reader)
            random_tip = random.choice(tips)[0]
            self.tip_label.setText(random_tip)


    def build_ui(self):

      self.setMinimumSize(650, 100)

      layout = QVBoxLayout()

      self.tip_label = QLabel("Some Tip")
      tip_label_layout = QHBoxLayout()
      tip_label_layout.addWidget(self.tip_label)
      self.tip_label.setWordWrap(True)

      Next_btn = QPushButton("Next Tip")
      Next_btn.clicked.connect(self.NextTip)

      buttons_layout = QHBoxLayout()
      buttons_layout.addWidget(Next_btn)

      layout.addLayout(tip_label_layout)
      layout.addLayout(buttons_layout)

      self.setLayout(layout)
      #self.setFixedHeight(self.sizeHint().height()) 


dialog = Tip_Dialog(hou.ui.mainQtWindow())
dialog.exec_()