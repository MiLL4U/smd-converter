import json
from os.path import isfile
from typing import Any, Dict

from .constants import SETTINGS_JSON_PATH

from .defaultsettings import DEFAULT_SETTINGS

JSON_INDENT = 4


class ApplicationSettings:
    def __init__(self, settings_dict: Dict[str, Any], json_path: str) -> None:
        self.__settings_dict = settings_dict
        self.__json_path = json_path

    @property
    def general(self) -> Dict[str, Any]:
        return self.__settings_dict['general']

    @property
    def multi_detector_flag(self) -> bool:
        return self.general['loadMultipleDetectors']

    def set_multi_detector_flag(self, flag: bool) -> None:
        self.__settings_dict['general']['loadMultipleDetectors'] = flag

    @property
    def ibw_name_formats(self) -> Dict[str, str]:
        return self.__settings_dict['ibwNameFormats']

    def set_ibw_name_format(self, detector_name: str, format_: str) -> None:
        self.__settings_dict['ibwNameFormats'][detector_name] = format_

    @property
    def spectral_axis_name_formats(self) -> Dict[str, str]:
        return self.__settings_dict['spectralAxisNameFormats']

    def set_spectral_axis_name_format(self, unit: str, format_: str) -> None:
        self.__settings_dict['spectralAxisNameFormats'][unit] = format_

    def save(self) -> None:
        with open(self.__json_path, mode='w') as f:
            json.dump(self.__settings_dict, f, indent=JSON_INDENT)


class ApplicationSettingsHandler:
    def __init__(self, json_path: str = SETTINGS_JSON_PATH) -> None:
        self.__json_path = json_path

    def load(self) -> ApplicationSettings:
        if isfile(self.__json_path):  # check if settings file exists
            with open(self.__json_path, mode='r') as f:
                settings_dict = json.load(f)

        else:  # make settings file and load default settings
            self.save_default_settings()
            settings_dict = DEFAULT_SETTINGS

        return ApplicationSettings(settings_dict, self.__json_path)

    def save_default_settings(self) -> None:
        with open(self.__json_path, mode='w') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=JSON_INDENT)
