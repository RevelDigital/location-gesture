import serial
import time

# def OpenPort(self):
#     try:
#         self.sSerial.open()
#     except SerialException, e:
#         raise e
# OpenPort()

ser = serial.Serial(port='ttyUSB0', baudrate=9600,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    )

sum = 0
while 1:
    bytesToRead = ser.inWaiting()
    if bytesToRead > 0:
        serial_line = ser.read(bytesToRead)
        sum += bytesToRead
        print(sum)
    time.sleep(0.01)