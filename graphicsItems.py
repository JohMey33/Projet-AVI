from PyQt5 import QtWidgets
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QTransform
from PyQt5.QtCore import Qt
import numpy as np
import geometry

RAD2DEG = 180/np.pi

# Waypoints width
WP_WIDTH = 15
WP_DP = WP_WIDTH/2.
TP_WIDTH = 10
TP_DP = TP_WIDTH/2.
ASW = 0.3 # ASW stands for Arc Semi Width

# Aicraft width
AC_WIDTH = 100

# Pens
P_PEN = QPen(Qt.transparent)
TRAJ_PEN = QPen(QColor(255, 255, 0),ASW*2)
LEG_PEN = QPen(QColor("lightgrey"), ASW)

# Brushes
TP_BRUSH = QBrush(QColor("grey"))
WP_BRUSH = QBrush(QColor("red"))
AC_BRUSH = QBrush(QColor("white")) # for the aicraft

# Coefficient multiplicateur pour les arc. Un cercle complet = 360*16
SP_ANGLE_COEFF = 16


class QGraphicsArcItem(QtWidgets.QGraphicsEllipseItem):
    """Classe graphique qui affiche un arc de cercle,
    comme portion du cercle commençant à start_angle et finissant à
    start_angle + span_angle"""
    def __init__(self, start, centre, alpha, turnRadius, det, parent):
        self.det = det #déterminant entre les deux segments de la transition
        self.set_XY(centre, turnRadius+ASW)
        self.w, self.h = (turnRadius+ASW)*2, (turnRadius+ASW)*2
        super().__init__(self.x, self.y, self.w, self.h, parent)
        self.set_span_angle(alpha)
        self.start_angle = self.set_start_angle(start, centre)

    def paint(self, painter=QPainter(), style=None, widget=None):
        painter.setPen(TRAJ_PEN)
        painter.translate(3*ASW, 3*ASW)
        if self.det < 0:
            painter.drawArc(self.x, self.y, self.w, self.h, self.start_angle, self.span_angle)
        else:
            painter.drawArc(self.x, self.y, self.w, self.h, self.start_angle, -self.span_angle)

    def set_span_angle(self, alpha):
        self.span_angle = alpha * SP_ANGLE_COEFF

    def set_start_angle(self, start, centre):
        beta = np.arctan((start.y - centre.y) / (start.x - centre.x)) * RAD2DEG
        if start.x < centre.x:
            return -(180 + beta) * SP_ANGLE_COEFF
        else:
            return -beta * SP_ANGLE_COEFF

    def set_XY(self, centre, turnRadius):
        self.x = centre.x - turnRadius - ASW
        self.y = centre.y - turnRadius - ASW



class QGraphicsWayPointsItem(QtWidgets.QGraphicsRectItem):
    """Affichage des Way Points"""
    def __init__(self, x, y, parent):
        self.x, self.y = x, y
        super().__init__(x, y, WP_WIDTH, WP_WIDTH, parent)
        self.paint(QPainter())

    def paint(self, painter, style=None, widget=None):
        painter.setPen(P_PEN)
        painter.setBrush(WP_BRUSH)

        # copie la transformation due au zoom
        t = painter.transform()
        m11, m22 = t.m11(), t.m22()

        # fixé les coefficients de translation horizontale m11 et verticale m22 à 1
        painter.setTransform(QTransform(1, t.m12(), t.m13(), t.m21(), 1, t.m23(), t.m31(), t.m32(), t.m33()))

        # the item itself will not be scaled, but when the scene is transformed
        # this item still anchor correctly
        painter.translate(-WP_DP, -WP_DP) # translate de -WP_DP pour s'affranchir de l'épaisseur de l'item
        painter.drawRect(self.x*m11, self.y*m22, WP_WIDTH, WP_WIDTH)

        painter.restore()

class QGraphicsTransitionPoints(QtWidgets.QGraphicsRectItem):
    def __init__(self, x, y, parent):
        super().__init__(x, y, TP_WIDTH, TP_WIDTH, parent)
        self.x, self.y = x, y
        self.paint(QPainter())

    def paint(self, painter, style=None, widget=None):
        painter.setPen(P_PEN)
        painter.setBrush(TP_BRUSH)

        # copie la transformation due au zoom
        t = painter.transform()
        m11, m22 = t.m11(), t.m22()

        # fixé les coefficients de translation horizontale m11 et verticale m22 à 1
        painter.setTransform(QTransform(1, t.m12(), t.m13(), t.m21(), 1, t.m23(), t.m31(), t.m32(), t.m33()))

        # the item itself will not be scaled, but when the scene is transformed
        # this item still anchor correctly
        painter.translate(-TP_DP, -TP_DP) # translate de -TP_DP pour s'affranchir de l'épaisseur de l'item
        painter.drawRect(self.x * m11, self.y * m22, TP_WIDTH, TP_WIDTH)
        painter.restore()


class QGraphicsLegsItem(QtWidgets.QGraphicsLineItem):
    """Affichage des legs"""
    def __init__(self, x1, y1, x2, y2, parent):
        super().__init__(x1, y1, x2, y2, parent)
        self.pen = LEG_PEN


class AircraftItem(QtWidgets.QGraphicsItemGroup):
    """The view of an aircraft in the GraphicsScene"""

    def __init__(self):
        """AircraftItem constructor, creates the ellipse and adds to the scene"""
        super().__init__(None)
        self.item = QtWidgets.QGraphicsEllipseItem()
        self.item.setBrush(AC_BRUSH)
        self.addToGroup(self.item)

    def update_position(self, x, y):
        self.item.setPos(x, y)
        self.item.setRect(x - AC_WIDTH / 2, y - AC_WIDTH / 2, AC_WIDTH, AC_WIDTH)