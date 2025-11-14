# usb_frame.py
import sys
import traceback

try:
    import serial
    from serial.tools import list_ports
except Exception as e:
    serial = None
    list_ports = None
    print("pyserial import failed:", e, file=sys.stderr)

def list_serial_ports():
    """Return a list of available serial port device names (strings)."""
    ports = []
    if list_ports:
        try:
            ports = [p.device for p in list_ports.comports()]
        except Exception:
            print("Failed to enumerate serial ports:", file=sys.stderr)
            traceback.print_exc()
    else:
        print("serial.tools.list_ports not available (pyserial missing).", file=sys.stderr)
    return ports

def try_open(preferred="COM10", baudrate=115200, timeout=1):
    """
    Try to open the preferred port (COM6 by default). If not found, try
    reasonable fallbacks. Returns an open serial.Serial instance or None.
    Detailed errors are printed to stderr.
    """
    if serial is None:
        print("pyserial is not installed; cannot open serial ports.", file=sys.stderr)
        return None

    ports = list_serial_ports()
    print("Available serial ports:", ports)

    # First try exact match of preferred
    candidates = []
    if preferred:
        if preferred in ports:
            candidates.append(preferred)
        else:
            # On some systems list_ports returns lower/upper differences; try case-insensitive match
            for p in ports:
                if p.lower() == preferred.lower():
                    candidates.append(p)
                    break

    # If preferred not present, add USB-like or first available
    if not candidates:
        for p in ports:
            if ("usb" in p.lower()) or ("ttyUSB" in p) or ("ttyACM" in p) or p.lower().startswith("com"):
                candidates.append(p)
        if not candidates and ports:
            candidates.append(ports[0])

    if not candidates:
        print("No serial ports found to try.", file=sys.stderr)
        return None

    for port_name in candidates:
        try:
            print(f"Attempting to open serial port {port_name} @ {baudrate}bps...")
            ser = serial.Serial(port_name, baudrate, timeout=timeout)
            # Verify it's open
            if ser.is_open:
                print(f"Opened serial port {port_name}")
                return ser
            else:
                print(f"Port {port_name} opened but is_open is False", file=sys.stderr)
                try:
                    ser.close()
                except Exception:
                    pass
        except Exception as e:
            print(f"Failed to open {port_name}: {e}", file=sys.stderr)
            traceback.print_exc()
            # try next candidate

    print("All attempts to open serial port failed.", file=sys.stderr)
    return None

def send_frame(serial_port, frame_rgb, width, height):
    """
    Write an RGB frame to the device as a single payload.
    Expects frame_rgb as iterable of rows, each row an iterable of (r,g,b) tuples.
    The payload format is ":" + concatenated RRGGBB hex for all pixels + "\n".
    """
    if serial_port is None:
        print("send_frame called with serial_port=None", file=sys.stderr)
        return

    try:
        # Build full payload in memory, then send once.
        parts = [":"]
        for row in frame_rgb:
            # append each pixel as two-hex-digit components
            parts.append("".join(f"{int(r):02X}{int(g):02X}{int(b):02X}" for (r, g, b) in row))
        payload = "".join(parts) + "\n"
        serial_port.write(payload.encode("ascii"))
        try:
            serial_port.flush()
        except Exception:
            pass
    except Exception as e:
        print("Error while sending frame:", e, file=sys.stderr)
        traceback.print_exc()
