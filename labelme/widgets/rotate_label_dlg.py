#!/usr/bin/env python
# -*- coding: utf-8 -*-

from qtpy import QtWidgets, QtCore
from qtpy.QtGui import QPainter, QColor, QBrush
from qtpy.QtWidgets import QDialog, QWidget, QHBoxLayout, QVBoxLayout, QRadioButton, QSpinBox
from qtpy.QtCore import QPoint
from qtpy.QtGui import QTransform, QPolygonF, QPen


class AngleBar(QWidget):

    def __init__(self, parent, clockwise, angle, updateRotateInfoCB):
        super(AngleBar, self).__init__(parent)
        self.updateRotateInfoCB = updateRotateInfoCB
        self.rotate_clockwise = clockwise
        self.rotate_angle = angle

        self.mouse_pressing = False
        self.color_background = QColor(200, 0, 0)
        self.color_anglebar = QColor(25, 0, 90, 200)

    def calcRotateInfo(self, ev):
        pos = ev.localPos()
        mouse_posx = int(pos.x())
        angle_zero = self.width() / 2
        self.rotate_clockwise = mouse_posx > angle_zero
        self.rotate_angle = int(abs(mouse_posx - angle_zero) * 360 / angle_zero)
        if self.rotate_angle < 0:
            self.rotate_angle = 0
        elif self.rotate_angle > 360:
            self.rotate_angle = 360
        self.updateRotateInfoCB(self.rotate_clockwise, self.rotate_angle)
        self.repaint()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        w = self.width()
        h = self.height()
        # paint background
        qp.setBrush(self.color_background)
        qp.drawRect(0, 0, w, h)

        # paint angle bar
        qp.setBrush(self.color_anglebar)
        angle_zero_pos = w // 2
        angle_bar_width = int(angle_zero_pos * self.rotate_angle / 360)
        if self.rotate_clockwise:
            qp.drawRect(angle_zero_pos, 0, angle_bar_width, h)
        else:
            qp.drawRect(angle_zero_pos - angle_bar_width, 0, angle_bar_width, h)

        qp.end()

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.mouse_pressing = True
            self.calcRotateInfo(ev)

    def mouseMoveEvent(self, ev):
        if self.mouse_pressing:
            self.calcRotateInfo(ev)

    def mouseReleaseEvent(self, ev):
        self.mouse_pressing = False

    def updateRotationInfo(self, clockwise, angle):
        self.rotate_clockwise = clockwise
        self.rotate_angle = angle
        self.repaint()


class RotateLabelDlg(QDialog):

    rotateSelectedPolygon = QtCore.Signal(bool, int)

    def __init__(self, parent=None, clockwise=True, angle=0):
        super(RotateLabelDlg, self).__init__(parent)
        self.setWindowTitle(self.tr("Rotate the selected polygon"))
        self.clockwise = clockwise
        self.angle = angle
        self.setLayout(self.createLayout())

    def createLayout(self):
        hbox = QHBoxLayout()
        self.radio_clockwise = QRadioButton(self.tr("clockwise"), self)
        self.radio_clockwise.clockwise = True
        self.radio_clockwise.setChecked(self.clockwise)
        self.radio_clockwise.toggled.connect(self.rotationDirectionChanged)

        self.radio_anticlockwise = QRadioButton(self.tr("anticlockwise"), self)
        self.radio_anticlockwise.clockwise = False
        self.radio_anticlockwise.setChecked(not self.clockwise)
        self.radio_anticlockwise.toggled.connect(self.rotationDirectionChanged)

        self.angle_editor = QSpinBox(self)
        self.angle_editor.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.angle_editor.setRange(0, 360)
        self.angle_editor.setSuffix(" °")
        self.angle_editor.setValue(self.angle)
        self.angle_editor.setToolTip("rotation angle")
        self.angle_editor.setStatusTip(self.toolTip())
        self.angle_editor.setAlignment(QtCore.Qt.AlignCenter)
        self.angle_editor.valueChanged.connect(self.rotationAngleChanged)

        hbox.addWidget(self.radio_anticlockwise)
        hbox.addWidget(self.radio_clockwise)
        hbox.addWidget(self.angle_editor)

        self.rotate_bar = AngleBar(self, self.clockwise, self.angle, self.angleBarChanged)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.rotate_bar)
        return vbox

    def rotationDirectionChanged(self, value):
        # radio button
        rbtn = self.sender()
        if rbtn.isChecked():
            self.clockwise = rbtn.clockwise
            self.rotate_bar.updateRotationInfo(self.clockwise, self.angle)
            self.appleRotateInfo()

    def rotationAngleChanged(self, value):
        # spinbox
        if value != self.angle:
            self.angle = value
            self.rotate_bar.updateRotationInfo(self.clockwise, self.angle)
            self.appleRotateInfo()

    def angleBarChanged(self, clockwise, angle):
        if self.clockwise == clockwise and self.angle == angle:
            return
        self.clockwise = clockwise
        self.angle = angle

        self.angle_editor.setValue(self.angle)
        if self.clockwise and not self.radio_clockwise.isChecked():
            self.radio_clockwise.setChecked(True)
        elif not self.clockwise and not self.radio_anticlockwise.isChecked():
            self.radio_anticlockwise.setChecked(True)
        else:
            self.appleRotateInfo()

    def appleRotateInfo(self):
        self.rotateSelectedPolygon.emit(self.clockwise, self.angle)

    # def paintEvent(self, ev):
    #     painter = QPainter()
    #     painter.begin(self)
    #
    #     # [0, 0], [1, 0], [1, 1], [0.5, 1.5], [0, 1]
    #     a = QPoint(100, 100)
    #     b = QPoint(200, 100)
    #     c = QPoint(200, 200)
    #     d = QPoint(150, 250)
    #     e = QPoint(100, 200)
    #     center = QPoint(150, 150)
    #
    #     painter.setPen(QPen(QColor(QtCore.Qt.red), 4))
    #     pointer = QPolygonF([a, b, c, d, e])
    #     painter.drawPolygon(pointer)
    #     painter.drawPoint(center)
    #
    #     transform = QTransform()
    #     transform.translate(center.x(), center.y())
    #     transform.rotate(45)
    #     transform.translate(-center.x(), -center.y())
    #
    #     painter.setPen(QPen(QColor(QtCore.Qt.green), 4))
    #     pointer = transform.map(pointer)
    #     painter.drawPolygon(pointer)
    #     painter.drawPoint(center)
    #
    #     painter.setPen(QPen(QColor(QtCore.Qt.blue), 4))
    #     for i, p in enumerate(pointer):
    #         painter.drawText(p, str(i))
    #
    #     painter.end()
    #
    #     pass

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dlg = RotateLabelDlg()
    dlg.setMinimumSize(400, 100)
    dlg.show()
    sys.exit(app.exec_())