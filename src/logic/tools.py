from abc import ABC, abstractmethod
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsView
from src.logic.factory import ShapeFactory


class Tool(ABC):
    def __init__(self, view, undo_stack=None):
        self.view = view
        self.scene = view.scene
        self.undo_stack = undo_stack

    @abstractmethod
    def mouse_press(self, event): pass

    @abstractmethod
    def mouse_move(self, event): pass

    @abstractmethod
    def mouse_release(self, event): pass


class SelectionTool(Tool):
    def __init__(self, view, undo_stack):
        super().__init__(view, undo_stack)
        self.item_positions = {}

    def mouse_press(self, event):
        # Сначала даем Qt обработать клик
        QGraphicsView.mousePressEvent(self.view, event)

        # Запоминаем позиции выделенных объектов
        self.item_positions.clear()
        for item in self.scene.selectedItems():
            self.item_positions[item] = item.pos()

    def mouse_move(self, event):
        QGraphicsView.mouseMoveEvent(self.view, event)

    def mouse_release(self, event):
        # Даем Qt завершить перемещение
        QGraphicsView.mouseReleaseEvent(self.view, event)

        # Проверяем, сдвинулись ли объекты
        moved_items = []
        for item, old_pos in self.item_positions.items():
            new_pos = item.pos()
            if new_pos != old_pos:
                moved_items.append((item, old_pos, new_pos))

        if moved_items and self.undo_stack:
            # Начинаем транзакцию
            self.undo_stack.beginMacro("Move Items")

            from src.logic.commands import MoveCommand
            for item, old_pos, new_pos in moved_items:
                cmd = MoveCommand(item, old_pos, new_pos)
                self.undo_stack.push(cmd)

            self.undo_stack.endMacro()

        self.item_positions.clear()


class CreationTool(Tool):
    def __init__(self, view, shape_type, undo_stack):
        super().__init__(view, undo_stack)
        self.shape_type = shape_type
        self.start_pos = None
        self.temp_shape = None

    def mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = self.view.mapToScene(event.pos())

    def mouse_move(self, event):
        # УБРАНА ПРОВЕРКА НА undo_stack - временная фигура должна отображаться всегда
        if self.start_pos:
            current_pos = self.view.mapToScene(event.pos())

            # Если уже создана временная фигура, удаляем ее
            if self.temp_shape:
                self.scene.removeItem(self.temp_shape)

            # Создаем новую временную фигуру
            try:
                self.temp_shape = ShapeFactory.create_shape(
                    self.shape_type,
                    self.start_pos,
                    current_pos,
                    "white"
                )
                self.scene.addItem(self.temp_shape)
            except ValueError as e:
                print(f"Error creating temp shape: {e}")

    def mouse_release(self, event):
        if self.start_pos and event.button() == Qt.LeftButton:
            end_pos = self.view.mapToScene(event.pos())

            # Удаляем временную фигуру
            if self.temp_shape:
                self.scene.removeItem(self.temp_shape)
                self.temp_shape = None

            # Создаем финальную фигуру и добавляем в стек
            try:
                final_shape = ShapeFactory.create_shape(
                    self.shape_type,
                    self.start_pos,
                    end_pos,
                    "white"
                )

                # Добавляем в стек через команду
                from src.logic.commands import AddShapeCommand
                command = AddShapeCommand(self.scene, final_shape)
                self.undo_stack.push(command)

                self.start_pos = None

                print(f"Создана фигура: {self.shape_type}")
            except ValueError as e:
                print(f"Error creating final shape: {e}")

                self.start_pos = None