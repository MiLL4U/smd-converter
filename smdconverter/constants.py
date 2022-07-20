from typing import Any, Dict
from typing_extensions import Literal

VERSION = "1.1.1"
GITHUB_URL = "https://github.com/MiLL4U/smd-converter/releases"

# literals
Direction = Literal['Up', 'Down']

# layout options
PADDING_OPTIONS: Dict[str, Any] = {'padx': 5, 'pady': 5}

# file paths
SETTINGS_JSON_PATH = "settings.json"

# columns for tree
SPECTRAL_DATA_FORMAT_COLUMNS = ('detector', 'name_fmt')
SPECTRAL_DATA_FORMAT_COLUMN_TEXTS = {
    'detector': "Detector", 'name_fmt': "Name format"}
SPECTRAL_AXIS_FORMAT_COLUMNS = ('unit', 'name_fmt')
SPECTRAL_AXIS_FORMAT_COLUMN_TEXTS = {
    'unit': "Unit", 'name_fmt': "Name format"}
