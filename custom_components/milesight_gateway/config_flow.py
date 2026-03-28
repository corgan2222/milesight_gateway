"""Config flow for the Milesight Gateway integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_PORT, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import APIAuthError, APIConnectionError, MilesightGatewayAPI
from .const import (
    CONF_GATEWAY_MQTT_BASE_TOPIC,
    CONF_GATEWAY_URL,
    CONF_IV,
    CONF_SECRET_KEY,
    DEFAULT_GATEWAY_MQTT_BASE_TOPIC,
    DEFAULT_IV,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SECRET_KEY,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_GATEWAY_URL): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_SECRET_KEY, default=DEFAULT_SECRET_KEY): str,
        vol.Required(CONF_IV, default=DEFAULT_IV): str,
        vol.Required(CONF_GATEWAY_MQTT_BASE_TOPIC, default=DEFAULT_GATEWAY_MQTT_BASE_TOPIC): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    api = MilesightGatewayAPI(
        gateway_url=data[CONF_GATEWAY_URL],
        port=data[CONF_PORT],
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        secret_key=data[CONF_SECRET_KEY],
        iv=data[CONF_IV],
        mqtt_base_topic=data[CONF_GATEWAY_MQTT_BASE_TOPIC],
    )
    try:
        session = async_get_clientsession(hass)
        await api.async_connect(session)
    except APIAuthError as err:
        raise InvalidAuth from err
    except APIConnectionError as err:
        raise CannotConnect from err

    return {"title": data[CONF_GATEWAY_URL]}


class MilesightGatewayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Milesight Gateway."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(_config_entry) -> MilesightGatewayOptionsFlow:
        """Return the options flow handler."""
        return MilesightGatewayOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                unique_id = f"{user_input[CONF_GATEWAY_URL]}:{user_input[CONF_PORT]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow the user to update credentials without removing the integration."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reconfigure_entry()

        if user_input is not None:
            try:
                full_data = {
                    **reauth_entry.data,
                    **user_input,
                    CONF_GATEWAY_URL: reauth_entry.data[CONF_GATEWAY_URL],
                    CONF_PORT: reauth_entry.data[CONF_PORT],
                }
                await validate_input(self.hass, full_data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    unique_id=reauth_entry.unique_id,
                    data={**reauth_entry.data, **user_input},
                    reason="reconfigure_successful",
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=reauth_entry.data[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_SECRET_KEY, default=reauth_entry.data[CONF_SECRET_KEY]): str,
                    vol.Required(CONF_IV, default=reauth_entry.data[CONF_IV]): str,
                    vol.Required(
                        CONF_GATEWAY_MQTT_BASE_TOPIC,
                        default=reauth_entry.data.get(
                            CONF_GATEWAY_MQTT_BASE_TOPIC, DEFAULT_GATEWAY_MQTT_BASE_TOPIC
                        ),
                    ): str,
                }
            ),
            errors=errors,
        )


class MilesightGatewayOptionsFlow(OptionsFlow):
    """Handle options for the Milesight Gateway integration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=self.config_entry.options | user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Clamp(min=MIN_SCAN_INTERVAL)),
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
