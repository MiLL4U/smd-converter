from __future__ import annotations
import datetime

from typing import Dict, List, OrderedDict, Tuple
from typing_extensions import Literal

import numpy as np
import xmltodict

SpatialAxisName = Literal['Z', 'Y', 'X']
SpectralUnit = Literal['nm', 'cm-1', 'GHz']

XML_BORDER = b'</SCANDATA>\x0d\x0a'
SPATIAL_AXES: Tuple[SpatialAxisName, ...] = ('Z', 'Y', 'X')
SPECTRAL_UNITS = ('nm', 'cm-1', 'GHz')

DTYPE = np.float32
LIGHT_C = 2.998e8  # m/s


class HeaderDict:
    """handle hierarchical structure of xml header"""

    def __init__(self, data_dict: OrderedDict) -> None:
        self.__data = data_dict

    @property
    def data(self):
        return self.__data


class SMDHeader(HeaderDict):
    """handle xml header of smd file"""

    def __init__(self, header_buffer: bytes) -> None:
        self.__buffer = header_buffer
        data_dict = xmltodict.parse(header_buffer)['SCANDATA']
        super().__init__(data_dict)

        frame_params = self.data['ScannedFrameParameters']

        self.frame_header = FrameHeader(
            frame_params['FrameHeader'])
        self.frame_options = FrameOptions(
            frame_params['FrameOptions'])
        self.stage_parameters = Stage3DParameters(
            frame_params['Stage3DParameters'])
        # self.data_calibrations = ...

        detector_num = self.frame_options.multi_detection_count
        if detector_num != 1:
            self.data_calibrations = [DataCalibration(
                frame_params['DataCalibration' + str(num)])
                for num in range(1, detector_num + 1)]
        else:
            self.data_calibrations = [DataCalibration(
                frame_params['DataCalibration'])]

    @property
    def buffer(self):
        return self.__buffer


class FrameHeader(HeaderDict):
    """handle FrameHeader data in a xml hader of smd file
    It contains information of creation date and so on.
    """

    def __init__(self, data_dict: OrderedDict) -> None:
        super().__init__(data_dict)

        self.__creation_datetime = self.__parse_creation_datetime()

    def __parse_creation_datetime(self):
        date_str = self.data['Date']
        time_str = self.data['Time']

        dt_str = f"{date_str} {time_str}"

        return datetime.datetime.strptime(dt_str, '%d/%m/%Y %H:%M:%S')

    @property
    def creation_datetime(self) -> datetime.datetime:
        return self.__creation_datetime


class FrameOptions(HeaderDict):
    """handle FrameOptions data in a xml header of smd file
    It contains information of excitation wavelength
    and the number of detectors.
    """

    def __init__(self, data_dict: OrderedDict) -> None:
        super().__init__(data_dict)

    @property
    def multi_detection_count(self) -> int:
        """
        NOTE: In xml header, MultiDetectionCount = 0 when data contains
        only a single detector. This method returns 1 in such case.
        """
        count = int(self.data['MultiDetectionCount'])
        return count if count else 1

    @property
    def excitation_wavelength(self) -> float:
        wl_str = self.data['OmuLaserWLnm']
        return float(wl_str)

    @property
    def grating_groove(self) -> int:
        groove_str = self.data['OmuGratingGroove']
        return int(groove_str)

    @property
    def central_wavelength(self) -> float:
        central_wl_str = self.data['OmuCentralWaveLengthNM']
        return float(central_wl_str)


class Stage3DParameters(HeaderDict):
    """handle Stage3DParameters data in a xml header of smd file
    It contains sizes of each spatial axis,
    and detail information of each spatial axis.
    """

    def __init__(self, data_dict: OrderedDict) -> None:
        super().__init__(data_dict)

        self.axis_names = SPATIAL_AXES

        self.axes: Dict[SpatialAxisName, StageAxisInfo] = {
            axis_name: StageAxisInfo(
                self.data['StageAxesDimentions']['Axis' + axis_name])
            # NOTE: is "dimention" misspelling of "dimension"?
            for axis_name in self.axis_names}

    @property
    def spatial_size(self) -> Tuple[int, ...]:
        return tuple(([int(self.data['AxisSize' + axis_name])
                       for axis_name in self.axis_names]))

    @property
    def spatial_scales(self) -> Dict[SpatialAxisName, Tuple[float, float]]:
        # returns {axis_name: (start, delta)}
        return {axis: (self.axes[axis].start_coordinate,
                       self.axes[axis].step_length)
                for axis in self.axes.keys()}

    @property
    def spatial_units(self) -> Dict[SpatialAxisName, str]:
        return {axis: (self.axes[axis].unit) for axis in self.axes.keys()}


