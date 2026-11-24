"""
This tests requests for Air Purifiers.

All tests inherit from the TestBase class which contains the fixtures
and methods needed to run the tests.

The tests are automatically parametrized by `pytest_generate_tests` in
conftest.py. The two methods that are parametrized are `test_details`
and `test_methods`. The class variables are used to build the list of
devices, test methods and arguments.

The `helpers.call_api` method is patched to return a mock response.
The method, endpoint, headers and json arguments are recorded
in YAML files in the api directory, categorized in folders by
module and files by the class name.

The default is to record requests that do not exist and compare requests
that already exist. If the API changes, set the overwrite argument to True
in order to overwrite the existing YAML file with the new request.

See Also
--------
`utils.TestBase` - Base class for all tests, containing mock objects
`confest.pytest_generate_tests` - Parametrizes tests based on
    method names & class attributes
`call_json_fans` - Contains API responses
"""

import logging
import pytest

import pyvesync.const as const
from pyvesync.base_devices.purifier_base import VeSyncPurifier
from base_test_cases import TestBase
from utils import assert_test, parse_args
import call_json_purifiers


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestAirPurifiers(TestBase):
    """Air Purifier testing class.

    This class tests Air Purifier device details and methods.
    The methods are parametrized from the class variables using
    `pytest_generate_tests`. The call_json_fans module contains the responses
    for the API requests. The device is instantiated from the details provided by
    `call_json.DeviceList.device_list_item()`. Inherits from `utils.TestBase`.

    Instance Attributes
    -------------------
    self.manager : VeSync
        Instantiated VeSync object
    self.mock_api : Mock
        Mock with patched `helpers.call_api` method
    self.caplog : LogCaptureFixture
        Pytest fixture for capturing logs

    Class Attributes
    ---------------
    device : str
        Name of product class - air_purifiers
    air_purifiers : list
        List of setup_entry's for air purifiers, this variable is named
        after the device variable value
    base_methods : List[List[str, Dict[str, Any]]]
        List of common methods for all devices
    device_methods : Dict[List[List[str, Dict[str, Any]]]]
        Dictionary of methods specific to device types

    Methods
    --------
    test_details()
        Test the device details API request and response
    test_methods()
        Test device methods API request and response

    Examples
    --------
    >>> device = 'air_purifiers'
    >>> air_purifiers = call_json_fans.AIR_MODELS
    >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
    >>> device_methods = {
        'ESWD16': [['method1'], ['method2', {'kwargs': 'value'}]]
        }
    """

    device = "air_purifiers"
    air_purifiers = call_json_purifiers.PURIFIER_MODELS
    base_methods = [
        ["turn_on"],
        ["turn_off"],
        ["set_manual_mode"],
        ["set_fan_speed", {"speed": 3}],
    ]
    # TODO: Add timer tests
    device_methods = {
        "Core200S": [["set_sleep_mode"],],
        "Core300S": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "Core400S": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "Core600S": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "LV-PUR131S": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "LV-RH131S": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "LAP-V102S": [["set_auto_mode"], ['set_sleep_mode'], ['set_pet_mode'], ["turn_on_display"], ["turn_off_display"]],
        "LAP-V201S": [["set_auto_mode"], ['set_sleep_mode'], ['set_pet_mode'], ["turn_on_display"], ["turn_off_display"]],
        "EL551S": [["set_auto_mode"], ["set_sleep_mode"], ["set_turbo_mode"], ["turn_on_display"], ["turn_off_display"]],
        "LAP-B851S-WUS": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],

    }

    def test_details(self, setup_entry, method):
        """Test the device details API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of product class - air_purifiers),
        device name (air_purifiers) list of device types.

        Example:
            >>> device = 'air_purifiers'
            >>> air_purifiers = call_json_fans.AIR_MODELS

        See Also
        --------
        `utils.TestBase` class docstring
        `call_json_fans` module docstring

        Notes
        ------
        The device is instantiated using the `call_json.DeviceList.device_list_item()`
        method. The device details contain the default values set in `utils.Defaults`
        """
        # Set return value for call_api based on call_json_fan.DETAILS_RESPONSES
        return_dict = call_json_purifiers.DETAILS_RESPONSES[setup_entry]
        return_val = (return_dict, 200)
        self.mock_api.return_value = return_val

        # Instantiate device from device list return item
        fan_obj = self.get_device("air_purifiers", setup_entry)
        assert isinstance(fan_obj, VeSyncPurifier)

        method_call = getattr(fan_obj, method)
        self.run_in_loop(method_call)

        # Test state attributes
        assert fan_obj.state.device_status == const.DeviceStatus.ON
        assert fan_obj.state.mode == call_json_purifiers.PurifierDefaults.purifier_mode
        assert fan_obj.state.fan_level == call_json_purifiers.PurifierDefaults.fan_level

        # Parse mock_api args tuple from arg, kwargs to kwargs
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recorded request or write new records
        assert assert_test(
            method_call, all_kwargs, setup_entry, self.write_api, self.overwrite
        )

    def test_sprout_weu_fourth_speed(self):
        """Send the verified fourth manual speed only on the WEU model."""
        device = self.get_device("air_purifiers", "LAP-B851S-WEU")
        assert device.fan_levels == [1, 2, 3, 4]
        self.mock_api.return_value = ({"code": 0, "result": {"code": 0}}, 200)
        assert self.run_in_loop(device.set_fan_speed, 4)

        payload = parse_args(self.mock_api)["json_object"]["payload"]
        assert payload["method"] == "setLevel"
        assert payload["data"] == {
            "levelIdx": 0,
            "manualSpeedLevel": 4,
            "levelType": "wind",
        }

        other = self.get_device("air_purifiers", "LAP-B851S-WUS")
        self.mock_api.reset_mock()
        assert self.run_in_loop(other.set_fan_speed, 4) is False
        self.mock_api.assert_not_called()

    def test_sprout_weu_fan_modes(self):
        """Expose the two fan modes offered by the VeSync app on WEU."""
        device = self.get_device("air_purifiers", "LAP-B851S-WEU")
        assert set(device.modes) == {const.PurifierModes.MANUAL, const.PurifierModes.AUTO}
        self.mock_api.reset_mock()
        assert self.run_in_loop(device.set_sleep_mode) is False
        self.mock_api.assert_not_called()

    def test_sprout_temperature_refresh(self):
        """Preserve tenths of a degree and keep a null reading unknown."""
        device = self.get_device("air_purifiers", "LAP-B851S-WEU")
        details = call_json_purifiers.PURIFIER_DETAILS["LAP-B851S-WUS"]
        for raw, expected in ((609, 60.9), (0, 0.0), (None, None)):
            response = call_json_purifiers.build_bypass_v2_response(
                inner_result={**details, "temperature": raw}
            )
            self.mock_api.return_value = (response, 200)
            self.run_in_loop(device.update)
            assert device.state.temperature == expected

    def test_sprout_filter_life_refresh(self):
        """Read the filter percentage and preserve it across incomplete polls."""
        setup_entry = "LAP-B851S-WUS"
        device = self.get_device("air_purifiers", setup_entry)
        device.device_type = "LAP-B851S-WEU"
        details = call_json_purifiers.PURIFIER_DETAILS[setup_entry]
        assert device.state.filter_life is None

        for fields, expected in (
            ({"filterLifePercent": 76}, 76),
            ({}, 76),
            ({"filterLifePercent": 0}, 0),
        ):
            response = call_json_purifiers.build_bypass_v2_response(
                inner_result={**details, **fields}
            )
            self.mock_api.return_value = (response, 200)
            self.run_in_loop(device.update)
            assert device.state.filter_life == expected

    def test_sprout_nightlight_refresh(self):
        """Refresh power, brightness and colour temperature from each poll."""
        setup_entry = "LAP-B851S-WUS"
        device = self.get_device("air_purifiers", setup_entry)
        details = call_json_purifiers.PURIFIER_DETAILS[setup_entry]
        initial_light = details["nightLight"]
        updated_light = {"nightLightSwitch": 0, "brightness": 20, "colorTemperature": 2700}
        for light, expected_light in (
            (initial_light, initial_light),
            (updated_light, updated_light),
            (None, updated_light),
        ):
            poll_details = {key: value for key, value in details.items() if key != "nightLight"}
            if light is not None:
                poll_details["nightLight"] = light
            response = call_json_purifiers.build_bypass_v2_response(
                inner_result=poll_details
            )
            self.mock_api.return_value = (response, 200)
            self.run_in_loop(device.update)
            assert device.state.nightlight_status == const.DeviceStatus.from_int(
                expected_light["nightLightSwitch"]
            )
            assert device.state.nightlight_brightness == expected_light["brightness"]
            assert device.state.nightlight_color_temp == expected_light["colorTemperature"]

    @pytest.mark.parametrize(
        ("response", "accepted"),
        [
            ({"code": 0, "result": {"code": 0}}, True),
            ({"code": 0, "result": {"code": -1}}, False),
            ({"code": 0, "result": {"code": "-1"}}, False),
            ({"code": 0}, False),
            ({"code": 0, "result": {"code": "invalid"}}, False),
            ({"code": "invalid", "result": {"code": 0}}, False),
        ],
    )
    def test_sprout_weu_auto_preference(self, response, accepted):
        """Update the cached preference only after a confirmed command."""
        device = self.get_device("air_purifiers", "LAP-B851S-WUS")
        device.device_type = "LAP-B851S-WEU"
        device.state.auto_preference_type = "default"
        device.state.auto_room_size = 152
        self.mock_api.return_value = (response, 200)

        assert self.run_in_loop(device.set_auto_preference, "quiet") is accepted
        payload = parse_args(self.mock_api)["json_object"]["payload"]
        assert payload["method"] == "setAutoPreference"
        assert payload["data"] == {"autoPreferenceType": "quiet", "roomSize": 152}
        assert device.state.auto_preference_type == ("quiet" if accepted else "default")
        assert device.state.auto_room_size == 152

    @pytest.mark.parametrize("code", [0, "-1"])
    @pytest.mark.parametrize(
        ("method", "switch", "previous_state"),
        [
            ("turn_on_nightlight", 1, const.DeviceStatus.OFF),
            ("turn_off_nightlight", 0, const.DeviceStatus.ON),
        ],
    )
    def test_sprout_weu_nightlight_power(self, code, method, switch, previous_state):
        """Send the captured request and leave power state to the next poll."""
        device = self.get_device("air_purifiers", "LAP-B851S-WUS")
        device.device_type = "LAP-B851S-WEU"
        device.state.nightlight_status = previous_state
        device.state.nightlight_brightness = 18
        device.state.nightlight_color_temp = 2000
        self.mock_api.return_value = ({"code": 0, "result": {"code": code}}, 200)

        assert self.run_in_loop(getattr(device, method)) is (code == 0)
        payload = parse_args(self.mock_api)["json_object"]["payload"]
        assert payload["method"] == "setLightStatus"
        assert payload["data"] == {
            "nightLightSwitch": switch,
            "brightness": 18,
            "colorTemperature": 2000,
            "colorMode": "white",
        }
        assert device.state.nightlight_status == previous_state

    @pytest.mark.parametrize(
        ("settings", "brightness", "color_temp"),
        [
            ({"brightness": 30, "color_temp_kelvin": 2700}, 30, 2700),
            ({"brightness": 30}, 30, 2000),
            ({"color_temp_kelvin": 2700}, 18, 2700),
        ],
    )
    def test_sprout_weu_nightlight_settings(self, settings, brightness, color_temp):
        """Send new settings while retaining omitted values and polled state."""
        device = self.get_device("air_purifiers", "LAP-B851S-WUS")
        device.device_type = "LAP-B851S-WEU"
        device.state.nightlight_brightness = 18
        device.state.nightlight_color_temp = 2000
        self.mock_api.return_value = ({"code": 0, "result": {"code": 0}}, 200)

        assert self.run_in_loop(device.set_nightlight_mode, "on", **settings)
        payload = parse_args(self.mock_api)["json_object"]["payload"]
        assert payload["method"] == "setLightStatus"
        assert payload["data"] == {
            "nightLightSwitch": 1,
            "brightness": brightness,
            "colorTemperature": color_temp,
            "colorMode": "white",
        }
        assert device.state.nightlight_brightness == 18
        assert device.state.nightlight_color_temp == 2000

    def test_sprout_weu_auto_preference_requires_room_size(self):
        """Avoid sending an arbitrary room size when it has yet to be reported."""
        device = self.get_device("air_purifiers", "LAP-B851S-WUS")
        device.device_type = "LAP-B851S-WEU"
        self.mock_api.reset_mock()

        assert self.run_in_loop(device.set_auto_preference, "quiet") is False
        self.mock_api.assert_not_called()

    def test_methods(self, setup_entry, method):
        """Test device methods API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of product class - air_purifiers),
        device name (air_purifiers) list of setup_entry's, `base_methods` - list of
        methods for all devices, and `device_methods` - list of methods for
        each device type.

        Example:
            >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
            >>> device_methods = {
                'setup_entry': [['method1'], ['method2', {'kwargs': 'value'}]]
                }

        Notes
        -----
        The response can be a callable that accepts the `kwargs` argument to
        sync the device response with the API response. In some cases the API
        returns data from the method call, such as `get_yearly_energy`, in other cases the
        API returns a simple confirmation the command was successful.

        See Also
        --------
        `TestBase` class method
        `call_json_fans` module

        """
        # TODO: FIX `clear_timer` recorded API request in yaml
        if method[0] == "clear_timer":
            pytest.skip("Incorrect clear_timer API request")
        # Get method name and kwargs from method fixture
        method_name = method[0]
        if len(method) == 2 and isinstance(method[1], dict):
            method_kwargs = method[1]
        else:
            method_kwargs = {}

        # Set return value for call_api based on call_json_fans.METHOD_RESPONSES
        method_response = call_json_purifiers.METHOD_RESPONSES[setup_entry][method_name]
        if callable(method_response):
            if method_kwargs:
                return_dict = method_response(method_kwargs)
            else:
                return_dict = method_response()
        else:
            return_dict = method_response
        self.mock_api.return_value = (return_dict, 200)

        # Get device configuration from call_json.DeviceList.device_list_item()
        fan_obj = self.get_device("air_purifiers", setup_entry)
        assert isinstance(fan_obj, VeSyncPurifier)

        # Get method from device object
        method_call = getattr(fan_obj, method_name)

        # Ensure method runs based on device configuration
        if method_name == "turn_on":
            fan_obj.state.device_status = const.DeviceStatus.OFF
        elif method_name == "turn_off":
            fan_obj.state.device_status = const.DeviceStatus.ON
        elif method_name == "set_fan_speed":
            fan_obj.state.mode = const.PurifierModes.MANUAL
        elif method_name in ["set_auto_mode", "set_sleep_mode", "set_pet_mode", "set_turbo_mode"]:
            fan_obj.state.mode = const.PurifierModes.MANUAL
        elif method_name == "set_manual_mode":
            fan_obj.state.mode = const.PurifierModes.AUTO
        elif method_name in ["turn_on_display"]:
            fan_obj.state.display_set_status = const.DeviceStatus.OFF
        elif method_name in ["turn_off_display"]:
            fan_obj.state.display_set_status = const.DeviceStatus.ON

        # Call method with kwargs if defined
        if method_kwargs:
            self.run_in_loop(method_call, **method_kwargs)
        else:
            self.run_in_loop(method_call)

        if method_name == "turn_on":
            assert fan_obj.state.device_status == const.DeviceStatus.ON
        elif method_name == "turn_off":
            assert fan_obj.state.device_status == const.DeviceStatus.OFF
        elif method_name == "set_fan_speed":
            assert fan_obj.state.fan_level == method_kwargs["speed"]
        elif method_name in ["set_auto_mode"]:
            assert fan_obj.state.mode == const.PurifierModes.AUTO
        elif method_name in ["set_sleep_mode"]:
            assert fan_obj.state.mode == const.PurifierModes.SLEEP
        elif method_name in ["set_pet_mode"]:
            assert fan_obj.state.mode == const.PurifierModes.PET
        elif method_name in ["set_turbo_mode"]:
            assert fan_obj.state.mode == const.PurifierModes.TURBO
        elif method_name in ["turn_on_display"]:
            assert fan_obj.state.display_set_status == const.DeviceStatus.ON
        elif method_name in ["turn_off_display"]:
            assert fan_obj.state.display_set_status == const.DeviceStatus.OFF

        # Parse arguments from mock_api call into a dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recorded request or write new records
        assert assert_test(
            method_call, all_kwargs, setup_entry, self.write_api, self.overwrite
        )
