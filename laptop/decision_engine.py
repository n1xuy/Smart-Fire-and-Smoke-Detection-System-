from config import THRESHOLDS, STATE_SAFE, STATE_WARNING, STATE_ALARM

T = THRESHOLDS

class DecisionEngine:
    def __init__(self):
        self.current_state = STATE_SAFE
        self.prev_state = STATE_SAFE

    def evaluate(self, sensor_data, vision_detections):
        t = sensor_data.get("temperature", 0)
        h = sensor_data.get("humidity", 0)
        g = sensor_data.get("gas", 0)

        alarm_count = 0
        warning_count = 0

        if t >= T["temp_alarm"]:
            alarm_count += 1
        elif t >= T["temp_warning"]:
            warning_count += 1

        if h <= T["hum_alarm"]:
            alarm_count += 1
        elif h <= T["hum_warning"]:
            warning_count += 1

        if g >= T["gas_alarm"]:
            alarm_count += 1
        elif g >= T["gas_warning"]:
            warning_count += 1

        for det in vision_detections:
            label = det.get("label", "")
            conf = det.get("confidence", 0)
            if label == "fire":
                if conf >= T["yolo_fire_alarm"]:
                    alarm_count += 1
                elif conf >= T["yolo_fire_warning"]:
                    warning_count += 1
            elif label == "smoke":
                if conf >= T["yolo_smoke_alarm"]:
                    alarm_count += 1
                elif conf >= T["yolo_smoke_warning"]:
                    warning_count += 1

        if alarm_count > 0:
            new_state = STATE_ALARM
        elif warning_count > 0:
            new_state = STATE_WARNING
        else:
            new_state = STATE_SAFE

        self.prev_state = self.current_state
        self.current_state = new_state
        return new_state

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