class StageAxisInfo(HeaderDict):
    """handle detail information of each spatial axis.
    In smd file, spatial coordinates in real space are saved as scale * count.
    The count of start and end of ROI is AxisCountStart and AxisCountStop,
    and the interval of pixels (count) are AxisCountStep.
    """

    def __init__(self, data_dict: OrderedDict) -> None:
        super().__init__(data_dict)

    @property
    def unit(self):
        """returns unit of this spatial axis"""
        return self.data['AxisUnitName']

    @property
    def scale(self) -> float:
        """returns length in real space per one count"""
        return float(self.data['AxisScaleFloat'])

    @property
    def start_count(self) -> int:
        """returns count of start point in ROI"""
        return int(self.data['AxisCountStart'])

    @property
    def end_count(self) -> int:
        """returns count of end point in ROI"""
        return int(self.data['AxisCountStop'])

    @property
    def step_count(self) -> int:
        """returns count of each step"""
        return int(self.data['AxisCountStep'])

    @property
    def start_coordinate(self) -> float:
        """returns corrdinate of start in ROI in unit of real space"""
        return self.scale * self.start_count

    @property
    def step_length(self) -> float:
        """returns length of steps in unit of real space"""
        return self.scale * self.step_count

    @property
    def width(self) -> float:
        """returns width of ROI in unit of real space"""
        return (self.end_count - self.start_count) * self.scale


class DataCalibration(HeaderDict):
    """handle information of each detector (which may contain
    multiple channels)"""

    def __init__(self, data_dict: OrderedDict) -> None:
        super().__init__(data_dict)

        self.channels = [ChannelInfo(
            self.data['DataDimentions']['Channel' + str(num)])
            for num in range(self.channels_num)]

    @property
    def channels_num(self) -> int:
        return int(self.data['Channels'])


class ChannelInfo(HeaderDict):
    """handle information of each channel in detector"""

    def __init__(self, data_dict: OrderedDict) -> None:
        super().__init__(data_dict)

    @property
    def device_name(self) -> str:
        return self.data['DeviceName']

    @property
    def series_num(self) -> int:
        return int(self.data['SeriesSize'])

    @property
    def size(self) -> int:
        return int(self.data['ChannelSize'])

    @property
    def unit(self) -> str:
        return self.data['ChannelAxisUnit']

    @property
    def axis_array(self) -> np.ndarray:
        array_str = self.data['ChannelAxisArray']
        return np.fromstring(array_str, sep=" ", dtype=DTYPE)

    @property
    def informations(self) -> List[str]:
        information_dict: Dict[str, str] = self.data['ChannelInfo']
        return list(information_dict.values())


class SMDParser:
    """Parser of any types of smd file

    smd files save full spectrum data as multi-dimensonal array.
    it contains Z, Y, X-axis as spatial dimension, and
    can contain dimensions of multiple detector, channel, and series.

    Structure of multi-dimensional array is:
        array[z][y][x][d][c][s][r]
    where z, y, x is index of z, y, x-axis,
    d is index of detectors, c is index of channels in each detector,
    s is index of spectra in multiple series for channel, and
    r is index of spectral axis.

    Because size of c, s, and r may different for each detector (d),
    not all data formats can be represented as NumPy array.
    """

    def __init__(self, smd_buffer: bytes) -> None:
        header_buf, body_buf = smd_buffer.split(XML_BORDER)
        header_buf = header_buf + XML_BORDER

        self.header = SMDHeader(header_buf)
        self.__body_buffer = body_buf

    @property
    def creation_datetime(self) -> datetime.datetime:
        return self.header.frame_header.creation_datetime

    @property
    def excite_nm(self) -> float:
        return self.header.frame_options.excitation_wavelength

    @property
    def grating_groove(self) -> int:
        return self.header.frame_options.grating_groove

    @property
    def central_wavelength(self) -> float:
        return self.header.frame_options.central_wavelength

    @property
    def body_buffer(self) -> bytes:
        return self.__body_buffer

    def set_body_buffer(self, buffer: bytes) -> SMDParser:
        self.__body_buffer = buffer
        return self

    @property
    def detector_count(self) -> int:
        return self.header.frame_options.multi_detection_count

    @property
    def data_calibrations(self) -> List[DataCalibration]:
        return self.header.data_calibrations

    @property
    def spatial_size(self) -> Tuple[int, ...]:
        return self.header.stage_parameters.spatial_size

    @property
    def spatial_scales(self) -> Dict[SpatialAxisName, Tuple[float, float]]:
        return self.header.stage_parameters.spatial_scales

    @property
    def spatial_axes(self) -> Dict[SpatialAxisName, np.ndarray]:
        res: Dict[SpatialAxisName, np.ndarray] = {}
        for axis, size in zip(self.spatial_scales.keys(), self.spatial_size):
            scale = self.spatial_scales[axis]
            deltas = np.arange(size) * scale[1]
            arr = scale[0] + deltas
            res[axis] = arr
        return res

    @property
    def spatial_units(self) -> Dict[SpatialAxisName, str]:
        return self.header.stage_parameters.spatial_units

    def spectral_size(self, detector_id: int, channel_id: int = 0) -> int:
        detector = self.header.data_calibrations[detector_id]
        return detector.channels[channel_id].size

    def channel_axis_array(
            self, detector_id: int, channel_id: int = 0) -> np.ndarray:
        detector = self.header.data_calibrations[detector_id]
        return detector.channels[channel_id].axis_array

    def save(self, path: str) -> None:
        buffer = self.header.buffer + self.body_buffer
        with open(path, mode='wb') as f:
            f.write(buffer)
        print(f"Saved: {path}")


