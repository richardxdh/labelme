#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt
from qtpy.QtWidgets import QWidget, QGridLayout, QLabel, QProgressBar, QGroupBox, QVBoxLayout, QFormLayout, QScrollArea


class ScaleWidget(QWidget):


    def __init__(self):
        super().__init__()

        formLayout = self.createLayout()
        scales = QWidget(self)
        scales.setLayout(formLayout)

        scroll = QScrollArea()
        scroll.setWidget(scales)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

        self.setLayout(layout)


    def createScaleBar(self, barlen):
        pb = QProgressBar(self)
        pb.setAlignment(Qt.AlignCenter) 
        pb.setStyleSheet("QProgressBar {border: solid grey; border-radius: 0px; color: black; } \
                          QProgressBar::chunk {background-color: #00AAFF; border-radius:0px;}") 
        pb.setValue(100)
        pb.setFixedSize(barlen, 6)
        pb.setTextVisible(False)
        return pb


    def createLayout(self):

        layout = QFormLayout()

        # 5 pixel
        self.pb5 = self.createScaleBar(5)
        layout.addRow(QLabel("  5 pixels:"), self.pb5)

        # 50 pixel
        self.pb50 = self.createScaleBar(50)
        layout.addRow(QLabel(" 50 pixels:"), self.pb50)

        # 100 pixel
        self.pb100 = self.createScaleBar(100)
        layout.addRow(QLabel("100 pixels:"), self.pb100)

        return layout


    def updateScale(self, scale5, scale50, scale100):
        self.pb5.setFixedWidth(scale5)
        self.pb50.setFixedWidth(scale50)
        self.pb100.setFixedWidth(scale100)
