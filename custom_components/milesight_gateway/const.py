"""Constants for the Milesight Gateway integration."""

DOMAIN = "milesight_gateway"

CONF_GATEWAY_URL = "gateway_url"
CONF_GATEWAY_MQTT_BASE_TOPIC = "gateway_mqtt_base_topic"
CONF_HA_TOPIC = "ha_topic"
CONF_SECRET_KEY = "secret_key"
CONF_IV = "iv"

DEFAULT_PORT = 8080
DEFAULT_HA_TOPIC = "homeassistant"
DEFAULT_SECRET_KEY = "1111111111111111"
DEFAULT_IV = "2222222222222222"
DEFAULT_GATEWAY_MQTT_BASE_TOPIC = "sensors/lora/uplink"
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes — device list rarely changes
MIN_SCAN_INTERVAL = 60
