import sys
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer
from PIL import Image, ImageDraw
import numpy as np

class GPSVis(object):
    def __init__(self, map_path, points):
        self.points = points
        self.map_path = map_path
        self.result_image = Image.open(self.map_path, 'r')
        self.x_ticks = []
        self.y_ticks = []
        self.gps_data = []

    def plot_map(self):
        self.get_ticks()
        img_points = []
        for d in self.gps_data:
            x1, y1 = self.scale_to_img(d, (self.result_image.size[0], self.result_image.size[1]))
            img_points.append((x1, y1))
        draw = ImageDraw.Draw(self.result_image)
        draw.line(img_points, fill=(0, 0, 255), width=3)

    def scale_to_img(self, lat_lon, h_w):
        old = (self.points[2], self.points[0])
        new = (0, h_w[1])
        y = ((lat_lon[0] - old[0]) * (new[1] - new[0]) / (old[1] - old[0])) + new[0]
        old = (self.points[1], self.points[3])
        new = (0, h_w[0])
        x = ((lat_lon[1] - old[0]) * (new[1] - new[0]) / (old[1] - old[0])) + new[0]
        return int(x), h_w[1] - int(y)

    def get_ticks(self):
        self.x_ticks = list(map(lambda x: round(x, 4), np.linspace(self.points[1], self.points[3], num=7)))
        y_ticks = list(map(lambda x: round(x, 4), np.linspace(self.points[2], self.points[0], num=8)))
        self.y_ticks = sorted(y_ticks, reverse=True)

class GPSVisApp(QMainWindow):
    def __init__(self, map_path, points, csv_filename):
        super(GPSVisApp, self).__init__()
        self.map_path = map_path
        self.points = points
        self.gps_data = []
        self.csv_filename = csv_filename
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.image_label = QLabel(self)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.image_label)
        self.input_layout = QHBoxLayout()
        self.central_layout.addLayout(self.input_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_map)
        self.delay_timer = QTimer(self)
        self.delay_timer.timeout.connect(self.delayed_update)
        self.delay_duration = 2000  # Set the delay duration in milliseconds
        self.csvfile = None  # Added to keep track of the open file

        self.update_map()

    def plot_map(self, x_value, y_value):
        self.gps_data.append((x_value, y_value))
        vis = GPSVis(map_path=self.map_path, points=self.points)
        vis.gps_data = self.gps_data
        vis.plot_map()
        result_image = vis.result_image
        image_data = result_image.convert("RGBA").tobytes("raw", "RGBA")
        q_image = QPixmap.fromImage(QImage(image_data, result_image.size[0], result_image.size[1], QImage.Format_RGBA8888))
        self.image_label.setPixmap(q_image)

    def update_map(self):
        try:
            self.csvfile = open(self.csv_filename, 'r', newline='')
            reader = csv.reader(self.csvfile)
            self.row_iterator = iter(reader)
            self.delayed_update()  # Start the process
        except FileNotFoundError:
            print(f"Error: {self.csv_filename} not found.")

    def delayed_update(self):
        try:
            row = next(self.row_iterator)
            x_value, y_value = map(float, row)
            self.plot_map(x_value, y_value)
            self.delay_timer.singleShot(self.delay_duration, self.delayed_update)
        except StopIteration:
            print("End of file reached.")
            self.csvfile.close()  # Close the file when finished

def main():
    app = QApplication(sys.argv)
    points = (10.05627, 76.35362, 10.05535, 76.35552)
    main_window = GPSVisApp(map_path='map.png', points=points, csv_filename='data.csv')
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

