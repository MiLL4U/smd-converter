import datetime
import os
from typing import Tuple
from .convertjob import ConvertJob
from .appsettings import ApplicationSettings

DEFAULT_NAME_FMT = "wave{}"


class IBWNameFormatter:
    def __init__(self, job: ConvertJob, settings: ApplicationSettings,
                 print_warning: bool = True) -> None:
        self.__job = job
        self.__settings = settings
        self.__print_warning = print_warning

    @property
    def job(self) -> ConvertJob:
        return self.__job

    @property
    def settings(self) -> ApplicationSettings:
        return self.__settings

    @property
    def print_warning(self) -> bool:
        return self.__print_warning

    def updatesettings(self, settings: ApplicationSettings) -> None:
        self.__settings = settings

    def format_original_name(self, name_fmt: str) -> str:
        org_name, _ = os.path.splitext(
            os.path.basename(self.job.src_path))
        return name_fmt.replace("%O", org_name)

    def format_acq_datetime(self, name_fmt: str) -> str:
        dt = self.job.creation_time
        return datetime.datetime.strftime(dt, name_fmt)

    def validate_first_character(self, name: str) -> str:
        if not name[0].isalpha():
            name = DEFAULT_NAME_FMT.format(name)
            if self.print_warning:
                print("Warning: wave name must start with an alphabet")
        return name

    def replace_space(self, name: str) -> str:
        res = name.replace(" ", "_")
        if res != name and self.print_warning:
            print("Warning: space(s) in wave name were "
                  "replaced with underscore(s)")
        return res

    def remove_invalid_chr(self, name: str) -> str:
        valid_characters = [chr_ for chr_ in name
                            if chr_.encode('utf-8').isalnum()
                            or chr_ == '_']
        res = "".join(valid_characters)
        if res != name and self.print_warning:
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
    def __init__(self, job: ConvertJob, settings: ApplicationSettings,
                 print_warning: bool = True) -> None:
        super().__init__(job, settings, print_warning)

    def get_name(self, exist_names: Tuple[str, ...] = None) -> str:
        detector_name = self.job.selected_detector_name
        try:
            name_fmt = self.settings.data_name_formats[detector_name]
            res = self.format_name(name_fmt)
        except KeyError:  # if format is not registered
            print(f"Warning: Name format for {self.job.selected_detector_name} "
                  "is not found")
            res = self.job.smd_name  # use original name of smd
        res = self.validate_name(res)
        if exist_names:
            res = self.unique_name(res, exist_names)

        return res

    def unique_name(self, name: str, exist_names: Tuple[str, ...]) -> str:
        res = name

        conflict_count = 0
        while res in exist_names:
            res = f"{name}_{conflict_count + 1}"
            conflict_count += 1
        if conflict_count != 0 and self.print_warning:
            print("Warning: got output name already exist")

        return res
