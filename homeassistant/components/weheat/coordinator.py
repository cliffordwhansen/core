"""Define a custom coordinator for the Weheat heatpump integration."""

from datetime import timedelta

from weheat.abstractions.discovery import HeatPumpDiscovery
from weheat.abstractions.heat_pump import HeatPump
from weheat.exceptions import (
    ApiException,
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ServiceException,
    UnauthorizedException,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, DOMAIN, LOGGER, UPDATE_INTERVAL

EXCEPTIONS = (
    ServiceException,
    NotFoundException,
    ForbiddenException,
    BadRequestException,
    ApiException,
)

type WeheatConfigEntry = ConfigEntry[list[WeheatDataUpdateCoordinator]]


class WeheatDataUpdateCoordinator(DataUpdateCoordinator[HeatPump]):
    """A custom coordinator for the Weheat heatpump integration."""

    config_entry: WeheatConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: WeheatConfigEntry,
        session: OAuth2Session,
        heat_pump: HeatPumpDiscovery.HeatPumpInfo,
    ) -> None:
        """Initialize the data coordinator."""
        super().__init__(
            hass,
            logger=LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.heat_pump_info = heat_pump
        self._heat_pump_data = HeatPump(
            API_URL, heat_pump.uuid, async_get_clientsession(hass)
        )

        self.session = session

    @property
    def heatpump_id(self) -> str:
        """Return the heat pump id."""
        return self.heat_pump_info.uuid

    @property
    def readable_name(self) -> str | None:
        """Return the readable name of the heat pump."""
        if self.heat_pump_info.name:
            return self.heat_pump_info.name
        return self.heat_pump_info.model

    @property
    def model(self) -> str:
        """Return the model of the heat pump."""
        return self.heat_pump_info.model

    async def _async_update_data(self) -> HeatPump:
        """Fetch data from the API."""
        await self.session.async_ensure_token_valid()

        try:
            await self._heat_pump_data.async_get_status(
                self.session.token[CONF_ACCESS_TOKEN]
            )
        except UnauthorizedException as error:
            raise ConfigEntryAuthFailed from error
        except EXCEPTIONS as error:
            raise UpdateFailed(error) from error

        return self._heat_pump_data
