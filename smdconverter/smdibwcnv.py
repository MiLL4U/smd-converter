from .smdparser import SpectralUnit
from .smdparser import SimpledSMDParser
import ibwpy as ip
from ibwpy.main import BinaryWave5
import numpy as np

IBW_SPATIAL_AXIS = ('X', 'Y', 'Z')


class SimpledSMDIBWConverter:
    def __init__(self, smd_data: SimpledSMDParser) -> None:
        self.__smd_data = smd_data

    @property
    def smd_data(self) -> SimpledSMDParser:
        return self.__smd_data

    def make_body(self, name: str, detector_id: int) -> BinaryWave5:
        """generate ibw of hyperspectral image data"""
        arr = self.smd_data.detector_array(detector_id)
        arr = self.__transpose_spatial_axis(arr)
        ibw = ip.from_nparray(arr, name)

        # copy creation date from smd to ibw
        creation_date = self.smd_data.creation_datetime
        ibw.set_creation_time(creation_date)

        # set units and scales of axis
        spatial_units = self.smd_data.spatial_units
        spatial_scales = self.smd_data.spatial_scales
        for i, axis in enumerate(IBW_SPATIAL_AXIS):
            ibw.set_axis_unit(i, spatial_units[axis])
            ibw.set_axis_scale(i, *spatial_scales[axis])
        return ibw

    def make_spectral_axis(
            self, name: str,
            detector_id: int, unit: SpectralUnit) -> BinaryWave5:
        """generate ibw of spectral axis data"""
        arr = self.smd_data.spectral_axis(detector_id, unit)
        ibw = ip.from_nparray(arr, name)

        # ibw.set_data_unit(unit)
        return ibw

    def __transpose_spatial_axis(self, src: np.ndarray) -> np.ndarray:
        """transpose axis of spatial dimension from smd to ibwo format
        In smd file, order of spatial dimension is z, y, x,
        while x, y, z in ibw file.
        """
        return np.transpose(src, (2, 1, 0, 3))
