import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import showerror
from typing import Callable, Union, cast

from ibwpy import BinaryWaveHeader5

from .appsettings import ApplicationSettings
from .constants import PADDING_OPTIONS, Direction
from .convertjob import ConvertJob
from .nameformatter import (SpectralAxisIBWNameFormatter,
                            SpectralDataIBWNameFormatter)
from .smdparser import SPECTRAL_UNITS, SpectralUnit

DEFAULT_SPECTRAL_AXIS_NAMES = {'nm': "Wavelength", 'cm-1': "RamanShift",
                               'GHz': "BrillouinShift"}

ENTRY_WIDTH = 30


class OutputOptionsFrame(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, cmd_on_update: Callable[[], None],
                 dst_var: tk.StringVar, seek_cmd: Callable[[Direction], None],
                 settings: ApplicationSettings,
                 *args, **kwargs) -> None:
        kwargs['master'] = master
        super().__init__(text="Options", *args, **kwargs)

        # variables
        self.current_job: Union[ConvertJob, None] = None
        self.cmd_on_update = cmd_on_update

        # tk variables
        self.dst_var = dst_var
        self.seek_cmd = seek_cmd
        self.__settings = settings
        self.selected_detector = tk.StringVar()
        self.output_name = tk.StringVar()
        self.selected_unit = tk.StringVar(value=SPECTRAL_UNITS[0])
        self.spaxis_region_text = tk.StringVar()
        self.sp_outname = tk.StringVar()

        self.__create_widgets()
        self.disable_widgets()

    def __create_widgets(self) -> None:
        self.__create_row0()
        self.__create_row1()

    def __create_row0(self) -> None:
        row = 0
        # Combobox to select detector
        detector_label = ttk.Label(self, text="Detector:")
        detector_label.grid(column=0, row=row, sticky=tk.E,
                            **PADDING_OPTIONS)
        self.detector_cb = ttk.Combobox(
            self, state='readonly', width=25,
            textvariable=self.selected_detector)
        self.detector_cb.bind('<<ComboboxSelected>>',
                              self.handle_detector_select)
        self.detector_cb.grid(column=1, columnspan=2, row=row,
                              sticky=tk.EW, **PADDING_OPTIONS)

        # Entry to set output name
        outname_label = ttk.Label(self, text="??? Output name:")
        outname_label.grid(column=3, row=row, sticky=tk.E,
                           **PADDING_OPTIONS)
        self.outname_entry = ttk.Entry(
            self, textvariable=self.output_name,
            width=ENTRY_WIDTH)
        self.outname_entry.bind('<KeyRelease>', self.handle_outname_enter)
        self.outname_entry.bind(
            sequence='<KeyPress-Up>',
            func=lambda event: self.handle_outname_arrow('Up'),
            add='+')
        self.outname_entry.bind(
            sequence='<KeyPress-Down>',
            func=lambda event: self.handle_outname_arrow('Down'),
            add='+')
        self.outname_entry.grid(
            column=4, row=row, sticky=tk.E, **PADDING_OPTIONS)

    def __create_row1(self) -> None:
        row = 1
        # label to display max and min of spectral axis
        spaxis_label = ttk.Label(self, text="Spectral axis:")
        spaxis_label.grid(column=0, row=row, sticky=tk.E,
                          **PADDING_OPTIONS)
        self.spaxis_region_label = ttk.Label(
            self, textvariable=self.spaxis_region_text)
        self.spaxis_region_label.grid(
            column=1, row=row, sticky=tk.E, **PADDING_OPTIONS)

        # Combobox to select unit of spectral axis
        self.unit_cb = ttk.Combobox(self, values=SPECTRAL_UNITS,
                                    textvariable=self.selected_unit,
                                    state='readonly', width=5)
        self.unit_cb.bind('<<ComboboxSelected>>', self.handle_unit_select)
        self.unit_cb.grid(column=2, row=row, sticky=tk.E,
                          **PADDING_OPTIONS)

        # Entry to set output name of spectral axis
        sp_outname_label = ttk.Label(self, text="??? Save as ibw:")
        sp_outname_label.grid(
            column=3, row=row, sticky=tk.W, **PADDING_OPTIONS)
        self.sp_outname_entry = ttk.Entry(
            self, textvariable=self.sp_outname, width=ENTRY_WIDTH)
        self.sp_outname_entry.grid(
            column=4, row=row, sticky=tk.E, **PADDING_OPTIONS)

        # Button to save spectral axis wave
        self.sp_save_btn = ttk.Button(
            self, text="Save", command=self.handle_spsave_btn)
        self.sp_save_btn.grid(
            column=5, row=row, sticky=tk.W, **PADDING_OPTIONS)

    def disable_widgets(self) -> None:  # when job is not selected
        self.selected_detector.set("")
        self.detector_cb.configure(state=tk.DISABLED)
        self.output_name.set("")
        self.outname_entry.configure(state=tk.DISABLED)

        self.spaxis_region_text.set("<<select input>>")
        self.unit_cb.configure(state=tk.DISABLED)
        self.sp_outname.set("")
        self.sp_outname_entry.configure(state=tk.DISABLED)
        self.sp_save_btn.configure(state=tk.DISABLED)

    def update_target_job(self, job: ConvertJob) -> None:
        """get information from ConvertJob and enable widgets
        """
        # detector
        self.current_job = job
        self.detector_cb.configure(
            values=job.detector_names_with_id, state='readonly')
        self.selected_detector.set(job.selected_detector_name_with_id)

        # output name
        self.output_name.set(job.output_name)
        self.outname_entry.configure(state=tk.NORMAL)

        # spectral axis
        self.update_spaxis_region()  # widgets are enabled in this method

    def handle_detector_select(self, event: tk.Event) -> None:
        detector_id = int(self.selected_detector.get().split(':')[0])
        if isinstance(self.current_job, ConvertJob):
            self.current_job.select_detector(detector_id)
            self.update_spaxis_region()
            name_formatter = SpectralDataIBWNameFormatter(
                job=self.current_job, settings=self.__settings)
            self.current_job.output_name = name_formatter.get_name()

            self.cmd_on_update()

    def handle_outname_enter(self, event: tk.Event) -> None:
        if event.keysym == 'Up' or event.keysym == 'Down':
            return
        if isinstance(self.current_job, ConvertJob):
            self.current_job.output_name = self.output_name.get()
            self.cmd_on_update()

    def handle_outname_arrow(self, direction: Direction) -> None:
        self.seek_cmd(direction)

    def update_spaxis_region(self) -> None:
        if self.current_job:
            unit = self.selected_unit.get()
            unit = cast(SpectralUnit, unit)
            if self.current_job.shape[3] == 1:
                # if detector doesn't have spectral axis
                self.spaxis_region_text.set("<<no axis data>>")
                self.unit_cb.configure(state=tk.DISABLED)
                self.sp_outname.set("")
                self.sp_outname_entry.configure(state=tk.DISABLED)
                self.sp_save_btn.configure(state=tk.DISABLED)
            else:
                arr = self.current_job.spectral_axis_array(unit)
                self.spaxis_region_text.set(f"{arr[0]:.1f} ~ {arr[-1]:.1f}")
                self.sp_outname.set(DEFAULT_SPECTRAL_AXIS_NAMES[unit])

                name_formatter = SpectralAxisIBWNameFormatter(
                    job=self.current_job, settings=self.__settings)
                self.sp_outname.set(name_formatter.get_name(unit))

                self.unit_cb.configure(state='readonly')
                self.sp_outname_entry.configure(state=tk.NORMAL)
                self.sp_save_btn.configure(state=tk.NORMAL)

    def handle_unit_select(self, *args) -> None:
        self.update_spaxis_region()

    def handle_spsave_btn(self) -> None:
        try:
            BinaryWaveHeader5.is_valid_name(self.sp_outname.get())
        except ValueError as error:
            showerror(title="Error", message=f"Invalid name: {error}")
            return

        dst_path = asksaveasfilename(
            initialdir=self.dst_var.get(),
            filetypes=(("Igor Binary Wave", '*.ibw'),
                       ("All files", '*.*')),
            initialfile=f"{self.sp_outname.get()}.ibw")
        if dst_path and isinstance(self.current_job, ConvertJob):
            unit = cast(SpectralUnit, self.selected_unit.get())
            ibw = self.current_job.spectra_axis_ibw(
                unit=unit, name=self.sp_outname.get())
            ibw.save(dst_path)
            print(f"Saved: {dst_path}")
