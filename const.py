"""Constants for the Indevolt integration."""

from homeassistant.const import Platform

# fmt: off
DOMAIN = "indevolt"
DEFAULT_PORT = 8080
DEFAULT_SCAN_INTERVAL = 30
PLATFORMS = [
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]

SUPPORTED_MODELS = [
    "BK1600/BK1600Ultra",
    "SolidFlex/PowerFlex2000"
]
# fmt: on
