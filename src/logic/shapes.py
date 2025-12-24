from abc import abstractmethod
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItemGroup
from PySide6.QtGui import QPen, QColor, QPainterPath
from PySide6.QtCore import QPointF


class Shape(QGraphicsPathItem):
    def __init__(self, color: str = "white", stroke_width: int = 2):
        # Проверка, что мы не создаем экземпляр абстрактного класса
        if type(self) is Shape:
            raise TypeError("Shape is an abstract class and cannot be instantiated")

        super().__init__()
        self._setup_pen(color, stroke_width)
        self._setup_flags()

    def _setup_pen(self, color: str, stroke_width: int):
        pen = QPen(QColor(color))
        pen.setWidth(stroke_width)
        self.setPen(pen)

    def _setup_flags(self):
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def set_active_color(self, color: str):
        """Изменение цвета фигуры"""
        pen = self.pen()
        pen.setColor(QColor(color))
        self.setPen(pen)

    def set_stroke_width(self, width: int):
        """Изменение толщины обводки"""
        pen = self.pen()
        pen.setWidth(width)
        self.setPen(pen)

    @property
    @abstractmethod
    def type_name(self) -> str:
        """Возвращает строковый идентификатор типа фигуры"""
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """Сериализация данных фигуры для сохранения в JSON"""
        pass


class Rectangle(Shape):
    def __init__(self, x, y, w, h, color="white", stroke_width=2):
        super().__init__(color, stroke_width)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self._update_path()

    def _update_path(self):
        path = QPainterPath()
        path.addRect(self.x, self.y, self.w, self.h)
        self.setPath(path)

    def set_geometry(self, start_point: QPointF, end_point: QPointF):
        """Обновление геометрии фигуры"""
        self.x = min(start_point.x(), end_point.x())
        self.y = min(start_point.y(), end_point.y())
        self.w = abs(end_point.x() - start_point.x())
        self.h = abs(end_point.y() - start_point.y())
        self._update_path()

    @property
    def type_name(self) -> str:
        return "rect"

    def to_dict(self) -> dict:
        return {
            "type": self.type_name,
            "pos": [self.x(), self.y()],
            "props": {
                "x": self.x,
                "y": self.y,
                "w": self.w,
                "h": self.h,
                "color": self.pen().color().name(),
                "stroke_width": self.pen().width()
            }
        }


class Line(Shape):
    def __init__(self, x1, y1, x2, y2, color="white", stroke_width=2):
        super().__init__(color, stroke_width)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self._update_path()

    def _update_path(self):
        path = QPainterPath()
        path.moveTo(self.x1, self.y1)
        path.lineTo(self.x2, self.y2)
        self.setPath(path)

    def set_geometry(self, start_point: QPointF, end_point: QPointF):
        self.x1 = start_point.x()
        self.y1 = start_point.y()
        self.x2 = end_point.x()
        self.y2 = end_point.y()
        self._update_path()

    @property
    def type_name(self) -> str:
        return "line"

    def to_dict(self) -> dict:
        return {
            "type": self.type_name,
            "pos": [self.x(), self.y()],
            "props": {
                "x1": self.x1,
                "y1": self.y1,
                "x2": self.x2,
                "y2": self.y2,
                "color": self.pen().color().name(),
                "stroke_width": self.pen().width()
            }
        }


class Ellipse(Shape):
    def __init__(self, x, y, w, h, color="white", stroke_width=2):
        super().__init__(color, stroke_width)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self._update_path()

    def _update_path(self):
        path = QPainterPath()
        path.addEllipse(self.x, self.y, self.w, self.h)
        self.setPath(path)

    def set_geometry(self, start_point: QPointF, end_point: QPointF):
        self.x = min(start_point.x(), end_point.x())
        self.y = min(start_point.y(), end_point.y())
        self.w = abs(end_point.x() - start_point.x())
        self.h = abs(end_point.y() - start_point.y())
        self._update_path()

    @property
    def type_name(self) -> str:
        return "ellipse"

    def to_dict(self) -> dict:
        return {
            "type": self.type_name,
            "pos": [self.x(), self.y()],
            "props": {
                "x": self.x,
                "y": self.y,
                "w": self.w,
                "h": self.h,
                "color": self.pen().color().name(),
                "stroke_width": self.pen().width()
            }
        }


class Group(QGraphicsItemGroup):
    def __init__(self):
        # Проверка, что мы не создаем экземпляр абстрактного класса
        if type(self) is Group:
            raise TypeError("Group is an abstract class and cannot be instantiated")

        super().__init__()
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable)
        self.setHandlesChildEvents(True)

    @property
    def type_name(self) -> str:
        return "group"

    def set_active_color(self, color: str):
        """Рекурсивное изменение цвета для всех дочерних элементов"""
        for child in self.childItems():
            if hasattr(child, "set_active_color"):
                child.set_active_color(color)

    def set_stroke_width(self, width: int):
        """Рекурсивное изменение толщины для всех дочерних элементов"""
        for child in self.childItems():
            if hasattr(child, "set_stroke_width"):
                child.set_stroke_width(width)

    def to_dict(self) -> dict:
        """Рекурсивная сериализация"""
        children_data = []
        for child in self.childItems():
            if hasattr(child, "to_dict"):
                children_data.append(child.to_dict())

        return {
            "type": self.type_name,
            "pos": [self.x(), self.y()],
            "children": children_data
        }

    def set_geometry(self, start_point: QPointF, end_point: QPointF):
        """Группу нельзя создать растягиванием мыши"""
        pass