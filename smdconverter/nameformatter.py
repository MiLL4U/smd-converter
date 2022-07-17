import datetime
import os
from .convertjob import ConvertJob
from smdconverter.appsettings import ApplicationSettings

DEFAULT_NAME_FMT = "wave{}"


class IBWNameFormatter:
    def __init__(self, job: ConvertJob, settings: ApplicationSettings,
                 print_warning: bool = True) -> None:
        self.__job = job
        self.__settings = settings
        self.__print_warning = print_warning

    @property
    def settings(self) -> ApplicationSettings:
        return self.__settings

    def update_settings(self, settings: ApplicationSettings):
        self.__settings = settings

    def format_original_name(self, name_fmt: str) -> str:
        org_name = os.path.splitext(self.__job.src_path)[0]
        return name_fmt.replace("%O", org_name)

    def format_acq_datetime(self, name_fmt: str) -> str:
        dt = self.__job.creation_time
        return datetime.datetime.strftime(dt, name_fmt)

    def validate_first_character(self, name: str) -> str:
        if not name[0].isalpha():
            name = DEFAULT_NAME_FMT.format(name)
            if self.__print_warning:
                print("Warning: wave name must start with an alphabet")
        return name

    def replace_space(self, name: str) -> str:
        res = name.replace(" ", "_")
        if res != name and self.__print_warning:
            print("Warning: space(s) in wave name were "
                  "replaced with underscore(s)")
        return res

    def remove_invalid_chr(self, name: str) -> str:
        valid_characters = [chr_ for chr_ in name
                            if chr_.encode('utf-8').isalnum()
                            or chr_ == '_']
        res = "".join(valid_characters)
        if res != name and self.__print_warning:
            print("Warning: all characters in name must be"
                  "alphabet, digit, or underscore")
        return res

    def format_name(self, name_fmt: str) -> str:
        res = self.format_original_name(name_fmt)  # %O
        res = self.format_acq_datetime(res)

        return res

    def validate_name(self, name: str) -> str:
        name = self.validate_first_character(name)
        name = self.replace_space(name)
        name = self.remove_invalid_chr(name)

        return name


class SpectralAxisIBWNameFormatter(IBWNameFormatter):
    def __init__(self, job: ConvertJob, settings: ApplicationSettings,
                 print_warning: bool = True) -> None:
        super().__init__(job, settings, print_warning)

    def get_name(self, unit: str) -> str:
        name_fmt = self.settings.spectral_axis_name_formats[unit]
        res = self.format_name(name_fmt)
        res = self.validate_name(res)

        return res


class SpectralDataIBWNameFormatter(IBWNameFormatter):
    def __init__(self) -> None:
        super().__init__()
    pass
