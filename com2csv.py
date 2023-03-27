"""
com2csv.py - En GUI-applikation för att läsa in data från en streckkodsläsare och spara den till en CSV-fil.

Beskrivning:
Denna applikation ansluter till en streckkodsläsare via en seriell port och lyssnar på inkommande data. All inläst data sparas till en CSV-fil tillsammans med tidpunkten då datat lästes in. Om samma data läses in flera gånger skrivs endast en kopia till filen.

Applikationen har en enkel GUI med en textruta för att visa inläst data och två knappar: "Stäng" för att avsluta applikationen och "Ta bort data" för att rensa all tidigare sparad data.

Författare: Joakim Ringstad jmux.se

Datum: 2023-03-27

Licens: GNU-GPL, open source free for commersial use

"""

# Importera nödvändiga moduler
import serial
import sys
import csv
import time
from datetime import datetime
from PyQt5 import QtWidgets, QtGui, QtCore
import serial.tools.list_ports

csv_filename = str(datetime.now().strftime('%Y%m%d'))+"_com2csv.csv"

def get_serial_port():
    # Get list of all serial ports
    ports = list(serial.tools.list_ports.comports())

    # Filter list of ports to those with "barcode" or "scanner" in description
    barcode_scanner_ports = [port for port in ports if "barcode" in port.description.lower() or "scanner" in port.description.lower() or "serial device" in port.description.lower()]

    # Select first port in filtered list, or return None if no matching ports found
    return barcode_scanner_ports[0].device if barcode_scanner_ports else None

class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.buffer = ''
        self.timeout = 0.1 # timeout i sekunder

    def run(self):
        while True:
            try:
                byte = self.serial_port.read().decode()
                self.buffer += byte
                if byte == '\r':
                    self.data_received.emit(self.buffer.strip())
                    self.buffer = ''
            except serial.SerialTimeoutException:
                pass

    def stop(self):
        self.terminate()
        self.serial_port.close()


class MyApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Get serial port for barcode scanner or scanner
        port_name = get_serial_port()
        if not port_name:
            print("No serial port found.")
            sys.exit(1)

        # Create buttons
        self.delete_button = QtWidgets.QPushButton('Ta bort data')
        self.delete_button.setMaximumWidth(100)
        self.delete_button.clicked.connect(self.delete_data)
        self.delete_button.hide()

        self.close_button = QtWidgets.QPushButton('Stäng')
        self.close_button.setMaximumWidth(100)
        self.close_button.clicked.connect(self.close_app)

        # Create text panel and set font
        self.data_panel = QtWidgets.QTextEdit()
        font = QtGui.QFont()
        font.setPointSize(12)
        self.data_panel.setFont(font)

        # Add message with selected serial port to text panel
        message = f"com2csv är ett program som sparar data över com-port till csv-fil."
        self.data_panel.append(message)
        message = f"Scannern är ansluten till com-port: <font color='green'> {port_name}</font>"
        self.data_panel.append(message)
        message = f"\nInläst data kommer sparas till: " + csv_filename
        self.data_panel.append(message)

        # Create layout
        layout = QtWidgets.QVBoxLayout()

        # Add title text at the top of the window
        self.title_text = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setPointSize(24)
        self.title_text.setFont(font)
        self.title_text.setText("com2csv")
        layout.addWidget(self.title_text)

        # Add output window to left side
        layout.addWidget(self.data_panel, stretch=1)

        # Add container for buttons to right side
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.close_button)
        button_container.setLayout(button_layout)
        layout.addWidget(button_container)

        # Add bottom text at the bottom of the window
        self.bottom_text = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setItalic(True)
        self.bottom_text.setFont(font)
        self.bottom_text.setText("Licensierad under GNU GPL version 3.0\n2023 J.Ringstad\nhttps://github.com/joeraven0/com2csv")
        self.bottom_text.setMaximumWidth(300)
        self.bottom_text.setWordWrap(True)
        layout.addStretch()
        layout.addWidget(self.bottom_text)

        # Set layout and window size
        self.setLayout(layout)
        self.setGeometry(100, 100, 800, 400)

        # Connect to serial port and create CSV file
        self.ser = serial.Serial(port_name, 9600, timeout=0.1)
        self.csv_file = open(csv_filename, 'a', newline='')
        self.csv_writer = csv.writer(self.csv_file)

        # Create serial thread and start reading data
        self.show()
        self.serial_thread = SerialThread(self.ser)
        self.serial_thread.data_received.connect(self.read_data)
        self.serial_thread.start()

    def close_app(self):
        # Stop the serial thread and close the serial port
        self.serial_thread.stop()
        self.ser.close()
        # Close the main window and exit the application
        QtWidgets.QApplication.instance().quit()


    def read_data(self, data):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Open CSV-file in read mode to check if data already exists
        with open(csv_filename, 'r') as f:
            reader = csv.reader(f)
            # Check if data already exists in file
            if any(data in row for row in reader):
                # Print message to output window in red text
                message = f"<font color='red'>Data already exists in file</font>"
                self.data_panel.append(message)

            else:
                # Write data to file if it doesn't already exist
                self.csv_writer.writerow([now, data])
                self.csv_file.flush() # write buffer to file
        self.data_panel.append(f'{now}  {data}')


    def delete_data(self):
        pass


    def show_data(self):
        with open(csv_filename, 'r') as f:
            reader = csv.reader(f)
            data = list(reader)
        self.data_panel.clear()
        for row in data:
            self.data_panel.append(f'{row[0]}  {row[1]}')


    def closeEvent(self, event):
        self.serial_thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MyApp()
    sys.exit(app.exec_())
