from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
from DemoPage2 import VideoWindow


class CustomButton(QPushButton):
    def __init__(self, parent=None):
        super(CustomButton, self).__init__(parent)
        self.setObjectName("CustomButton")
        self.setText("Приступить!")
        self.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.setStyleSheet("""
            #CustomButton {
                width: 250px;
                height: 50px;
                line-height: 50px;
                font-weight: bold;
                text-decoration: none;
                background: #333;
                text-align: center;
                font-family: Unbounded;
                color: #fff;
                text-transform: uppercase;
                letter-spacing: 1px;
                border: 3px solid #333;
                border-radius: 20px;
            }
            #CustomButton:hover {
                width: 200px;
                border: 3px solid #2ecc71;
                background: transparent;
                color: #2ecc71;
            }
        """)


class DemoPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filePath = None

        height = 768
        self.setFixedHeight(height)
        width = 1400
        self.setFixedWidth(width)

        self.button = CustomButton(self)
        self.button.clicked.connect(self.showFileDialog)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self.button, alignment=Qt.AlignCenter)
        layout.addStretch()

        self.setLayout(layout)

    def showFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileName, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "",
                                                  "MP4-видео (*.mp4);; AVI-видео (*.avi)", options=options)
        if fileName:
            self.filePath = fileName
            print(f"Выбранный файл: {self.filePath}")
            self.openVideoWindow()

    def openVideoWindow(self):

        self.video_window = VideoWindow(self.filePath)
        self.video_window.show()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = DemoPage()
    demo.show()
    sys.exit(app.exec_())
