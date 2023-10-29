# pylint: disable=line-too-long
""" A climate over switch classe """
import logging
from datetime import timedelta

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval

from homeassistant.components.climate import HVACAction, HVACMode

from .base_thermostat import BaseThermostat

from .const import CONF_CLIMATE, CONF_CLIMATE_2, CONF_CLIMATE_3, CONF_CLIMATE_4, overrides

from .underlyings import UnderlyingClimate

_LOGGER = logging.getLogger(__name__)

class ThermostatOverClimate(BaseThermostat):
    """Representation of a base class for a Versatile Thermostat over a climate"""

    _entity_component_unrecorded_attributes = BaseThermostat._entity_component_unrecorded_attributes.union(frozenset(
        {
            "is_over_climate", "start_hvac_action_date", "underlying_climate_0", "underlying_climate_1",
            "underlying_climate_2", "underlying_climate_3"
        }))

    # Useless for now
    # def __init__(self, hass: HomeAssistant, unique_id, name, entry_infos) -> None:
    #    """Initialize the thermostat over switch."""
    #    super().__init__(hass, unique_id, name, entry_infos)

    @property
    def is_over_climate(self) -> bool:
        """ True if the Thermostat is over_climate"""
        return True

    @property
    def hvac_action(self) -> HVACAction | None:
        """ Returns the current hvac_action by checking all hvac_action of the underlyings """

        # if one not IDLE or OFF -> return it
        # else if one IDLE -> IDLE
        # else OFF
        one_idle = False
        for under in self._underlyings:
            if (action := under.hvac_action) not in [
                HVACAction.IDLE,
                HVACAction.OFF,
            ]:
                return action
            if under.hvac_action == HVACAction.IDLE:
                one_idle = True
        if one_idle:
            return HVACAction.IDLE
        return HVACAction.OFF

    @property
    def hvac_modes(self):
        """List of available operation modes."""
        if self.underlying_entity(0):
            return self.underlying_entity(0).hvac_modes
        else:
            return super.hvac_modes

    @property
    def mean_cycle_power(self) -> float | None:
        """Returns the mean power consumption during the cycle"""
        return None

    @property
    def fan_mode(self) -> str | None:
        """Return the fan setting.

        Requires ClimateEntityFeature.FAN_MODE.
        """
        if self.underlying_entity(0):
            return self.underlying_entity(0).fan_mode

        return None

    @property
    def fan_modes(self) -> list[str] | None:
        """Return the list of available fan modes.

        Requires ClimateEntityFeature.FAN_MODE.
        """
        if self.underlying_entity(0):
            return self.underlying_entity(0).fan_modes

        return []

    @property
    def swing_mode(self) -> str | None:
        """Return the swing setting.

        Requires ClimateEntityFeature.SWING_MODE.
        """
        if self.underlying_entity(0):
            return self.underlying_entity(0).swing_mode

        return None

    @property
    def swing_modes(self) -> list[str] | None:
        """Return the list of available swing modes.

        Requires ClimateEntityFeature.SWING_MODE.
        """
        if self.underlying_entity(0):
            return self.underlying_entity(0).swing_modes

        return None

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        if self.underlying_entity(0):
            return self.underlying_entity(0).temperature_unit

        return self._unit

    @property
    def supported_features(self):
        """Return the list of supported features."""
        if self.underlying_entity(0):
            return self.underlying_entity(0).supported_features | self._support_flags

        return self._support_flags

    @property
    def target_temperature_step(self) -> float | None:
        """Return the supported step of target temperature."""
        if self.underlying_entity(0):
            return self.underlying_entity(0).target_temperature_step

        return None

    @property
    def target_temperature_high(self) -> float | None:
        """Return the highbound target temperature we try to reach.

        Requires ClimateEntityFeature.TARGET_TEMPERATURE_RANGE.
        """
        if self.underlying_entity(0):
            return self.underlying_entity(0).target_temperature_high

        return None

    @property
    def target_temperature_low(self) -> float | None:
        """Return the lowbound target temperature we try to reach.

        Requires ClimateEntityFeature.TARGET_TEMPERATURE_RANGE.
        """
        if self.underlying_entity(0):
            return self.underlying_entity(0).target_temperature_low

        return None

    @property
    def is_aux_heat(self) -> bool | None:
        """Return true if aux heater.

        Requires ClimateEntityFeature.AUX_HEAT.
        """
        if self.underlying_entity(0):
            return self.underlying_entity(0).is_aux_heat

        return None

    @overrides
    def turn_aux_heat_on(self) -> None:
        """Turn auxiliary heater on."""
        if self.underlying_entity(0):
            return self.underlying_entity(0).turn_aux_heat_on()

        raise NotImplementedError()

    @overrides
    async def async_turn_aux_heat_on(self) -> None:
        """Turn auxiliary heater on."""
        for under in self._underlyings:
            await under.async_turn_aux_heat_on()

    @overrides
    def turn_aux_heat_off(self) -> None:
        """Turn auxiliary heater off."""
        for under in self._underlyings:
            return under.turn_aux_heat_off()

    @overrides
    async def async_turn_aux_heat_off(self) -> None:
        """Turn auxiliary heater off."""
        for under in self._underlyings:
            await under.async_turn_aux_heat_off()

    @overrides
    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        _LOGGER.info("%s - Set fan mode: %s", self, fan_mode)
        if fan_mode is None:
            return

        for under in self._underlyings:
            await under.set_fan_mode(fan_mode)
        self._fan_mode = fan_mode
        self.async_write_ha_state()

    @overrides
    async def async_set_humidity(self, humidity: int):
        """Set new target humidity."""
        _LOGGER.info("%s - Set fan mode: %s", self, humidity)
        if humidity is None:
            return
        for under in self._underlyings:
            await under.set_humidity(humidity)
        self._humidity = humidity
        self.async_write_ha_state()

    @overrides
    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        _LOGGER.info("%s - Set fan mode: %s", self, swing_mode)
        if swing_mode is None:
            return
        for under in self._underlyings:
            await under.set_swing_mode(swing_mode)
        self._swing_mode = swing_mode
        self.async_write_ha_state()

    @overrides
    async def _async_internal_set_temperature(self, temperature):
        """Set the target temperature and the target temperature of underlying climate if any"""
        await super()._async_internal_set_temperature(temperature)

        for under in self._underlyings:
            await under.set_temperature(
                temperature, self._attr_max_temp, self._attr_min_temp
            )

    @overrides
    def post_init(self, entry_infos):
        """ Initialize the Thermostat"""

        super().post_init(entry_infos)
        for climate in [
            CONF_CLIMATE,
            CONF_CLIMATE_2,
            CONF_CLIMATE_3,
            CONF_CLIMATE_4,
        ]:
            if entry_infos.get(climate):
                self._underlyings.append(
                    UnderlyingClimate(
                        hass=self._hass,
                        thermostat=self,
                        climate_entity_id=entry_infos.get(climate),
                    )
                )

    @overrides
    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        _LOGGER.debug("Calling async_added_to_hass")

        await super().async_added_to_hass()

        # Add listener to all underlying entities
        for climate in self._underlyings:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [climate.entity_id], self._async_climate_changed
                )
            )

        # Start the control_heating
        # starts a cycle
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self.async_control_heating,
                interval=timedelta(minutes=self._cycle_min),
            )
        )

    @overrides
    def update_custom_attributes(self):
        """ Custom attributes """
        super().update_custom_attributes()

        self._attr_extra_state_attributes["is_over_climate"] = self.is_over_climate
        self._attr_extra_state_attributes["start_hvac_action_date"] = (
            self._underlying_climate_start_hvac_action_date)
        self._attr_extra_state_attributes["underlying_climate_0"] = (
                self._underlyings[0].entity_id)
        self._attr_extra_state_attributes["underlying_climate_1"] = (
                self._underlyings[1].entity_id if len(self._underlyings) > 1 else None
            )
        self._attr_extra_state_attributes["underlying_climate_2"] = (
                self._underlyings[2].entity_id if len(self._underlyings) > 2 else None
            )
        self._attr_extra_state_attributes["underlying_climate_3"] = (
                self._underlyings[3].entity_id if len(self._underlyings) > 3 else None
            )

        self.async_write_ha_state()
        _LOGGER.debug(
            "%s - Calling update_custom_attributes: %s",
            self,
            self._attr_extra_state_attributes,
        )

    @overrides
    def recalculate(self):
        """A utility function to force the calculation of a the algo and
        update the custom attributes and write the state
        """
        _LOGGER.debug("%s - recalculate all", self)
        self.update_custom_attributes()
        self.async_write_ha_state()

    @overrides
    async def restore_hvac_mode(self, need_control_heating=False):
        """Restore a previous hvac_mod"""
        old_hvac_mode = self.hvac_mode

        await super().restore_hvac_mode(need_control_heating=need_control_heating)

        # Issue 133 - force the temperature in over_climate mode if unerlying are turned on
        if old_hvac_mode == HVACMode.OFF and self.hvac_mode != HVACMode.OFF:
            _LOGGER.info(
                "%s - Force resent target temp cause we turn on some over climate"
            )
            await self._async_internal_set_temperature(self._target_temp)

    @overrides
    def incremente_energy(self):
        """increment the energy counter if device is active"""

        if self.hvac_mode == HVACMode.OFF:
            return

        added_energy = 0
        if self.is_over_climate and self._underlying_climate_delta_t is not None:
            added_energy = self._device_power * self._underlying_climate_delta_t

        self._total_energy += added_energy
        _LOGGER.debug(
            "%s - added energy is %.3f . Total energy is now: %.3f",
            self,
            added_energy,
            self._total_energy,
        )

    @callback
    async def _async_climate_changed(self, event):
        """Handle unerdlying climate state changes.
        This method takes the underlying values and update the VTherm with them.
        To avoid loops (issues #121 #101 #95 #99), we discard the event if it is received
        less than 10 sec after the last command. What we want here is to take the values
        from underlyings ONLY if someone have change directly on the underlying and not
        as a return of the command. The only thing we take all the time is the HVACAction
        which is important for feedaback and which cannot generates loops.
        """

        async def end_climate_changed(changes):
            """To end the event management"""
            if changes:
                self.async_write_ha_state()
                self.update_custom_attributes()
                await self.async_control_heating()

        new_state = event.data.get("new_state")
        _LOGGER.debug("%s - _async_climate_changed new_state is %s", self, new_state)
        if not new_state:
            return

        changes = False
        new_hvac_mode = new_state.state

        old_state = event.data.get("old_state")
        old_hvac_action = (
            old_state.attributes.get("hvac_action")
            if old_state and old_state.attributes
            else None
        )
        new_hvac_action = (
            new_state.attributes.get("hvac_action")
            if new_state and new_state.attributes
            else None
        )

        old_state_date_changed = (
            old_state.last_changed if old_state and old_state.last_changed else None
        )
        old_state_date_updated = (
            old_state.last_updated if old_state and old_state.last_updated else None
        )
        new_state_date_changed = (
            new_state.last_changed if new_state and new_state.last_changed else None
        )
        new_state_date_updated = (
            new_state.last_updated if new_state and new_state.last_updated else None
        )

        # Issue 99 - some AC turn hvac_mode=cool and hvac_action=idle when sending a HVACMode_OFF command
        # Issue 114 - Remove this because hvac_mode is now managed by local _hvac_mode and use idle action as is
        # if self._hvac_mode == HVACMode.OFF and new_hvac_action == HVACAction.IDLE:
        #    _LOGGER.debug("The underlying switch to idle instead of OFF. We will consider it as OFF")
        #    new_hvac_mode = HVACMode.OFF

        _LOGGER.info(
            "%s - Underlying climate changed. Event.new_hvac_mode is %s, current_hvac_mode=%s, new_hvac_action=%s, old_hvac_action=%s",
            self,
            new_hvac_mode,
            self._hvac_mode,
            new_hvac_action,
            old_hvac_action,
        )

        _LOGGER.debug(
            "%s - last_change_time=%s old_state_date_changed=%s old_state_date_updated=%s new_state_date_changed=%s new_state_date_updated=%s",
            self,
            self._last_change_time,
            old_state_date_changed,
            old_state_date_updated,
            new_state_date_changed,
            new_state_date_updated,
        )

        # Interpretation of hvac action
        HVAC_ACTION_ON = [  # pylint: disable=invalid-name
            HVACAction.COOLING,
            HVACAction.DRYING,
            HVACAction.FAN,
            HVACAction.HEATING,
        ]
        if old_hvac_action not in HVAC_ACTION_ON and new_hvac_action in HVAC_ACTION_ON:
            self._underlying_climate_start_hvac_action_date = (
                self.get_last_updated_date_or_now(new_state)
            )
            _LOGGER.info(
                "%s - underlying just switch ON. Set power and energy start date %s",
                self,
                self._underlying_climate_start_hvac_action_date.isoformat(),
            )
            changes = True

        if old_hvac_action in HVAC_ACTION_ON and new_hvac_action not in HVAC_ACTION_ON:
            stop_power_date = self.get_last_updated_date_or_now(new_state)
            if self._underlying_climate_start_hvac_action_date:
                delta = (
                    stop_power_date - self._underlying_climate_start_hvac_action_date
                )
                self._underlying_climate_delta_t = delta.total_seconds() / 3600.0

                # increment energy at the end of the cycle
                self.incremente_energy()

                self._underlying_climate_start_hvac_action_date = None

            _LOGGER.info(
                "%s - underlying just switch OFF at %s. delta_h=%.3f h",
                self,
                stop_power_date.isoformat(),
                self._underlying_climate_delta_t,
            )
            changes = True

        # Issue #120 - Some TRV are chaning target temperature a very long time (6 sec) after the change.
        # In that case a loop is possible if a user change multiple times during this 6 sec.
        if new_state_date_updated and self._last_change_time:
            delta = (new_state_date_updated - self._last_change_time).total_seconds()
            if delta < 10:
                _LOGGER.info(
                    "%s - underlying event is received less than 10 sec after command. Forget it to avoid loop",
                    self,
                )
                await end_climate_changed(changes)
                return

        if (
            new_hvac_mode
            in [
                HVACMode.OFF,
                HVACMode.HEAT,
                HVACMode.COOL,
                HVACMode.HEAT_COOL,
                HVACMode.DRY,
                HVACMode.AUTO,
                HVACMode.FAN_ONLY,
                None,
            ]
            and self._hvac_mode != new_hvac_mode
        ):
            changes = True
            self._hvac_mode = new_hvac_mode
            # Update all underlyings state
            if self.is_over_climate:
                for under in self._underlyings:
                    await under.set_hvac_mode(new_hvac_mode)

        if not changes:
            # try to manage new target temperature set if state
            _LOGGER.debug(
                "Do temperature check. temperature is %s, new_state.attributes is %s",
                self.target_temperature,
                new_state.attributes,
            )
            if (
                self.is_over_climate
                and new_state.attributes
                and (new_target_temp := new_state.attributes.get("temperature"))
                and new_target_temp != self.target_temperature
            ):
                _LOGGER.info(
                    "%s - Target temp in underlying have change to %s",
                    self,
                    new_target_temp,
                )
                await self.async_set_temperature(temperature=new_target_temp)
                changes = True

        await end_climate_changed(changes)