import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QPushButton, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal, QCoreApplication
import serial
import csv
import time

MAX_LINE_LENGTH = 100
BUFFER_SIZE = 1000
MAX_SENTENCE_LENGTH = 79
LATITUDE_LENGTH = 12
LONGITUDE_LENGTH = 12


class SerialDataPlayer(QWidget):

    stop_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Serial Data Player")
        self.setGeometry(100, 100, 600, 400)

        self.playing = False  # Flag to track whether data is being played
        self.init_ui()

        self.gps_thread = None

    def init_ui(self):
        layout = QVBoxLayout()

        # Dropdown box to select serial port
        self.port_dropdown = QComboBox()
        self.port_dropdown.addItems(['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3'])
        layout.addWidget(self.port_dropdown)

        # Play/Stop data button
        self.play_button = QPushButton("Play Data")
        self.play_button.clicked.connect(self.toggle_play)
        layout.addWidget(self.play_button)

        # Text area to display lines
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        # Toggle GPS button
        self.toggle_button = QPushButton('Start GPS')
        self.toggle_button.clicked.connect(self.toggle_gps)
        layout.addWidget(self.toggle_button)

        self.setLayout(layout)

        # Worker thread
        self.worker_thread = WorkerThread(self)
        self.worker_thread.finished.connect(self.play_finished)
        self.worker_thread.new_line.connect(self.update_text)

        self.stop_signal.connect(QCoreApplication.quit)

    def open_port(self):
        try:
            selected_port = self.port_dropdown.currentText()
            ser = serial.Serial(selected_port, baudrate=9600, timeout=None)
            print(f"Serial port opened successfully with port: {ser.port}")
            return ser
        except Exception as e:
            print(f"Error opening serial port: {e}")
            return None

    def toggle_play(self):
        if not self.playing:
            self.worker_thread.start()
            self.play_button.setText("Stop Data")
        else:
            self.worker_thread.stop()
            self.play_button.setText("Play Data")
            self.stop_signal.emit()

    def toggle_gps(self):
        if not self.gps_thread or not self.gps_thread.isRunning():
            selected_port = self.port_dropdown.currentText()
            self.gps_thread = GPSReaderThread(selected_port)
            self.gps_thread.data_received.connect(self.update_text)
            self.gps_thread.start()
            self.toggle_button.setText('Stop GPS')
        else:
            self.gps_thread.stop()
            self.gps_thread.wait()  # Wait for the thread to finish
            self.toggle_button.setText('Start GPS')

    def play_finished(self):
        self.playing = False
        self.play_button.setText("Play Data")

    def update_text(self, line):
        self.text_edit.append(line)


class WorkerThread(QThread):
    finished = pyqtSignal()
    new_line = pyqtSignal(str)

    def __init__(self, parent=None):
        super(WorkerThread, self).__init__(parent)
        self.stopped = False

    def stop(self):
        self.stopped = True

    def run(self):
        ser = self.parent().open_port()
        self.parent().playing = True

        if ser is not None:
            try:
                with open("GPS_raw.csv", "r") as csvfile:
                    csvreader = csv.reader(csvfile)
                    for row in csvreader:
                        if self.stopped:
                            break  # Stop playing if the button is toggled to "Stop Data"

                        line = ",".join(row).strip()
                        if line:
                            try:
                                ser.write(line.encode())
                                self.new_line.emit(line)
                                time.sleep(3)
                            except Exception as e:
                                print(f"Error writing to serial port: {e}")
                                break
            except Exception as e:
                print(f"Error reading the CSV file: {e}")
            finally:
                ser.close()

        self.finished.emit()


class GPSReaderThread(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, selected_port):
        super().__init__()
        self.selected_port = selected_port
        self.stopped = False

    def stop(self):
        self.stopped = True

    def run(self):
        try:
            ser = serial.Serial(self.selected_port, 9600, timeout=1)
            print(f"Serial port opened successfully with port: {ser.port}")

            with open("GPS_refined.csv", "w", newline='') as refined_file, open("GPS_raw.csv", "w") as raw_file:
                refined_csv_writer = csv.writer(refined_file)

                while not self.stopped:
                    data = ser.readline().decode('utf-8')
                    self.data_received.emit(data)

                    if data.startswith("$GNGGA,"):
                        raw_file.write(data.strip() + '\n')
                        raw_file.flush()

                        saved_sentence = data[:MAX_SENTENCE_LENGTH]

                        if len(saved_sentence) >= 44:
                            latitude = saved_sentence[18:29]
                            longitude = saved_sentence[32:44]

                            nmea_latitude = latitude
                            nmea_longitude = longitude

                            normal_latitude = nmea_to_normal_gps_lat(nmea_latitude)
                            normal_longitude = nmea_to_normal_gps_lon(nmea_longitude)

                            refined_csv_writer.writerow([normal_latitude, normal_longitude])
                            refined_file.flush()

            ser.close()
            print("Serial port closed.")

        except serial.SerialException as e:
            print(f"Error opening or reading from serial port: {e}")


def nmea_to_normal_gps_lat(nmea_coordinate):
    degrees, minutes = int(nmea_coordinate[:2]), float(nmea_coordinate[2:])
    normal_gps = degrees + (minutes / 60.0)
    return normal_gps


def nmea_to_normal_gps_lon(nmea_coordinate):
    degrees, minutes = int(nmea_coordinate[:3]), float(nmea_coordinate[3:])
    normal_gps = degrees + (minutes / 60.0)
    return normal_gps


def main():
    app = QApplication(sys.argv)
    window = SerialDataPlayer()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