class SimpledSMDParser(SMDParser):
    """Parser of smd files which have only one channel for each detector
    and only one series

    Because smd files which have multiple channel and series
    is hard to handle as NumPy array, this class defines the parser
    of smd files which have single channel and series.
    Dimensions of channel and series are ignored, and axes of all detector
    are concatenated.
    Multi-dimensional array is treated as NumPy array and its format is:
        array[z][y][x][r]
    where z, y, and x is index of z, y, and x-axis,
    and r is index of spectral axis (concatenated).
    """

    def __init__(self, smd_buffer: bytes) -> None:
        super().__init__(smd_buffer)
        self.validate()

        self.__detectors = [
            data_calibration.channels[0]
            for data_calibration in self.header.data_calibrations]
        self.__full_array = self.unpack_full_array()

    def validate(self):
        """check if data has only one channel and series"""
        for data_calibration in self.data_calibrations:
            if data_calibration.channels_num != 1:
                raise ValueError(
                    'Only one channel is available for '
                    'each detector (has {} channels)'
                    .format(data_calibration.channels_num,))
            for channel in data_calibration.channels:
                if channel.series_num != 1:
                    raise ValueError("Multiple series is not supported")

    def unpack_full_array(self) -> np.ndarray:
        """unpack 4-dimensional array from buffer"""
        arr_1d = np.frombuffer(self.body_buffer, dtype=DTYPE)
        return np.reshape(arr_1d, self.full_array_size)

    @property
    def detectors(self) -> List[ChannelInfo]:
        return self.__detectors

    @property
    def detector_sizes(self) -> Tuple[int, ...]:
        """returns tuple of spectral size for each detector"""
        return tuple(detector.size for detector in self.detectors)

    @property
    def detector_names(self) -> Tuple[str, ...]:
        """returns tuple of name of detectors"""
        return tuple(detector.device_name for detector in self.detectors)

    @property
    def full_array_size(self) -> Tuple[int, ...]:
        """returns full size of spectral data
        (spectral axes of all detectors are concatenated)"""
        return self.spatial_size + (sum(self.detector_sizes),)

    @property
    def full_array(self) -> np.ndarray:
        """getter of self.__full_array"""
        return self.__full_array

    def change_values(self, array: np.ndarray) -> SimpledSMDParser:
        """setter of spectral data
        self.__full_array and self.__body_buffer will be changed.
        """
        if array.shape != self.full_array_size:
            raise ValueError(
                "Shape of new array ({}) is different from original shape ({})"
                .format(array.shape, self.full_array_size))
        body_buf = array.tobytes(order='C')
        self.set_body_buffer(body_buf)
        self.__full_array = array
        return self

    def __validate_detector_id(self, detector_id: int) -> None:
        """check if detector_id is valid"""
        if not detector_id < self.detector_count:
            raise ValueError(f"got invalid detector ID ({detector_id})")

    def detector_array(self, detector_id: int) -> np.ndarray:
        """returns an array of 4-dimensional spectral data
        from the detector specified with detector_id"""
        self.__validate_detector_id(detector_id)

        start_idx = sum(self.detector_sizes[:detector_id])
        end_idx = start_idx + self.detector_sizes[detector_id]

        return self.full_array[:, :, :, start_idx:end_idx]

    def detector_array_size(self, detector_id: int
                            ) -> Tuple[int, ...]:
        """returns size of spectral data
        from the detector specified with detector_id"""
        return self.spatial_size + (self.detector_sizes[detector_id],)

    def spectral_axis(
            self, detector_id: int, unit: SpectralUnit = 'nm') -> np.ndarray:
        """returns an array of spectral axis from specific detector
        with specific unit. unit defaults to 'nm'.
        """
        self.__validate_detector_id(detector_id)

        wlength = self.detectors[detector_id].axis_array
        if unit == 'nm':
            res = wlength
        elif unit == 'cm-1':
            res = (1 / self.excite_nm - 1 / wlength) * 1e7
        elif unit == 'GHz':
            excite_ghz = LIGHT_C / self.excite_nm
            bril_ghz = LIGHT_C / wlength
            res = excite_ghz - bril_ghz
        else:
            raise ValueError(f"got invalid unit ({unit})")
        return res
