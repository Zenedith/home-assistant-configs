"""Support for Airly air quality sensors."""
from logging import getLogger
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MONITORED_CONDITIONS,
    CONF_SCAN_INTERVAL,
    CONF_SHOW_ON_MAP,
    CONF_REGION
)
from homeassistant.helpers import aiohttp_client, config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = getLogger(__name__)

ATTR_POLLUTANT_SYMBOL = "pollutant_symbol"
ATTR_POLLUTANT_UNIT = "pollutant_unit"

DEFAULT_ATTRIBUTION = "Data provided by Airly.eu"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)

VOLUME_MICROGRAMS_PER_CUBIC_METER = "µg/m3"

SENSOR_VALUES = ["PM1", "PM2.5", "PM10", "CAQI", "PM2.5 percent", "PM10 percent", "CAQI level"]
MESSAGE_LOCALES = {"en": "English", "pl": "Polish"}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_MONITORED_CONDITIONS, default=SENSOR_VALUES): vol.All(
            cv.ensure_list, [vol.In(SENSOR_VALUES)]
        ),
        vol.Required(CONF_REGION, default="en"): vol.Any(cv.ensure_list, [vol.In(MESSAGE_LOCALES)]),
        vol.Inclusive(CONF_LATITUDE, "coords"): cv.latitude,
        vol.Inclusive(CONF_LONGITUDE, "coords"): cv.longitude,
        vol.Optional(CONF_SHOW_ON_MAP, default=True): cv.boolean,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Configure the platform and add the sensors."""

    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    websession = aiohttp_client.async_get_clientsession(hass)

    _LOGGER.debug("Using latitude and longitude: %s, %s", latitude, longitude)
    location_id = ",".join((str(latitude), str(longitude)))
    data = AirlyData(
        session=websession,
        api_key=config[CONF_API_KEY],
        latitude=latitude,
        longitude=longitude,
        show_on_map=config[CONF_SHOW_ON_MAP],
        scan_interval=config[CONF_SCAN_INTERVAL],
    )

    await data.async_update()

    sensors = []
    for sensor_type in config[CONF_MONITORED_CONDITIONS]:

        if sensor_type == "CAQI":
            unit = "CAQI"
        elif sensor_type.endswith("percent"):
            unit = "%"
        elif sensor_type.startswith("PM"):
            unit = VOLUME_MICROGRAMS_PER_CUBIC_METER
        else:
            unit = None

        sensors.append(
            AirlySensor(data, sensor_type, sensor_type, "mdi:chart-line", unit, sensor_type, location_id)
        )

    async_add_entities(sensors, True)


class AirlySensor(Entity):
    """Define an AirVisual sensor."""

    def __init__(self, airly, kind, name, icon, unit, sensor_type, location_id):
        """Initialize."""
        self._attrs = {ATTR_ATTRIBUTION: DEFAULT_ATTRIBUTION}
        self._icon = icon
        self._sensor_type = sensor_type
        self._location_id = location_id
        self._name = name
        self._state = None
        self._type = kind
        self._unit = unit
        self.airly = airly

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        if self.airly.show_on_map:
            self._attrs[ATTR_LATITUDE] = self.airly.latitude
            self._attrs[ATTR_LONGITUDE] = self.airly.longitude
        else:
            self._attrs["lati"] = self.airly.latitude
            self._attrs["long"] = self.airly.longitude

        return self._attrs

    @property
    def available(self):
        """Return True if entity is available."""
        return bool(self.airly.pollution_info)

    @property
    def icon(self):
        """Return the icon."""
        return self._icon

    @property
    def name(self):
        """Return the name."""
        return "{0} {1}".format("Airly", self._name)

    @property
    def state(self):
        """Return the state."""
        return self._state

    @property
    def unique_id(self):
        """Return a unique, HASS-friendly identifier for this entity."""
        return f"{self._location_id}_{self._sensor_type}_{self._type}_v2"

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit

    async def async_update(self):
        """Update the sensor."""
        await self.airly.async_update()
        data = self.airly.pollution_info

        if not data:
            return

        if self._type == "CAQI":
            self._state = data["indexes"][0]["value"]
        elif self._type == "PM1":
            self._state = data["values"][0]["value"]
        elif self._type == "PM2.5":
            self._state = data["values"][1]["value"]
        elif self._type == "PM10":
            self._state = data["values"][2]["value"]
        elif self._type == "PM2.5 percent":
            self._state = data["standards"][0]["percent"]
        elif self._type == "PM10 percent":
            self._state = data["standards"][1]["percent"]
        elif self._type == "CAQI level":
            self._state = data["indexes"][0]["level"]


class AirlyData:
    """Define an object to hold sensor data."""

    def __init__(self, session, api_key, **kwargs):
        """Initialize."""
        self._session = session
        self._api_key = api_key
        self.latitude = kwargs.get(CONF_LATITUDE)
        self.longitude = kwargs.get(CONF_LONGITUDE)
        self.pollution_info = {}
        self.show_on_map = kwargs.get(CONF_SHOW_ON_MAP)

        self.async_update = Throttle(kwargs[CONF_SCAN_INTERVAL])(self._async_update)

    async def _async_update(self):
        """Update Airly data."""

        try:
            url = "https://airapi.airly.eu/v2/measurements/point"
            headers_map = {
                'Accept': "application/json",
                'apikey': self._api_key
            }
            query_map = {"lat": str(self.latitude), "lng": str(self.longitude)}
            async with self._session.get(url, params=query_map, headers=headers_map) as response:
                _LOGGER.debug("New data retrieved: %s", response)
                self.pollution_info = (await response.json())["current"]

        except (KeyError, IOError) as err:
            location = (self.latitude, self.longitude)

            _LOGGER.error("Can't retrieve data for location: %s (%s)", location, err)
            self.pollution_info = {}
