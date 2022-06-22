from .smdparser import ChannelInfo, SimpledSMDParser


DEFAULT_DETECTOR_ID = 0
DATETIME_FMT = "%Y/%m/%d %H:%M:%S"
HEADING_FMT = "<{}>\n"
INDENT_LV1 = "  "
ITEM_LV1_FMT = INDENT_LV1 + "{}: {}\n"


class IBWNoteGenerator:
    def __init__(self, smd_data: SimpledSMDParser) -> None:
        self.__smd_data = smd_data
        self.__detector_id: int = DEFAULT_DETECTOR_ID

    def set_detector_id(self, detector_id: int) -> None:
        """setter of ID of detector from which information is collected"""
        self.__detector_id = detector_id

    @property
    def selected_detector(self) -> ChannelInfo:
        return self.__smd_data.detectors[self.__detector_id]

    def generate(self) -> str:
        """generate note of ibw"""
        contents = [
            self.acquisition_datetime,
            self.excitation_wavelength,
            self.grating_infos,
            self.channel_infos]

        res = "\n".join(contents)
        return res

    # **following properties are contents of note**
    @property
    def acquisition_datetime(self) -> str:
        """return string of date of acquisition"""
        heading = HEADING_FMT.format("Acquisition date")

        acq_dt = self.__smd_data.creation_datetime
        content = INDENT_LV1 + acq_dt.strftime(DATETIME_FMT)

        res = heading + content + "\n"
        return res

    @property
    def excitation_wavelength(self) -> str:
        """return string of wavelength of excitation laser light"""
        heading = HEADING_FMT.format("Excitation wavelength")

        excite_wl = self.__smd_data.excite_nm
        content = INDENT_LV1 + str(excite_wl)
        res = heading + content + "\n"
        return res

    @property
    def grating_infos(self) -> str:
        """return string of informations about grating"""
        heading = HEADING_FMT.format("Grating informations")

        grating_groove = self.__smd_data.grating_groove
        item_1 = ITEM_LV1_FMT.format("Groove number", str(grating_groove))

        central_wl = self.__smd_data.central_wavelength
        item_2 = ITEM_LV1_FMT.format("Central wavelength", str(central_wl))

        content = item_1 + item_2
        res = heading + content
        return res

    @property
    def channel_infos(self) -> str:
        """Return string of informations about channel.
        Information about each channel is listed as a string
        in the xml header of smd files.
        This method returns those strings in the same order
        as they were originally listed.
        """
        heading = HEADING_FMT.format("Channel informations")

        informations = self.selected_detector.informations
        rows = [INDENT_LV1 + information for information in informations]

        content = "\n".join(rows)
        res = heading + content
        return res
