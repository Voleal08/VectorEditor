from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor
from src.logic.tools import SelectionTool, CreationTool
from src.logic.commands import DeleteCommand
from PySide6.QtGui import QUndoStack


class EditorCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        # Настройка сцены
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(0, 0, 800, 600)

        # Включаем сглаживание
        # self.setRenderHint(self.renderHints() | Qt.RenderHint.Antialiasing)
        self.setAlignment(Qt.AlignCenter)

        # Создаем стек истории
        self.undo_stack = QUndoStack(self)

        # Инициализация инструментов
        self._init_tools()

        # Устанавливаем начальный инструмент
        self.set_tool("select")

        # Включаем отслеживание мыши
        self.setMouseTracking(True)

    def _init_tools(self):
        """Инициализация инструментов"""
        self.tools = {
            "select": SelectionTool(self, self.undo_stack),
            "rect": CreationTool(self, "rect", self.undo_stack),
            "line": CreationTool(self, "line", self.undo_stack),
            "ellipse": CreationTool(self, "ellipse", self.undo_stack)
        }

    def set_tool(self, tool_name):
        """Установка текущего инструмента"""
        if tool_name in self.tools:
            self.current_tool = self.tools[tool_name]

            # Изменяем курсор
            if tool_name == "select":
                self.setCursor(Qt.ArrowCursor)
            else:
                self.setCursor(Qt.CrossCursor)

    def group_selection(self):
        """Создает группу из выделенных элементов"""
        selected_items = self.scene.selectedItems()

        # Защита от дурака: не группируем пустоту
        if len(selected_items) < 2:
            return

        # Создаем группу
        from src.logic.shapes import Group
        group = Group()

        # Сначала добавляем пустую группу на сцену
        self.scene.addItem(group)

        # Переносим элементы
        for item in selected_items:
            # Снимаем выделение с ребенка
            item.setSelected(False)
            # Добавляем в группу (Qt сам пересчитает координаты)
            group.addToGroup(item)

        # Выделяем новую группу
        group.setSelected(True)
        print("Группа создана")

    def ungroup_selection(self):
        """Разбивает выделенные группы на отдельные элементы"""
        selected_items = self.scene.selectedItems()

        for item in selected_items:
            from src.logic.shapes import Group
            if isinstance(item, Group):
                # Уничтожаем группу, дети возвращаются на сцену
                self.scene.destroyGroup(item)
                print("Группа расформирована")

    def delete_selected(self):
        """Удаляет выделенные элементы"""
        selected = self.scene.selectedItems()
        if not selected:
            return

        # Используем макрос для объединения удалений
        self.undo_stack.beginMacro("Delete Selection")

        for item in selected:
            from src.logic.commands import DeleteCommand
            cmd = DeleteCommand(self.scene, item)
            self.undo_stack.push(cmd)

        self.undo_stack.endMacro()

    # --- Обработка событий ---
    def mousePressEvent(self, event):
        # Сначала обрабатываем событие инструментом
        self.current_tool.mouse_press(event)
        # Потом передаем событие стандартной обработке
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Сначала обрабатываем событие инструментом
        self.current_tool.mouse_move(event)
        # Потом передаем событие стандартной обработке
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Сначала обрабатываем событие инструментом
        self.current_tool.mouse_release(event)
        # Потом передаем событие стандартной обработке
        super().mouseReleaseEvent(event)