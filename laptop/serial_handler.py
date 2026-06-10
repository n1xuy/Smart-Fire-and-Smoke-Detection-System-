import threading
import serial
import re
from config import SERIAL_PORT, SERIAL_BAUD

SENSOR_REGEX = re.compile(r"T:([\d\.\-]+)\s+H:([\d\.\-]+)\s+G:(\d+)")

class SerialHandler:
    def __init__(self):
        self.port = None
        self.lock = threading.Lock()
        self._data = {"temperature": 0.0, "humidity": 0.0, "gas": 0}
        self._running = False
        self._thread = None

    def connect(self):
        try:
            self.port = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            return True
        except serial.SerialException as e:
            print(f"[Serial] Failed to open {SERIAL_PORT}: {e}")
            return False

    def _read_loop(self):
        while self._running:
            try:
                line = self.port.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                match = SENSOR_REGEX.search(line)
                if match:
                    with self.lock:
                        t_str = match.group(1)
                        h_str = match.group(2)
                        g_str = match.group(3)
                        if t_str != "--" and h_str != "--":
                            self._data["temperature"] = float(t_str)
                            self._data["humidity"] = float(h_str)
                        self._data["gas"] = int(g_str)
            except Exception as e:
                print(f"[Serial] Read error: {e}")
                break

    def get_data(self):
        with self.lock:
            return dict(self._data)

    def send_command(self, led, buzzer):
        if self.port and self.port.is_open:
            cmd = f"L:{led} B:{buzzer}\n"
            try:
                self.port.write(cmd.encode())
            except Exception as e:
                print(f"[Serial] Write error: {e}")

    def close(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self.port and self.port.is_open:
            self.port.close()
