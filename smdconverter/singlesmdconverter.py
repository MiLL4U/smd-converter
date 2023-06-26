from __future__ import annotations

import os
import re
import tkinter as tk
from copy import deepcopy
from tkinter import ttk
from tkinter.filedialog import askopenfilenames
from tkinter.messagebox import askyesno, showerror, showinfo
from typing import Callable, Dict, List, Tuple, Union

import tkinterdnd2 as tkdnd
from ibwpy import BinaryWaveHeader5
from typing_extensions import Literal

from .appsettings import ApplicationSettingsHandler
from .constants import (GITHUB_URL, PADDING_OPTIONS, SETTINGS_JSON_PATH,
                        VERSION, Direction)
from .convertjob import ConvertJob
from .dstselector import DestinationSelector
from .joblist import JobList
from .nameformatter import SpectralDataIBWNameFormatter
from .opbtnarray import OperationButtonArray
from .outputoptionsframe import OutputOptionsFrame
from .settingwndw import SettingsWindow


class App(tkdnd.Tk):
    """Main window of SMD Converter
    """
    ROOT_TITLE = "SMD Converter"
    LAUNCH_MSG = f"{ROOT_TITLE} {VERSION}\n" + \
        "Copyright (c) 2022-2023 Hiroaki Takahashi.\n\n" + \
        "Latest release is available at:\n  " + GITHUB_URL + "\n"
    FILE_TYPES = (
        ("SMD spectral data", '*.smd'),
        ("All files", '*.*'))

    # layout options
    SCRLBAR_COLUMN = 1  # column which contains scroll bar in main window

    # operation button array
    OPERATION_BUTTON_TEXTS = {
        'open': "Open...", 'remove': "Remove",
        'clear': "Clear", 'convert': "Convert",
        'settings': "Settings...", 'exit': "Exit"}

    OPERATION_BUTTON_ICONS = {  # ./image/...
        'open': "folder_open.png", 'remove': "subtract.png",
        'clear': "loader.png", 'convert': "check.png",
        'settings': "settings.png", 'exit': "close.png"}

    OPERATION_BUTTON_ICONS_DISABLED = {
        'open': "folder_open_gray.png", 'remove': "subtract_gray.png",
        'clear': "loader_gray.png", 'convert': "check_gray.png",
        'settings': "settings_gray.png", 'exit': "close_gray.png"}

    def __init__(self) -> None:
        super().__init__()
        print(self.LAUNCH_MSG)

        self.title(f"{self.ROOT_TITLE} {VERSION}")

        # grid settings
        self.columnconfigure(0, weight=1)  # column for widgets
        # column for scroll bar
        self.columnconfigure(self.SCRLBAR_COLUMN, weight=0)

        self.rowconfigure(0, weight=0)  # operation buttons
        self.rowconfigure(1, weight=1)  # list of jobs
        self.rowconfigure(2, weight=0)  # tools for spectral axis
        self.rowconfigure(3, weight=0)  # destination selector

        # variables
        self.jobs: List[ConvertJob] = []
        self.dst_dir = tk.StringVar(value="")
        settings_handler = ApplicationSettingsHandler(
            SETTINGS_JSON_PATH)
        self.__settings = settings_handler.load()

        self.__create_widgets()
        self.update_idletasks()  # required for set minsize dynamically
        self.minsize(width=self.winfo_width(), height=self.winfo_height())

        # drug & drop
        self.drop_target_register(tkdnd.DND_FILES)
        self.dnd_bind('<<Drop>>', self.dropped)

        print("\nPlease open smd files.")

    def __create_widgets(self) -> None:
        # main operation buttons
        op_commands: Dict[str, Callable[[], None]] = {
            'open': self.open_smd, 'remove': self.remove_job,
            'clear': self.clear_jobs, 'convert': self.convert,
            'settings': self.show_settings_window,
            'exit': self.destroy}

        self.opbutton_arr = OperationButtonArray(
            self, commands=op_commands,
            command_texts=self.OPERATION_BUTTON_TEXTS,
            command_icons=self.OPERATION_BUTTON_ICONS,
            command_icons_disabled=self.OPERATION_BUTTON_ICONS_DISABLED)
        self.disable_opbuttons()
        self.opbutton_arr.grid(
            column=0, columnspan=2, row=0,
            sticky=tk.NSEW, **PADDING_OPTIONS)

        # list of jobs
        self.job_list = JobList(self, self.jobs, self.handle_select_job)
        self.job_list.grid(
            column=0, row=1, sticky=tk.NSEW, **PADDING_OPTIONS)

        # scroll bar of job list
        self.joblist_scrl = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.job_list.yview)
        self.joblist_scrl.grid(column=self.SCRLBAR_COLUMN, row=1, sticky=tk.NS)
        self.job_list.config(yscrollcommand=self.joblist_scrl.set)

        # output options
        self.outputopt_frame = OutputOptionsFrame(
            self, self.update_options, dst_var=self.dst_dir,
            seek_cmd=self.seek_job, settings=self.__settings)
        self.outputopt_frame.grid(
            column=0, columnspan=2, row=3,
            sticky=tk.NSEW, **PADDING_OPTIONS)

        # destination selector
        self.dst_selector = DestinationSelector(self, dst_var=self.dst_dir)
        self.dst_selector.grid(
            column=0, columnspan=2, row=4,
            sticky=tk.NSEW, **PADDING_OPTIONS)

    def open_smd(self) -> None:
        smd_paths = self.__ask_filenames()
        if smd_paths:
            self.__set_jobs(smd_paths)

    def __ask_filenames(self) -> Union[Tuple[str, ...], Literal['']]:
        filenames = askopenfilenames(
            title="Open files", initialdir='./',
            filetypes=self.FILE_TYPES)
        return filenames

    def clear_jobs(self) -> None:
        self.disable_opbuttons()
        self.jobs.clear()
        self.job_list.reset_contents()
        self.outputopt_frame.disable_widgets()
        self.dst_selector.reset()
        print("Information: All jobs are removed.")

    def __set_jobs(self, smd_paths: Tuple[str, ...]) -> None:
        opened = False
        for smd_path in smd_paths:
            smd_name, extension = os.path.splitext(
                os.path.basename(smd_path))
            if extension != '.smd':
                print(f"Skipped (invalid file extension): {smd_path}")
                continue

            smd_path = os.path.abspath(smd_path)
            try:  # load job with temporal name
                convert_job = ConvertJob(
                    os.path.abspath(smd_path), smd_name)
            except Exception as error:
                print(f"Skipped (illegal format): {smd_path} ({error})")
                continue

            convert_job = self.__format_output_name(convert_job)
            self.jobs.append(convert_job)
            print(f"Opened: {convert_job.output_name} "
                  f"from {convert_job.src_path}")
            opened = True

            # add multiple jobs when multiple detectors are found
            if self.__settings.multi_jobs_flag:
                self.__add_other_detectors(convert_job)

        if not opened:  # if valid file is not loaded
            return
        else:
            self.__update_widgets_on_open(smd_paths)

    def __update_widgets_on_open(self, smd_paths: Tuple[str, ...]) -> None:
        self.job_list.update_contents()
        self.opbutton_arr.enable('convert')
        self.opbutton_arr.enable('clear')
        if not self.dst_dir.get():
            self.dst_dir.set(
                os.path.abspath(os.path.dirname(smd_paths[-1])) + "/")

        # select last job which opened
        last_job = self.jobs[-1]
        self.job_list.select_job(last_job)

    def __format_output_name(self, job: ConvertJob) -> ConvertJob:
        formatter = SpectralDataIBWNameFormatter(
            job=job, settings=self.__settings)
        job.output_name = formatter.get_name(
            exist_names=self.output_names)

        return job

    def __add_other_detectors(self, convert_job: ConvertJob) -> None:
        # HACK: Depending on jobs already loaded is ineffective?
        detector_ids = convert_job.detector_ids
        for detector_id in detector_ids[1:]:
            additive_job = deepcopy(convert_job)
            additive_job.select_detector(detector_id)
            self.__format_output_name(additive_job)
            self.jobs.append(additive_job)
            print(f"Opened: {additive_job.output_name} "
                  f"from {additive_job.src_path}")

    @property
    def output_names(self) -> Tuple[str, ...]:
        return tuple(job.output_name for job in self.jobs)

    def remove_job(self) -> None:
        selected_job = self.job_list.selected_job
        selected_job_idx = self.jobs.index(selected_job)
        last_job_idx = len(self.jobs) - 1

        self.jobs.remove(selected_job)
        print(f"Removed: {selected_job.src_path}")
        self.job_list.update_contents()

        if len(self.jobs) == 0:  # if all jobs are removed
            self.disable_opbuttons()
            self.outputopt_frame.disable_widgets()
        else:  # if job(s) are remain
            next_job_idx = selected_job_idx \
                if selected_job_idx != last_job_idx else last_job_idx - 1
            next_job = self.jobs[next_job_idx]
            self.job_list.select_job(next_job)

            self.handle_select_job(self.job_list.selected_job)
        pass

    def convert(self) -> None:
        # validate all output names
        for name in self.output_names:
            try:
                BinaryWaveHeader5.is_valid_name(name)
            except ValueError as error:
                msg = "Error: Got invalid output name ({}). {}.".format(
                    name, str(error).capitalize())
                showerror("Error", message=msg)
                return

        # check name confliction
        conflicted_names = [x for x in set(self.output_names)
                            if self.output_names.count(x) > 1]
        if conflicted_names:
            msg = "Error: Duplicate output name(s) exists ({}).".format(
                ", ".join(conflicted_names))
            showerror("Error", message=msg)
            return

        # ask if overwrite
        files_and_dirs = os.listdir(self.dst_dir.get())
        files = [f for f in files_and_dirs
                 if os.path.isfile(os.path.join(self.dst_dir.get(), f))]
        exist_names = [f"{name}.ibw" for name in self.output_names
                       if f"{name}.ibw" in files]
        if exist_names:
            msg = "ibw file(s) already exists in destination ({}). " \
                  "Are you sure to overwrite?".format(
                      ", ".join(exist_names))
            ans = askyesno("Information", message=msg)
            if ans is False:
                return

        for job in self.jobs:
            job.convert(path=self.dst_dir.get())
        showinfo("Information", message="Conversion completed.")
        print("Information: Conversion completed.")

        # clear jobs if enabled in the settings
        if self.__settings.clear_jobs_flag:
            self.clear_jobs()

    def handle_select_job(self, job: ConvertJob) -> None:
        self.opbutton_arr.enable('remove')
        self.outputopt_frame.update_target_job(job)

    def seek_job(self, direction: Direction) -> None:
        cur_job_idx = self.jobs.index(self.job_list.selected_job)
        last_job_idx = len(self.jobs) - 1

        # loop index
        if direction == 'Up':
            seeked_idx = cur_job_idx - 1
            seeked_idx = last_job_idx if seeked_idx == -1 else seeked_idx
        elif direction == 'Down':
            seeked_idx = cur_job_idx + 1
            seeked_idx = 0 if seeked_idx == last_job_idx + 1 else seeked_idx
        self.job_list.select_job(self.jobs[seeked_idx])

    def update_options(self) -> None:
        # backup selection of JobList (because id changes)
        selected_job = self.job_list.selected_job

        self.job_list.update_contents()

        # restore selection
        self.job_list.select_job(selected_job)

    def show_settings_window(self) -> None:
        self.setting_window = SettingsWindow(self, self.__settings)

    def disable_opbuttons(self) -> None:
        """disable operation buttons which are available only when job(s) exist
        """
        self.opbutton_arr.disable('remove')
        self.opbutton_arr.disable('clear')
        self.opbutton_arr.disable('convert')

    def dropped(self, event: tkdnd.TkinterDnD.DnDEvent) -> None:
        """add job by drug and drop
        """
        paths_str: str = event.data
        paths_with_space: List[str] = [
            path.lstrip("{").rstrip("}")
            for path in re.findall(
                r'\{.+?\}', paths_str)]
        space_removed = re.sub(r'\{.+?\}', '', paths_str)
        paths_without_space = space_removed.split()
        paths = paths_with_space + paths_without_space
        self.__set_jobs(tuple(paths))
