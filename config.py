# BARCODE PRINTING
# "printers" is the allowlist: a print request naming anything else is rejected.
# The list is never sent to the browser — users type the name of the printer they are at.
PRINT_CONFIG = {
    "printer_topic_prefix": "crucible-printer",
    "printers": ["ucd1", "b30-113", "b67-1202", "print1"],
    # A batch is published synchronously, so max_batch * print_delay_s is the worst-case
    # request duration. Keep the product well under any proxy timeout.
    "max_batch": 100,
    "print_delay_s": 0.1,
}
