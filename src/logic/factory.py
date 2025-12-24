from .shapes import Rectangle, Line, Ellipse, Group
from PySide6.QtCore import QPointF


class ShapeFactory:
    @staticmethod
    def create_shape(shape_type: str, start_point: QPointF, end_point: QPointF, color: str = "black"):
        """Создает фигуру указанного типа"""
        x1, y1 = start_point.x(), start_point.y()
        x2, y2 = end_point.x(), end_point.y()

        # Вычисляем нормализованные координаты для прямоугольных фигур
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)

        if shape_type == "rect":
            return Rectangle(x, y, w, h, color)
        elif shape_type == "ellipse":
            return Ellipse(x, y, w, h, color)
        elif shape_type == "line":
            return Line(x1, y1, x2, y2, color)
        else:
            raise ValueError(f"Неизвестный тип фигуры: {shape_type}")

    @staticmethod
    def from_dict(data: dict):
        """Создает фигуру из словаря (для загрузки проекта)"""
        shape_type = data.get("type")

        if shape_type == "group":
            return ShapeFactory._create_group(data)
        elif shape_type in ["rect", "line", "ellipse"]:
            return ShapeFactory._create_primitive(data)
        else:
            raise ValueError(f"Неизвестный тип: {shape_type}")

    @staticmethod
    def _create_primitive(data: dict):
        """Создает примитивную фигуру из словаря"""
        props = data.get("props", {})
        shape_type = data.get("type")

        # Общие свойства
        color = props.get("color", "white")
        stroke_width = props.get("stroke_width", 2)

        if shape_type == "rect":
            return Rectangle(
                props["x"], props["y"], props["w"], props["h"],
                color, stroke_width
            )
        elif shape_type == "line":
            return Line(
                props["x1"], props["y1"], props["x2"], props["y2"],
                color, stroke_width
            )
        elif shape_type == "ellipse":
            return Ellipse(
                props["x"], props["y"], props["w"], props["h"],
                color, stroke_width
            )

    @staticmethod
    def _create_group(data: dict):
        """Создает группу из словаря"""
        group = Group()

        # Восстанавливаем позицию группы
        pos = data.get("pos", [0, 0])
        group.setPos(pos[0], pos[1])

        # Рекурсивно восстанавливаем детей
        children_data = data.get("children", [])
        for child_dict in children_data:
            child_item = ShapeFactory.from_dict(child_dict)
            group.addToGroup(child_item)

        return group