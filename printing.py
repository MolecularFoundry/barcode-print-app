import json
import os
import time
import uuid

import paho.mqtt.publish as publish

from config import PRINT_CONFIG


def resolve_printer(printer):
    """Turn user input into a validated short printer name.

    Accepts either "b30-113" or the fully qualified "crucible-printer/b30-113".
    The name ends up in an MQTT topic, so it is checked against the allowlist in
    PRINT_CONFIG rather than merely sanitized.

    The error deliberately does not name the valid printers — users are expected to
    know the printer they are standing next to.
    """
    prefix = PRINT_CONFIG["printer_topic_prefix"] + "/"
    name = str(printer or "").strip().lower()
    if name.startswith(prefix):
        name = name[len(prefix):]
    if not name:
        raise ValueError("No printer name given")
    if name not in PRINT_CONFIG["printers"]:
        raise ValueError(f"'{name}' is not a known printer")
    return name


def publish_barcode(printer, mfid, name=""):
    """Send one label job to a Crucible label printer over MQTT."""
    topic = f"{PRINT_CONFIG['printer_topic_prefix']}/{resolve_printer(printer)}/print"
    payload = {
        "job_id": str(uuid.uuid4()),
        "mfid": mfid,
        "name": name,
        "ts": time.time(),
    }

    publish.single(
        topic=topic,
        payload=json.dumps(payload),
        hostname=os.environ.get("MQTT_BROKER", "mqtt.mfdata.org"),
        port=int(os.environ.get("MQTT_PORT", "8883")),
        auth={
            "username": os.environ.get("MQTT_USERNAME", "crucible-printers"),
            "password": os.environ.get("MQTT_PASSWORD"),
        },
        tls={"ca_certs": None},
    )
