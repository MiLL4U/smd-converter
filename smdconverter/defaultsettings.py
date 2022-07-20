DEFAULT_SETTINGS = {
    "general": {
        "loadMultipleDetectors": True,
        "clearJobsOnComplete": False
    },
    "dataNameFormats": {
        "HyperFine": "%O_br",
        "Andor CCD": "%O_rm",
        "Multi-channel NI-ADCmx": "%O_ni"
    },
    "spectralAxisNameFormats": {
        "nm": "Wavelength_%Y%m%d",
        "cm-1": "RamanShift_%Y%m%d",
        "GHz": "BrillouinShift_%Y%m%d"
    }
}
