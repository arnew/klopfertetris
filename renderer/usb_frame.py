# renderer/usb_frame.py
import os, time

class USBFrameRenderer:
    """
    Writes frames as ASCII hex RRGGBB... + newline to a configured device file.
    Device path provided in config (e.g. /dev/ttyACM0).
    """

    def __init__(self, device_path, width=10, height=20, timeout=0.1):
        self.device_path = device_path
        self.width = width
        self.height = height
        self.timeout = timeout
        self.device = None
        self.open_device()

    def open_device(self):
        try:
            # open in binary unbuffered mode
            self.device = open(self.device_path, "wb", buffering=0)
            print("USB frame device opened:", self.device_path)
        except Exception as e:
            print("Failed to open USB frame device:", e)
            self.device = None

    def available(self):
        return self.device is not None

    def render(self, buffer2d):
        """
        buffer2d: list of rows [height][width] with 0/1 or color tuples
        Build RRGGBB per pixel row-major and write as one line + newline.
        """
        if not self.device:
            return False
        # Build
        out = bytearray()
        for y in range(self.height):
            for x in range(self.width):
                v = buffer2d[y][x]
                if isinstance(v, tuple):
                    r,g,b = v
                else:
                    if v:
                        r,g,b = (255,128,0)
                    else:
                        r,g,b = (0,0,0)
                out.extend(f"{r:02X}{g:02X}{b:02X}".encode("ascii"))
        try:
            self.device.write(out + b"\n")
            # flush? not necessary with buffering=0 but ensure
            self.device.flush()
            return True
        except Exception as e:
            print("USB frame write failed:", e)
            self.device = None
            return False
