from __future__ import annotations

import os
import re
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilenames
from tkinter.messagebox import askyesno, showerror, showinfo
from typing import Callable, Dict, List, Tuple, Union

import tkinterdnd2 as tkdnd
from ibwpy.main import BinaryWaveHeader5

from .appsettings import ApplicationSettings
from .constants import GITHUB_URL, PADDING_OPTIONS, VERSION, Direction
from .convertjob import ConvertJob
from .dstselector import DestinationSelector
from .joblist import JobList
from .opbtnarray import OperationButtonArray
from .outputoptionsframe import OutputOptionsFrame
from .settingwndw import SettingsWindow

ROOT_TITLE = "SMD Converter"
LAUNCH_MSG = f"{ROOT_TITLE} {VERSION}\n" + \
    "Latest release is available at:\n  " + GITHUB_URL + "\n"

FILE_TYPES = (
    ("SMD spectral data", '*.smd'),
    ("All files", '*.*'))
DEFAULT_NAME_FMT = "wave{}"


# layout options
SCRLBAR_COLUMN = 1  # column which contains scroll bar in main window

# operation button array
OPERATION_BUTTON_TEXTS = {'open': "Open...", 'remove': "Remove",
                          'clear': "Clear", 'convert': "Convert",
                          'settings': "Settings...", 'exit': "Exit"}


# def uniformize_grids(widget: tk.Misc):
#     """set weight of all columns and rows to 1

#     Args:
#         master (tk.Misc): widget which settings to be changed
#     """
#     columns, rows = widget.grid_size()
#     for column in range(columns):
#         widget.columnconfigure(column, weight=1)
#     for row in range(rows):
#         widget.rowconfigure(row, weight=1)


class App(tkdnd.Tk):
    def __init__(self):
        super().__init__()

        self.title(f"{ROOT_TITLE} {VERSION}")

        # grid settings
        self.columnconfigure(0, weight=1)  # column for widgets
        self.columnconfigure(SCRLBAR_COLUMN, weight=0)  # column for scroll bar

        self.rowconfigure(0, weight=0)  # operation buttons
        self.rowconfigure(1, weight=1)  # list of jobs
        self.rowconfigure(2, weight=0)  # tools for spectral axis
        self.rowconfigure(3, weight=0)  # destination selector

        # variables
        self.jobs: List[ConvertJob] = []
        self.dst_dir = tk.StringVar(value="")
        self.__settings = ApplicationSettings()

        self.__create_widgets()
        self.update_idletasks()  # required for set minsize dynamically
        self.minsize(width=self.winfo_width(), height=self.winfo_height())

        # drug & drop
        self.drop_target_register(tkdnd.DND_FILES)
        self.dnd_bind('<<Drop>>', self.dropped)

        print(LAUNCH_MSG)
        print("Please open smd files.")

    def __create_widgets(self):
        # main operation buttons
        op_commands: Dict[str, Callable] = {
            'open': self.open_smd, 'remove': self.remove_job,
            'clear': self.clear_jobs, 'convert': self.convert,
            'settings': self.show_settings_window, 'exit': self.destroy}

        self.opbutton_arr = OperationButtonArray(
            self, commands=op_commands, command_texts=OPERATION_BUTTON_TEXTS)
        self.disable_opbuttons()
        self.opbutton_arr.grid(
            row=0, column=0, columnspan=2,
            sticky=tk.NSEW, **PADDING_OPTIONS)

        # list of jobs
        self.job_list = JobList(self, self.jobs, self.handle_select_job)
        self.job_list.grid(
            row=1, column=0, sticky=tk.NSEW, **PADDING_OPTIONS)

        # scroll bar of job list
        self.joblist_scrl = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.job_list.yview)
        self.joblist_scrl.grid(row=1, column=SCRLBAR_COLUMN, sticky=tk.NS)
        self.job_list.config(yscrollcommand=self.joblist_scrl.set)

        # output options
        self.outputopt_frame = OutputOptionsFrame(
            self, self.update_options, dst_var=self.dst_dir,
            seek_cmd=self.seek_job)
        self.outputopt_frame.grid(
            row=3, column=0, columnspan=2,
            sticky=tk.NSEW, **PADDING_OPTIONS)

        # destination selector
        self.dst_selector = DestinationSelector(self, dst_var=self.dst_dir)
        self.dst_selector.grid(
            row=4, column=0, columnspan=2,
            sticky=tk.NSEW, **PADDING_OPTIONS)

    def open_smd(self):
        file_names = self.__ask_filenames()
        if file_names:
            self.__set_jobs(file_names)

    def __ask_filenames(self) -> Union[Tuple[str], None]:
        filenames = askopenfilenames(
            title="Open files", initialdir='./',
            filetypes=FILE_TYPES)
        return filenames

    def clear_jobs(self):
        self.disable_opbuttons()
        self.jobs.clear()
        self.job_list.reset_contents()
        self.outputopt_frame.disable_widgets()
        self.dst_selector.reset()
        print("Information: All jobs are removed.")

    def __set_jobs(self, file_names: Tuple[str]):
        opened = False
        for file_name in file_names:
            wave_name, extension = os.path.splitext(
                os.path.basename(file_name))
            if extension != '.smd':
                print(f"Skipped (invalid file extension): {file_name}")
                continue
            if not wave_name[0].isalpha():  # 1st character must be an alphabet
                print("Warning: wave name must start with an alphabet")
                wave_name = DEFAULT_NAME_FMT.format(wave_name)

            # replace space to underscore and remove invalid characters
            wave_name = wave_name.replace(" ", "_")
            valid_characters = [chr_ for chr_ in wave_name
                                if chr_.encode('utf-8').isalnum()
                                or chr_ == '_']
            valid_wave_name = "".join(valid_characters)
            if valid_wave_name != wave_name:
                wave_name = valid_wave_name
                print("Warning: all characters in name must be"
                      "alphabet, digit, or underscore")

            # avoid name confliction
            exist_names = self.output_names
            alter_name = wave_name
            conflict_count = 0
            while alter_name in exist_names:
                alter_name = f"{wave_name}_{conflict_count + 1}"
                if conflict_count == 0:
                    print("Warning: got output name already exist")
                conflict_count += 1
            wave_name = alter_name

            try:
                convert_job = ConvertJob(os.path.abspath(file_name), wave_name)
            except Exception as error:
                print(f"Skipped (illegal format): {file_name} ({error})")
                continue

            self.jobs.append(convert_job)
            print("Opened:", convert_job.src_path)
            opened = True

        if not opened:  # if valid file is not loaded
            return

        # update widgets
        self.job_list.update_contents()
        self.opbutton_arr.enable('convert')
        self.opbutton_arr.enable('clear')
        if not self.dst_dir.get():
            self.dst_dir.set(
                os.path.abspath(os.path.dirname(file_names[-1])) + "/")

        # select last job which opened
        last_job = self.jobs[-1]
        self.job_list.select_job(last_job)

    @property
    def output_names(self) -> Tuple[str]:
        return tuple(job.output_name for job in self.jobs)

    def remove_job(self):
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

    def convert(self):
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

    def handle_select_job(self, job: ConvertJob):
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

    def update_options(self):
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

    def dropped(self, event: tkdnd.TkinterDnD.DnDEvent):
        """add job by drug and drop
        """
        paths_str = event.data
        paths_with_space = [path.lstrip("{").rstrip("}")
                            for path in re.findall(r'\{.+?\}', paths_str)]
        space_removed = re.sub(r'\{.+?\}', '', paths_str)
        paths_without_space = space_removed.split()
        paths = paths_with_space + paths_without_space
        self.__set_jobs(paths)
