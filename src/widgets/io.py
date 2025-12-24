import json
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import QRectF
from abc import ABC, abstractmethod


class SaveStrategy(ABC):
    @abstractmethod
    def save(self, filename: str, scene, items: list):
        pass


class JsonSaveStrategy(SaveStrategy):
    def save(self, filename: str, scene, items: list):
        """Сохраняет проект в JSON-формате"""
        data = {
            "version": "1.0",
            "scene": {
                "width": scene.width(),
                "height": scene.height()
            },
            "shapes": []
        }

        # Собираем данные со всех фигур
        for item in items:
            if hasattr(item, "to_dict"):
                data["shapes"].append(item.to_dict())

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)


class ImageSaveStrategy(SaveStrategy):
    def init(self, format_name="PNG", background_color="white"):
        self.format_name = format_name
        self.bg_color = background_color

    def save(self, filename: str, scene, items: list):
        """Экспортирует сцену в изображение"""
        rect = scene.sceneRect()
        width = int(rect.width())
        height = int(rect.height())

        # Создаем буфер изображения
        image = QImage(width, height, QImage.Format_ARGB32)

        # Заливка фона
        if self.bg_color == "transparent":
            image.fill(0)
        else:
            image.fill(self.bg_color)

        # Рендеринг сцены
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        scene.render(painter, QRectF(image.rect()), rect)
        painter.end()

        # Сохранение на диск
        image.save(filename, self.format_name)