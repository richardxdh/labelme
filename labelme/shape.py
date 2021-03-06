import copy
import math

import numpy as np
from qtpy import QtCore
from qtpy import QtGui
from qtpy.QtGui import QPolygonF

import labelme.utils


# TODO(unknown):
# - [opt] Store paths instead of creating new ones at each paint.


DEFAULT_LINE_COLOR = QtGui.QColor(0, 255, 0, 128)  # bf hovering
DEFAULT_FILL_COLOR = QtGui.QColor(0, 255, 0, 128)  # hovering
DEFAULT_SELECT_LINE_COLOR = QtGui.QColor(255, 255, 255)  # selected
DEFAULT_SELECT_FILL_COLOR = QtGui.QColor(0, 255, 0, 155)  # selected
DEFAULT_VERTEX_FILL_COLOR = QtGui.QColor(0, 255, 0, 255)  # hovering
DEFAULT_HVERTEX_FILL_COLOR = QtGui.QColor(255, 255, 255, 255)  # hovering


class Shape(object):

    P_SQUARE, P_ROUND = 0, 1

    MOVE_VERTEX, NEAR_VERTEX = 0, 1

    # The following class variables influence the drawing of all shape objects.
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 8
    scale = 1.0

    def __init__(
        self,
        label=None,
        line_color=None,
        shape_type=None,
        flags=None,
        group_id=None,
    ):
        self.label = label
        self.group_id = group_id
        self.points = []
        self.fill = False
        self.selected = False
        self.shape_type = shape_type
        self.flags = flags
        self.other_data = {}

        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            # with an object attribute. Currently this
            # is used for drawing the pending line a different color.
            self.line_color = line_color

        self.shape_type = shape_type

        self.inner_points = None
        self.last_inner_points = None
        self.resizing_box_points = None
        self.rotating_points = None
        self.rotating_center = None

    @property
    def shape_type(self):
        return self._shape_type

    @shape_type.setter
    def shape_type(self, value):
        if value is None:
            value = "polygon"
        if value not in [
            "polygon",
            "rectangle",
            "point",
            "line",
            "circle",
            "linestrip",
            "resizingshape",
        ]:
            raise ValueError("Unexpected shape_type: {}".format(value))
        self._shape_type = value

    def close(self):
        self._closed = True

    def addPoint(self, point):
        if self.points and point == self.points[0]:
            self.close()
        else:
            self.points.append(point)

    def canAddPoint(self):
        return self.shape_type in ["polygon", "linestrip"]

    def popPoint(self):
        if self.points:
            return self.points.pop()
        return None

    def insertPoint(self, i, point):
        self.points.insert(i, point)

    def removePoint(self, i):
        self.points.pop(i)

    def isClosed(self):
        return self._closed

    def setOpen(self):
        self._closed = False

    def getRectFromLine(self, pt1, pt2):
        x1, y1 = pt1.x(), pt1.y()
        x2, y2 = pt2.x(), pt2.y()
        return QtCore.QRectF(x1, y1, x2 - x1, y2 - y1)

    def updateInnerPoints(self):
        outer_rect = self.getRectFromLine(*self.points)
        # inner_polygon = QPolygonF(self.inner_points)
        # inner_bounding_rect = inner_polygon.boundingRect()
        # scaleX = outer_rect.width() / inner_bounding_rect.width()
        # scaleY = outer_rect.height() / inner_bounding_rect.height()
        # inner_center = inner_bounding_rect.center()
        # inner_points = [p - inner_center for p in self.inner_points]
        # inner_points = [QtCore.QPointF(p.x()*scaleX, p.y()*scaleY) +
        #                 outer_rect.center() for p in inner_points]
        x1, y1 = self.inner_points.min(axis=0)
        x2, y2 = self.inner_points.max(axis=0)
        inner_bounding_rect_width = x2 - x1
        inner_bounding_rect_height = y2 - y1
        scaleX = outer_rect.width() / inner_bounding_rect_width
        scaleY = outer_rect.height() / inner_bounding_rect_height
        inner_center = ((x1 + x2) / 2, (y1 + y2) / 2)
        inner_points = self.inner_points - inner_center
        inner_points = [QtCore.QPointF(p[0]*scaleX, p[1]*scaleY) +
                             outer_rect.center() for p in inner_points]
        self.last_inner_points = np.array([[p.x(), p.y()] for p in inner_points])
        return inner_points

    def paintInnerShape(self, painter):
        if self.inner_points is not None:
            inner_points = self.updateInnerPoints()
            pen = QtGui.QPen(self.select_line_color)
            pen.setWidth(max(1, int(round(2.0 / self.scale))))
            pen.setStyle(QtCore.Qt.DashLine)
            painter.setPen(pen)
            line_path = QtGui.QPainterPath()
            vrtx_path = QtGui.QPainterPath()
            line_path.moveTo(inner_points[0])
            for i, p in enumerate(inner_points):
                line_path.lineTo(p)
                self.drawInnerVertex(vrtx_path, inner_points[i])
            line_path.lineTo(inner_points[0])
            painter.drawPath(line_path)
            painter.drawPath(vrtx_path)
            painter.fillPath(vrtx_path, self.vertex_fill_color)

    def paint(self, painter):
        if self.points:
            color = (
                self.select_line_color if self.selected else self.line_color
            )
            pen = QtGui.QPen(color)
            # Try using integer sizes for smoother drawing(?)
            pen.setWidth(max(1, int(round(2.0 / self.scale))))
            painter.setPen(pen)

            line_path = QtGui.QPainterPath()
            vrtx_path = QtGui.QPainterPath()

            if self.shape_type in ["rectangle", "resizingshape"]:
                assert len(self.points) in [1, 2]
                if len(self.points) == 2:
                    rectangle = self.getRectFromLine(*self.points)
                    line_path.addRect(rectangle)
                    # paint inner shape
                    if self.shape_type == "resizingshape" and self.inner_points is not None:
                        self.paintInnerShape(painter)
                        self.fill = False
                for i in range(len(self.points)):
                    self.drawVertex(vrtx_path, i)
            elif self.shape_type == "circle":
                assert len(self.points) in [1, 2]
                if len(self.points) == 2:
                    rectangle = self.getCircleRectFromLine(self.points)
                    line_path.addEllipse(rectangle)
                for i in range(len(self.points)):
                    self.drawVertex(vrtx_path, i)
            elif self.shape_type == "linestrip":
                line_path.moveTo(self.points[0])
                for i, p in enumerate(self.points):
                    line_path.lineTo(p)
                    self.drawVertex(vrtx_path, i)
            else:
                line_path.moveTo(self.points[0])
                # Uncommenting the following line will draw 2 paths
                # for the 1st vertex, and make it non-filled, which
                # may be desirable.
                # self.drawVertex(vrtx_path, 0)

                for i, p in enumerate(self.points):
                    line_path.lineTo(p)
                    self.drawVertex(vrtx_path, i)
                if self.isClosed():
                    line_path.lineTo(self.points[0])

            painter.drawPath(line_path)
            painter.drawPath(vrtx_path)
            painter.fillPath(vrtx_path, self._vertex_fill_color)
            if self.fill:
                color = (
                    self.select_fill_color
                    if self.selected
                    else self.fill_color
                )
                painter.fillPath(line_path, color)

    def drawInnerVertex(self, path, point):
        d = self.point_size / self.scale
        path.addEllipse(point, d / 2.0, d / 2.0)

    def drawVertex(self, path, i):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]
        if i == self._highlightIndex:
            size, shape = self._highlightSettings[self._highlightMode]
            d *= size
        if self._highlightIndex is not None:
            self._vertex_fill_color = self.hvertex_fill_color
        else:
            self._vertex_fill_color = self.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            assert False, "unsupported vertex shape"

    def nearestVertex(self, point, epsilon):
        min_distance = float("inf")
        min_i = None
        for i, p in enumerate(self.points):
            dist = labelme.utils.distance(p - point)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                min_i = i
        return min_i

    def nearestEdge(self, point, epsilon):
        min_distance = float("inf")
        post_i = None
        for i in range(len(self.points)):
            line = [self.points[i - 1], self.points[i]]
            dist = labelme.utils.distancetoline(point, line)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                post_i = i
        return post_i

    def containsPoint(self, point):
        return self.makePath().contains(point)

    def getCircleRectFromLine(self, line):
        """Computes parameters to draw with `QPainterPath::addEllipse`"""
        if len(line) != 2:
            return None
        (c, point) = line
        r = line[0] - line[1]
        d = math.sqrt(math.pow(r.x(), 2) + math.pow(r.y(), 2))
        rectangle = QtCore.QRectF(c.x() - d, c.y() - d, 2 * d, 2 * d)
        return rectangle

    def makePath(self):
        if self.shape_type in ["rectangle", "resizingshape"]:
            path = QtGui.QPainterPath()
            if len(self.points) == 2:
                rectangle = self.getRectFromLine(*self.points)
                path.addRect(rectangle)
        elif self.shape_type == "circle":
            path = QtGui.QPainterPath()
            if len(self.points) == 2:
                rectangle = self.getCircleRectFromLine(self.points)
                path.addEllipse(rectangle)
        else:
            path = QtGui.QPainterPath(self.points[0])
            for p in self.points[1:]:
                path.lineTo(p)
        return path

    def boundingRect(self):
        return self.makePath().boundingRect()

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    def moveVertexBy(self, i, offset):
        self.points[i] = self.points[i] + offset

    def highlightVertex(self, i, action):
        self._highlightIndex = i
        self._highlightMode = action

    def highlightClear(self):
        self._highlightIndex = None

    def copy(self):
        return copy.deepcopy(self)

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value

    def start_resizing_basicshape(self, inner_points=None):
        self.shape_type = "resizingshape"
        if inner_points is not None:
            self.inner_points = inner_points
            self.last_inner_points = inner_points.copy()
        if self.resizing_box_points is not None:
            self.points = [self.resizing_box_points[0],]

    def stop_resizing_basicshape(self):
        self.shape_type = "polygon"
        self.resizing_box_points = self.points
        self.points = [QtCore.QPointF(p[0], p[1]) for p in self.last_inner_points]

    def start_resizing_polygon(self):
        if self.shape_type == "polygon":
            self.shape_type = "resizingshape"
            self.inner_points = np.array([[p.x(), p.y()] for p in self.points])
            self.last_inner_points = self.inner_points.copy()

            x1, y1 = self.last_inner_points.min(axis=0)
            x2, y2 = self.last_inner_points.max(axis=0)
            self.points = [
                QtCore.QPointF(x1, y1),
                QtCore.QPointF(x2, y2),
            ]

    def stop_resizing_polygon(self):
        if self.shape_type == "resizingshape":
            self.shape_type = "polygon"
            if self.last_inner_points is not None:
                self.points = [QtCore.QPointF(p[0], p[1]) for p in self.last_inner_points]

    def startRotatePolygon(self):
        self.rotating_points = self.points.copy()
        # points = np.array([[p.x(), p.y()] for p in self.points])
        # x1, y1 = points.min(axis=0)
        # x2, y2 = points.max(axis=0)
        # cx, cy = ((x1 + x2) / 2, (y1 + y2) / 2)
        rect = self.boundingRect()
        cx = rect.x() + rect.width() // 2
        cy = rect.y() + rect.height() // 2
        self.rotating_center = (cx, cy)

    def rotatePolygon(self, clockwise, angle):
        if self.shape_type == "polygon":

            if clockwise is False:
                angle = -angle

            transform = QtGui.QTransform()
            transform.translate(self.rotating_center[0], self.rotating_center[1])
            transform.rotate(angle)
            transform.translate(-self.rotating_center[0], -self.rotating_center[1])

            polygon = QtGui.QPolygonF(self.rotating_points)
            rotated_polygon = transform.map(polygon)
            self.points = [QtCore.QPointF(int(p.x()), int(p.y())) for p in rotated_polygon]

