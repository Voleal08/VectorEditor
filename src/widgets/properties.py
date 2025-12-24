from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                               QDoubleSpinBox, QPushButton, QColorDialog,
                               QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from src.constants import DEFAULT_STROKE_WIDTH, DEFAULT_COLOR


class PropertiesPanel(QWidget):
    def __init__(self, scene, undo_stack):
        super().__init__()
        self.scene = scene
        self.undo_stack = undo_stack
        self._init_ui()

        # Подписываемся на изменения выделения
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def _init_ui(self):
        self.setFixedWidth(250)

        # Устанавливаем явные цвета текста и фона для всей панели
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: #333333;
                font-family: Arial, sans-serif;
                font-size: 11px;
                border-left: 1px solid #ccc;
            }
            QLabel {
                font-size: 11px;
                padding: 2px 0;
            }
            QDoubleSpinBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 2px;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 2px 5px;
                min-height: 25px;
            }
            QDoubleSpinBox:focus, QPushButton:focus {
                border: 1px solid #0a74da;
                outline: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignTop)

        # Заголовок
        title = QLabel("Свойства")
        title.setStyleSheet("font-weight: bold; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(title)

        # Тип объекта
        self.lbl_type = QLabel("Не выбрано")
        self.lbl_type.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(self.lbl_type)

        # Позиция
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("X:"))
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-10000, 10000)
        self.spin_x.setSingleStep(1.0)
        self.spin_x.valueChanged.connect(self.on_geo_changed)
        pos_layout.addWidget(self.spin_x)

        pos_layout.addWidget(QLabel("Y:"))
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-10000, 10000)
        self.spin_y.setSingleStep(1.0)
        self.spin_y.valueChanged.connect(self.on_geo_changed)
        pos_layout.addWidget(self.spin_y)
        layout.addLayout(pos_layout)

        layout.addSpacing(10)

        # Толщина обводки
        layout.addWidget(QLabel("Толщина обводки:"))
        self.spin_width = QDoubleSpinBox()
        self.spin_width.setRange(0.1, 20)
        self.spin_width.setSingleStep(0.5)
        self.spin_width.valueChanged.connect(self.on_width_changed)
        layout.addWidget(self.spin_width)

        layout.addSpacing(10)

        # Цвет линии
        layout.addWidget(QLabel("Цвет линии:"))
        self.btn_color = QPushButton()
        self.btn_color.setFixedHeight(25)
        self.btn_color.clicked.connect(self.on_color_clicked)
        layout.addWidget(self.btn_color)

        layout.addStretch()

        # Изначально панель выключена
        self.setEnabled(False)

    def _get_text_color(self, bg_color):
        """Определяет подходящий цвет текста на заданном фоне"""
        if not bg_color or bg_color == "transparent":
            return "#FFFFFF"

        # Удаляем # если есть
        if bg_color.startswith("#"):
            bg_color = bg_color[1:]

        # Конвертируем HEX в RGB
        r = int(bg_color[0:2], 16)
        g = int(bg_color[2:4], 16)
        b = int(bg_color[4:6], 16)
        # Вычисляем яркость (0-255)
        brightness = (r * 0.299 + g * 0.587 + b * 0.114)

        # Если фон темный - белый текст, иначе черный
        return "#FFFFFF" if brightness < 128 else "#000000"

    def on_selection_changed(self):
        """Обработка изменения выделения"""
        selected_items = self.scene.selectedItems()

        if not selected_items:
            self.setEnabled(False)
            return

        self.setEnabled(True)
        item = selected_items[0]

        # Обновляем метку типа
        if hasattr(item, "type_name"):
            type_text = item.type_name.capitalize()
        else:
            type_text = type(item).name

        if len(selected_items) > 1:
            type_text += f" (+{len(selected_items) - 1})"

        self.lbl_type.setText(type_text)

        # Обновляем координаты
        self.spin_x.blockSignals(True)
        self.spin_y.blockSignals(True)

        try:
            self.spin_x.setValue(item.x())
            self.spin_y.setValue(item.y())
        except Exception:
            pass

        self.spin_x.blockSignals(False)
        self.spin_y.blockSignals(False)

        # Обновляем толщину
        width = DEFAULT_STROKE_WIDTH
        if hasattr(item, "pen"):
            width = item.pen().width()

        self.spin_width.blockSignals(True)
        self.spin_width.setValue(width)
        self.spin_width.blockSignals(False)

        # Обновляем цвет
        color = DEFAULT_COLOR
        if hasattr(item, "pen"):
            color = item.pen().color().name()

        # Устанавливаем цвет кнопки с правильным цветом текста
        text_color = self._get_text_color(color)
        self.btn_color.setStyleSheet(
            f"background-color: {color}; color: {text_color}; border: 1px solid #b0b0b0;"
        )

    def on_width_changed(self, value):
        """Изменение толщины линии"""
        if not self.undo_stack:
            return

        selected_items = self.scene.selectedItems()
        if not selected_items:
            return

        # Начинаем транзакцию
        self.undo_stack.beginMacro("Change Width All")

        from src.logic.commands import ChangeWidthCommand
        for item in selected_items:
            cmd = ChangeWidthCommand(item, value)
            self.undo_stack.push(cmd)

        self.undo_stack.endMacro()
        self.scene.update()

    def on_color_clicked(self):
        """Изменение цвета линии"""
        if not self.undo_stack:
            return

        color = QColorDialog.getColor(title="Выберите цвет линии")

        if color.isValid():
            hex_color = color.name()

            # Обновляем кнопку с правильным цветом текста
            text_color = self._get_text_color(hex_color)
            self.btn_color.setStyleSheet(
                f"background-color: {hex_color}; color: {text_color}; border: 1px solid #b0b0b0;"
            )

            # Применяем ко всем выделенным
            selected_items = self.scene.selectedItems()
            if not selected_items:
                return

            # Начинаем транзакцию
            self.undo_stack.beginMacro("Change Color All")

            from src.logic.commands import ChangeColorCommand
            for item in selected_items:
                cmd = ChangeColorCommand(item, hex_color)
                self.undo_stack.push(cmd)

            self.undo_stack.endMacro()
            self.scene.update()

    def on_geo_changed(self, value):
        """Изменение позиции"""
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            item.setPos(self.spin_x.value(), self.spin_y.value())
        self.scene.update()