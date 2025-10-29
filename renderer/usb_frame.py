# usb_frame.py
import serial
import sys
import glob

def try_open():
    patterns = []
    if sys.platform.startswith("linux"):
        patterns = ["/dev/ttyACM*", "/dev/ttyUSB*"]
    elif sys.platform.startswith("darwin"):
        patterns = ["/dev/cu.usbmodem*", "/dev/cu.usbserial*"]
    elif sys.platform.startswith("win"):
        patterns = ["COM%s" % i for i in range(3, 30)]

    for p in patterns:
        for port in glob.glob(p):
            try:
                return serial.Serial(port, 115200, timeout=0)
            except:
                pass
    return None

def send_frame(serial_port, frame_rgb, width, height):
    for row in frame_rgb:
        line = "".join(f"{r:02X}{g:02X}{b:02X}" for (r,g,b) in row)
        serial_port.write((line + "\n").encode("ascii"))
