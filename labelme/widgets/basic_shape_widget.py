#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QSize
from qtpy.QtGui import QIcon, QMouseEvent
from qtpy.QtWidgets import QWidget, QPushButton, QVBoxLayout, QGridLayout, QScrollArea
from utils.qt import newIcon


class BasicShapeButton(QPushButton):

    def __init__(self, parent, shape_name, icon, btn_tip, callback):
        super(BasicShapeButton, self).__init__(parent)
        self.shape_name = shape_name
        self.icon = icon
        self.setIcon(newIcon("{}_unselected".format(self.icon)))
        self.setIconSize(QSize(48, 48))
        self.setFixedSize(48, 48)
        self.setToolTip(btn_tip)
        self.selected = False
        self.callback = callback

    def changeStatus(self, selected):
        self.selected = selected
        if self.selected:
            self.setIcon(newIcon("{}_selected".format(self.icon)))
        else:
            self.setIcon(newIcon("{}_unselected".format(self.icon)))

    def mousePressEvent(self, e: QMouseEvent):
        self.callback(self)


class BasicShapeWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.selected_shape_item = None
        self.shape_item_list = None
        self.createSelector()

    def basic_shape_changed(self, basic_shape_item):
        for item in self.shape_item_list:
            if item.shape_name == basic_shape_item.shape_name:
                item.changeStatus(not item.selected)
            elif item.selected:
                item.changeStatus(False)

    def createSelector(self):
        # create shape items
        item_round_rectangle = BasicShapeButton(self, "round_rectangle", "round_rectangle", "round rectangle",
                                                self.basic_shape_changed)
        item_surface_A = BasicShapeButton(self, "surface_A", "surface_A", "surface A", self.basic_shape_changed)
        item_logo_apple_stalk = BasicShapeButton(self, "apple_stalk", "logo_apple_stalk", "logo apple stalk",
                                                 self.basic_shape_changed)
        item_logo_apple_body = BasicShapeButton(self, "apple body", "logo_apple_body", "logo apple body",
                                                self.basic_shape_changed)
        self.shape_item_list = [item_round_rectangle, item_surface_A, item_logo_apple_stalk, item_logo_apple_body]

        # create layout
        layout = QGridLayout(self)
        layout.addWidget(item_round_rectangle, 0, 0)
        layout.addWidget(item_surface_A, 0, 1)
        layout.addWidget(item_logo_apple_stalk, 0, 2)
        layout.addWidget(item_logo_apple_body, 0, 3)

        shape_items = QWidget(self)
        shape_items.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidget(shape_items)
        scroll.setWidgetResizable(True)

        shape_widget_layout = QVBoxLayout(self)
        shape_widget_layout.addWidget(scroll)

        self.setLayout(shape_widget_layout)

    def getSelectedBasicShape(self):
        basic_shape_name = None
        for item in self.shape_item_list:
            if item.selected:
                basic_shape_name = item.shape_name
        return basic_shape_name

