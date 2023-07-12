import pkg_resources
from typing import Any, Dict

from typing_extensions import Literal

VERSION = "1.3.2"
GITHUB_URL = "https://github.com/MiLL4U/smd-converter/releases"

# literals
Direction = Literal['Up', 'Down']

# layout options
PADDING_OPTIONS: Dict[str, Any] = {'padx': 5, 'pady': 5}

# assets
IMAGE_PATH = pkg_resources.resource_filename('smdconverter', 'image/')

# file paths
SETTINGS_JSON_PATH = "settings.json"

# columns for tree
SPECTRAL_DATA_FORMAT_COLUMNS = ('detector', 'name_fmt')
SPECTRAL_DATA_FORMAT_COLUMN_TEXTS = {
    'detector': "Detector", 'name_fmt': "Name format"}
SPECTRAL_AXIS_FORMAT_COLUMNS = ('unit', 'name_fmt')
SPECTRAL_AXIS_FORMAT_COLUMN_TEXTS = {
    'unit': "Unit", 'name_fmt': "Name format"}

# texts
FORMAT_DESCRIPTION = """Format specifiers
  [General]
    %O: original name of SMD file
  [Acquisition date]
    %Y: year (4 digits), %y: year (2 digits), %m: month, %d: day,
    %H: hour, %M: minute, %S: second"""
