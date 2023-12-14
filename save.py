import serial
import time
import csv

BUFFER_SIZE = 1000
MAX_SENTENCE_LENGTH = 79
LATITUDE_LENGTH = 12
LONGITUDE_LENGTH = 12

def nmea_to_normal_gps_lat(nmea_coordinate):
    degrees, minutes = int(nmea_coordinate[:2]), float(nmea_coordinate[2:])
    normal_gps = degrees + (minutes / 60.0)
    return normal_gps

def nmea_to_normal_gps_lon(nmea_coordinate):
    degrees, minutes = int(nmea_coordinate[:3]), float(nmea_coordinate[3:])
    normal_gps = degrees + (minutes / 60.0)
    return normal_gps

def open_port():
    try:
        ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
        print(f"Serial port opened successfully with port: {ser.port}")
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return None

def main():
    ser = open_port()

    with open("GPS_refined.csv", "w", newline='') as file:
        csv_writer = csv.writer(file)

        if ser is not None:
            try:
                while True:
                    data = ser.readline().decode('utf-8')
                    if data.startswith("$GNGGA,"):
                        print(f"Raw Data: {data}")
                        saved_sentence = data[:MAX_SENTENCE_LENGTH]
                        print(f"Length of saved_sentence: {len(saved_sentence)}")

                        if len(saved_sentence) >= 44:
                            latitude = saved_sentence[18:29]
                            longitude = saved_sentence[32:44]

                            nmea_latitude = latitude
                            nmea_longitude = longitude

                            normal_latitude = nmea_to_normal_gps_lat(nmea_latitude)
                            normal_longitude = nmea_to_normal_gps_lon(nmea_longitude)

                            print(f"Latitude: {normal_latitude:.6f}")
                            print(f"Longitude: {normal_longitude:.6f}")

                            csv_writer.writerow([normal_latitude, normal_longitude])
                            file.flush()  # Flush the buffer to ensure data is written immediately

                        else:
                            print("Insufficient characters in saved_sentence.")
                    else:
                        print("Buffer does not contain $GNGGA.")

                    #time.sleep(1)  # Add a delay if needed to control the rate of reading

            except KeyboardInterrupt:
                pass  # Handle keyboard interrupt (Ctrl+C)

if __name__ == "__main__":
    main()

