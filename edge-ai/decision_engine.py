import time
from config import THRESHOLDS, STATE_SAFE, STATE_WARNING, STATE_ALARM

T = THRESHOLDS

class DecisionEngine:
    def __init__(self):
        self.current_state = STATE_SAFE
        self.prev_state = STATE_SAFE
        self._warmup_start = time.time()
        self._warmup_duration = 600
        self.trigger_reasons = []

    def evaluate(self, sensor_data, vision_detections):
        self.trigger_reasons = []
        t = sensor_data.get("temperature")
        h = sensor_data.get("humidity")
        g = sensor_data.get("gas")

        alarm_count = 0
        warning_count = 0

        if t is not None:
            if t >= T["temp_alarm"]:
                alarm_count += 1
                self.trigger_reasons.append(f"Temp {t:.1f}°C >= {T['temp_alarm']}°C")
            elif t >= T["temp_warning"]:
                warning_count += 1
                self.trigger_reasons.append(f"Temp {t:.1f}°C >= {T['temp_warning']}°C")

        if h is not None:
            if h <= T["hum_alarm"]:
                alarm_count += 1
                self.trigger_reasons.append(f"Humidity {h:.1f}% <= {T['hum_alarm']}%")
            elif h <= T["hum_warning"]:
                warning_count += 1
                self.trigger_reasons.append(f"Humidity {h:.1f}% <= {T['hum_warning']}%")

        elapsed = time.time() - self._warmup_start
        if g is not None and elapsed >= self._warmup_duration:
            if g >= T["gas_alarm"]:
                alarm_count += 1
                self.trigger_reasons.append(f"Gas {g} >= {T['gas_alarm']}")
            elif g >= T["gas_warning"]:
                warning_count += 1
                self.trigger_reasons.append(f"Gas {g} >= {T['gas_warning']}")

        for det in vision_detections:
            label = det.get("label", "")
            conf = det.get("confidence", 0)
            if label == "fire":
                if conf >= T["yolo_fire_alarm"]:
                    alarm_count += 1
                    self.trigger_reasons.append(f"Fire detected ({conf:.0%})")
                elif conf >= T["yolo_fire_warning"]:
                    warning_count += 1
                    self.trigger_reasons.append(f"Fire detected ({conf:.0%})")
            elif label == "smoke":
                if conf >= T["yolo_smoke_alarm"]:
                    alarm_count += 1
                    self.trigger_reasons.append(f"Smoke detected ({conf:.0%})")
                elif conf >= T["yolo_smoke_warning"]:
                    warning_count += 1
                    self.trigger_reasons.append(f"Smoke detected ({conf:.0%})")

        if alarm_count > 0:
            new_state = STATE_ALARM
        elif warning_count > 0:
            new_state = STATE_WARNING
        else:
            new_state = STATE_SAFE

        self.prev_state = self.current_state
        self.current_state = new_state
        return new_state

    def warmup_remaining(self):
        elapsed = time.time() - self._warmup_start
        remaining = self._warmup_duration - elapsed
        return max(0, int(remaining))

    def get_led_buzzer(self):
        if self.current_state == STATE_SAFE:
            return ("G", 0)
        elif self.current_state == STATE_WARNING:
            return ("Y", 2)
        else:
            return ("R", 1)

    def state_changed(self):
        return self.current_state != self.prev_state

    def get_state_name(self, state=None):
        s = state if state is not None else self.current_state
        return {STATE_SAFE: "SAFE", STATE_WARNING: "WARNING", STATE_ALARM: "ALARM"}.get(s, "UNKNOWN")
