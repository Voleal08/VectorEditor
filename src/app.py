from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
                               QToolBar, QStatusBar, QMenu, QFileDialog, QMessageBox,
                               QDockWidget)
from PySide6.QtGui import QKeySequence, QAction
from PySide6.QtCore import Qt
from src.canvas import EditorCanvas
from src.widgets.properties import PropertiesPanel
from src.constants import (FORMAT_VECTOR, FORMAT_PNG, FORMAT_JPG, DEFAULT_SCENE_WIDTH,
                           DEFAULT_SCENE_HEIGHT)
from src.logic.factory import ShapeFactory


class VectorEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vector Editor")
        self.resize(1200, 800)
        self._init_ui()

    def _init_ui(self):
        # Центральный виджет и холст
        self.canvas = EditorCanvas()
        self.setCentralWidget(self.canvas)

        # Статус-бар
        self.statusBar().showMessage("Готов к работе")

        # Создаем панель свойств
        self.props_panel = PropertiesPanel(self.canvas.scene, self.canvas.undo_stack)

        # Добавляем панель свойств как отдельный виджет
        props_dock = QDockWidget("Свойства", self)
        props_dock.setWidget(self.props_panel)
        props_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                               QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, props_dock)

        # Создаем меню
        self._create_menu()

        # Создаем тулбар
        self._create_toolbar()

    def _create_menu(self):
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("&Файл")

        # Действия для меню Файл
        save_action = QAction("Сохранить", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.on_save_clicked)

        save_as_action = QAction("Сохранить как...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.on_save_as_clicked)

        open_action = QAction("Открыть", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.on_open_clicked)

        export_action = QAction("Экспортировать", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.on_export_clicked)

        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)

        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(open_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Меню Правка
        edit_menu = menubar.addMenu("&Правка")

        # Добавляем Undo/Redo действия
        undo_action = self.canvas.undo_stack.createUndoAction(self, "&Отменить")
        undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(undo_action)

        redo_action = self.canvas.undo_stack.createRedoAction(self, "&Повторить")
        redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        group_action = QAction("Группировать", self)
        group_action.setShortcut(QKeySequence("Ctrl+G"))
        group_action.triggered.connect(self.canvas.group_selection)
        edit_menu.addAction(group_action)

        ungroup_action = QAction("Разгруппировать", self)
        ungroup_action.setShortcut(QKeySequence("Ctrl+U"))
        ungroup_action.triggered.connect(self.canvas.ungroup_selection)
        edit_menu.addAction(ungroup_action)

    def _create_toolbar(self):
        toolbar = QToolBar("Основные инструменты")
        self.addToolBar(toolbar)
        # Инструмент выделения
        select_action = QAction("Выделение", self)
        select_action.setCheckable(True)
        select_action.setChecked(True)
        select_action.triggered.connect(lambda: self.canvas.set_tool("select"))
        toolbar.addAction(select_action)

        # Инструменты рисования
        line_action = QAction("Линия", self)
        line_action.setCheckable(True)
        line_action.triggered.connect(lambda: self.canvas.set_tool("line"))
        toolbar.addAction(line_action)

        rect_action = QAction("Прямоугольник", self)
        rect_action.setCheckable(True)
        rect_action.triggered.connect(lambda: self.canvas.set_tool("rect"))
        toolbar.addAction(rect_action)

        ellipse_action = QAction("Эллипс", self)
        ellipse_action.setCheckable(True)
        ellipse_action.triggered.connect(lambda: self.canvas.set_tool("ellipse"))
        toolbar.addAction(ellipse_action)

    def on_save_clicked(self):
        self._save_project()

    def on_save_as_clicked(self):
        self._save_project(save_as=True)

    def _save_project(self, save_as=False):
        from src.widgets.io import JsonSaveStrategy

        # Если файл уже существует и это не save-as, используем существующий путь
        current_path = getattr(self, 'current_file_path', '') if not save_as else ''

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить проект",
            current_path,
            f"{FORMAT_VECTOR};;{FORMAT_PNG};;{FORMAT_JPG}"
        )

        if not path:
            return

        # Определяем стратегию сохранения
        if path.endswith((".png", ".jpg")):
            from src.widgets.io import ImageSaveStrategy
            fmt = "PNG" if path.endswith(".png") else "JPG"
            strategy = ImageSaveStrategy(fmt, "white")
        else:
            strategy = JsonSaveStrategy()

        try:
            strategy.save(path, self.canvas.scene, self.canvas.scene.items())
            self.current_file_path = path
            self.statusBar().showMessage(f"Сохранено в {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось сохранить файл:\n{str(e)}")

    def on_open_clicked(self):
        from src.logic.factory import ShapeFactory

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть проект",
            "",
            f"{FORMAT_VECTOR}"
        )

        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = f.read()
                if not data.strip():
                    raise ValueError("Файл пустой")

            # Очистка старого состояния
            self.canvas.scene.clear()
            self.canvas.undo_stack.clear()

            # Восстановление данных
            from json import loads
            json_data = loads(data)

            # Восстанавливаем сцену
            scene_info = json_data.get("scene", {})
            width = scene_info.get("width", DEFAULT_SCENE_WIDTH)
            height = scene_info.get("height", DEFAULT_SCENE_HEIGHT)
            self.canvas.scene.setSceneRect(0, 0, width, height)

            # Восстанавливаем фигуры
            shapes_data = json_data.get("shapes", [])
            for shape_dict in shapes_data:
                try:
                    shape = ShapeFactory.from_dict(shape_dict)
                    self.canvas.scene.addItem(shape)
                except Exception as e:
                    print(f"Ошибка загрузки фигуры: {e}")

            self.current_file_path = path
            self.statusBar().showMessage(f"Проект загружен: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки", f"Не удалось загрузить файл:\n{str(e)}")

    def on_export_clicked(self):
        from src.widgets.io import ImageSaveStrategy

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспортировать как изображение",
            "",
            f"{FORMAT_PNG};;{FORMAT_JPG}"
        )

        if not path:
            return

        fmt = "PNG" if path.endswith(".png") else "JPG"
        strategy = ImageSaveStrategy(fmt, "white")

        try:
            strategy.save(path, self.canvas.scene, self.canvas.scene.items())
            self.statusBar().showMessage(f"Экспорт выполнен: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось экспортировать:\n{str(e)}")