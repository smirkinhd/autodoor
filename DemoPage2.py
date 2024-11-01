import sys
import os
import random
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QBrush, QColor
from ultralytics import YOLO
import openpyxl


class VideoWindow(QWidget):
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.video_path = video_path  # Используем переданный путь к видео
        self.setWindowTitle("Демовариант автодор")
        self.setFixedSize(1400, 768)

        self.model = YOLO('Model/best_gpt3.pt')
        self.cap = cv2.VideoCapture(self.video_path)

        if not self.cap.isOpened():
            print("Не удалось открыть видеофайл.")
            sys.exit()

        self.line_position = 1100
        self.passenger_cars = 0
        self.motorcycles_bicycles = 0
        self.trucks = 0
        self.heavy_trucks = 0
        self.buses = 0
        self.car_categories = {}
        self.crossed_line = {}
        self.line_top = 540
        self.line_bottom = 750
        self.last_vehicle_info = "Нет данных о транспортном средстве"

        # Создание рамки для видео
        self.video_frame = QFrame(self)
        self.video_frame.setFrameShape(QFrame.Box)  # Установить рамку
        self.video_frame.setLineWidth(2)  # Ширина рамки
        self.video_frame.setStyleSheet("QFrame { border: 2px solid #333; }")  # Установка стиля рамки

        # Метка для отображения видео
        self.video_label = QLabel(self.video_frame)
        self.video_label.setFixedSize(900, 500)

        # Центрируем метку в рамке
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
        self.video_frame.setLayout(video_layout)

        # Info label and buttons
        self.info_label = QLabel("Загрузка данных...", self)
        self.info_label.setStyleSheet("font-size: 18px;")
        self.info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.details_button = QPushButton("Подробная статистика", self)
        self.details_button.clicked.connect(self.exportExcel)
        self.details_button.setFixedSize(200, 40)

        # Layouts
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.info_label)
        right_layout.addStretch(1)
        right_layout.addWidget(self.details_button)
        right_layout.setAlignment(Qt.AlignTop)
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.video_frame)  # Добавляем рамку с видео
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

        # Инициализация для рисования
        self.all_primitives = []  # Список для хранения завершенных примитивов (точек и цвет)
        self.used_colors = set()  # Множество для отслеживания использованных цветов
        self.current_points = []  # Текущие точки для нового примитива

        # Timer for frame updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Флаг для состояния воспроизведения
        self.is_playing = True

    def exportExcel(self):

        excel_file_path = "Report/ReportAboutTruck.xlsx"

        if os.path.exists(excel_file_path):
            workbook = openpyxl.load_workbook(excel_file_path)
            sheet = workbook.active
        else:
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Статистика Транспортных Средств"

        sheet["B4"] = self.passenger_cars
        sheet["B5"] = self.buses
        sheet["B6"] = self.trucks
        sheet["B7"] = self.heavy_trucks
        sheet["B8"] = self.motorcycles_bicycles

        new_excel_file_path = "Report/new_ReportAboutTruck.xlsx"
        workbook.save(new_excel_file_path)

        QMessageBox.information(self, "Файл сохранён", f"Данные успешно записаны в {new_excel_file_path}.")


    def update_frame(self):
        if not self.is_playing:
            return

        ret, frame = self.cap.read()

        if not ret:
            print("Конец видео.")
            self.timer.stop()
            return

        # Apply YOLO model to the frame
        results = self.model.track(frame, persist=True)
        cv2.line(frame, (self.line_position, self.line_top), (self.line_position, self.line_bottom), (0, 255, 0), 2)

        # Process detected objects
        for obj in results[0].boxes:
            x1, y1, x2, y2 = obj.xyxy[0].int().numpy()
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            object_id = obj.id.item()
            object_class = obj.cls.item()

            if object_id not in self.car_categories:
                if object_class == 0:
                    category = "bus"
                elif object_class == 1:
                    category = "car"
                elif object_class == 2:
                    category = "motorbike"
                elif object_class == 3:
                    category = "road_train"
                elif object_class == 4:
                    category = "truck"
                else:
                    category = "Unknown"
                self.car_categories[object_id] = category

            # Check if the object has crossed the line
            if object_id in self.crossed_line and self.crossed_line[object_id]:
                continue

            if self.line_top <= center_y <= self.line_bottom:
                if center_x > self.line_position:
                    category = self.car_categories.get(object_id, "Unknown")
                    if category == "car":
                        self.passenger_cars += 1
                    elif category == "motorbike":
                        self.motorcycles_bicycles += 1
                    elif category == "truck":
                        self.trucks += 1
                    elif category == "road_train":
                        self.heavy_trucks += 1
                    elif category == "bus":
                        self.buses += 1
                    self.last_vehicle_info = f"ID {object_id}, {category}"
                    self.crossed_line[object_id] = True

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

        info_text = (f"Легковые: {self.passenger_cars}\n"
                     f"Мотоциклы/Велосипеды: {self.motorcycles_bicycles}\n"
                     f"Грузовые: {self.trucks}\n"
                     f"Фуры: {self.heavy_trucks}\n"
                     f"Автобусы: {self.buses}\n")
        self.info_label.setText(info_text)


        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(pixmap)

        self.update_primitives()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_playing:  # Проверяем состояние воспроизведения
            # Проверяем, находится ли клик внутри области видео
            video_rect = self.video_label.rect()
            if video_rect.contains(event.pos() - self.video_label.pos()):
                self.current_points.append(event.pos() - self.video_label.pos())  # Уменьшаем позицию на позицию метки
                self.update()  # Обновляем, чтобы отобразить точку

    def paintEvent(self, event):
        # Отрисовка примитивов
        painter = QPainter(self.video_label)
        painter.setRenderHint(QPainter.Antialiasing)

        # Отрисовка текущего примитива без заливки
        self.draw_primitive(painter, self.current_points, QColor("black"), fill=False)

    def update_primitives(self):
        # Перерисовка всех примитивов
        painter = QPainter(self.video_label)
        painter.setRenderHint(QPainter.Antialiasing)

        for primitive, color in self.all_primitives:
            self.draw_primitive(painter, primitive, color, fill=True)

    def draw_primitive(self, painter, points, color, fill=False):
        pen = QPen(color, 2, Qt.SolidLine)
        painter.setPen(pen)
        if fill and len(points) > 2:
            brush = QBrush(color)
            painter.setBrush(brush)
            painter.drawPolygon(*points)

        painter.setBrush(Qt.NoBrush)
        for point in points:
            painter.drawEllipse(point, 5, 5)
        if len(points) >= 2:
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
            if fill and len(points) > 2:
                painter.drawLine(points[-1], points[0])  # Соединить последнюю точку с первой

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            self.all_primitives.clear()
            self.current_points.clear()
            self.used_colors.clear()
            self.update()
        elif event.key() == Qt.Key_Return:
            if len(self.current_points) > 2:
                random_color = self.generate_unique_color()
                self.all_primitives.append((self.current_points.copy(), random_color))
                self.current_points.clear()
                self.update()

    def generate_unique_color(self):
        while True:
            color = QColor(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
                255  # Установите альфа-канал на 255 для полной непрозрачности
            )
            color_tuple = (color.red(), color.green(), color.blue())
            if color_tuple not in self.used_colors:
                self.used_colors.add(color_tuple)
                return color

