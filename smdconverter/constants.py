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
