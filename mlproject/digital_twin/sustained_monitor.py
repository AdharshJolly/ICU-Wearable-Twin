# ============================================================
# PATIENT DIGITAL TWIN
# SUSTAINED ABNORMALITY DETECTION
# ============================================================

from datetime import datetime, timedelta


class SustainedAbnormalityMonitor:

    def __init__(self, sustained_minutes=10):

        self.sustained_minutes = sustained_minutes

        # When the current abnormal episode started
        self.abnormal_start_time = None

        # Whether a sustained alert has already been generated
        self.alert_generated = False

        # History
        self.history = []


    # --------------------------------------------------------
    # Check report-supported alert thresholds
    # --------------------------------------------------------

    def check_thresholds(self, measurement):

        triggered_rules = []


        # Paper 15:
        # Heart rate > 131 bpm
        if measurement["RestingHR"] > 131:

            triggered_rules.append(
                "Heart rate > 131 bpm"
            )


        # Paper 15:
        # Respiratory rate > 25/min
        if measurement["RespRate"] > 25:

            triggered_rules.append(
                "Respiratory rate > 25/min"
            )


        # Paper 15:
        # Temperature 38.1°C
        if measurement["BodyTemp_C"] >= 38.1:

            triggered_rules.append(
                "Body temperature >= 38.1°C"
            )


        return triggered_rules


    # --------------------------------------------------------
    # Process one measurement
    # --------------------------------------------------------

    def process(self, measurement, timestamp):

        triggered_rules = self.check_thresholds(
            measurement
        )


        is_abnormal = len(triggered_rules) > 0


        # ----------------------------------------------------
        # Normal measurement
        # ----------------------------------------------------

        if not is_abnormal:

            self.abnormal_start_time = None
            self.alert_generated = False

            result = {
                "timestamp": timestamp,
                "abnormal": False,
                "sustained": False,
                "duration_minutes": 0,
                "alert": False,
                "rules": []
            }

            self.history.append(result)

            return result


        # ----------------------------------------------------
        # First abnormal measurement
        # ----------------------------------------------------

        if self.abnormal_start_time is None:

            self.abnormal_start_time = timestamp

            self.alert_generated = False


        # ----------------------------------------------------
        # Calculate duration
        # ----------------------------------------------------

        duration = (
            timestamp
            - self.abnormal_start_time
        ).total_seconds() / 60


        # ----------------------------------------------------
        # Check sustained abnormality
        # ----------------------------------------------------

        sustained = (
            duration >= self.sustained_minutes
        )


        alert = (
            sustained
            and not self.alert_generated
        )


        if alert:

            self.alert_generated = True


        result = {

            "timestamp": timestamp,

            "abnormal": True,

            "sustained": sustained,

            "duration_minutes": duration,

            "alert": alert,

            "rules": triggered_rules
        }


        self.history.append(result)


        return result


    # --------------------------------------------------------
    # Display history
    # --------------------------------------------------------

    def display_history(self):

        print("\n==========================================")
        print("SUSTAINED ABNORMALITY HISTORY")
        print("==========================================")


        for record in self.history:

            print("\nTime:", record["timestamp"])

            print(
                "Abnormal:",
                record["abnormal"]
            )

            print(
                "Duration:",
                round(
                    record["duration_minutes"],
                    2
                ),
                "minutes"
            )

            print(
                "Sustained:",
                record["sustained"]
            )

            print(
                "Alert:",
                record["alert"]
            )


            if record["rules"]:

                print("Triggered Rules:")

                for rule in record["rules"]:

                    print(" -", rule)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    monitor = SustainedAbnormalityMonitor(
        sustained_minutes=10
    )


    start_time = datetime.now()


    # --------------------------------------------------------
    # Simulated wearable readings
    #
    # One reading every 2 minutes
    # --------------------------------------------------------

    measurements = [

        {
            "RestingHR": 75,
            "RespRate": 16,
            "BodyTemp_C": 36.8
        },

        {
            "RestingHR": 80,
            "RespRate": 17,
            "BodyTemp_C": 37.0
        },

        {
            "RestingHR": 135,
            "RespRate": 27,
            "BodyTemp_C": 38.2
        },

        {
            "RestingHR": 138,
            "RespRate": 28,
            "BodyTemp_C": 38.3
        },

        {
            "RestingHR": 140,
            "RespRate": 29,
            "BodyTemp_C": 38.4
        },

        {
            "RestingHR": 142,
            "RespRate": 30,
            "BodyTemp_C": 38.5
        },

        {
            "RestingHR": 145,
            "RespRate": 31,
            "BodyTemp_C": 38.6
        },

        {
            "RestingHR": 148,
            "RespRate": 32,
            "BodyTemp_C": 38.7
        }
    ]


    for i, measurement in enumerate(
        measurements
    ):

        timestamp = (
            start_time
            + timedelta(minutes=i * 2)
        )


        result = monitor.process(
            measurement,
            timestamp
        )


        print("\n------------------------------------------")

        print(
            "Measurement:",
            i + 1
        )

        print(
            "Time:",
            timestamp
        )

        print(
            "Abnormal:",
            result["abnormal"]
        )

        print(
            "Duration:",
            result["duration_minutes"],
            "minutes"
        )

        print(
            "Sustained:",
            result["sustained"]
        )

        print(
            "ALERT:",
            result["alert"]
        )

        if result["rules"]:

            print("Rules:")

            for rule in result["rules"]:

                print(" -", rule)


    monitor.display_history()