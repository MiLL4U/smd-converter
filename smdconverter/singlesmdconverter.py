from __future__ import annotations

import os
import re
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import (askdirectory, askopenfilenames,
                                asksaveasfilename)
from tkinter.messagebox import askyesno, showerror, showinfo
from typing import Any, Callable, Dict, List, Tuple, Union

import tkinterdnd2 as tkdnd
from ibwpy.main import BinaryWaveHeader5
from typing_extensions import Literal

from .smdparser import SPECTRAL_UNITS
from .convertjob import ConvertJob

VERSION = "1.2.0"
ROOT_TITLE = "SMD Converter"
GITHUB_URL = "https://github.com/MiLL4U/smd-converter/releases"
LAUNCH_MSG = f"{ROOT_TITLE} {VERSION}\n" + \
    "Latest release is available at:\n  " + GITHUB_URL + "\n"

FILE_TYPES = (
    ("SMD spectral data", '*.smd'),
    ("All files", '*.*'))
DEFAULT_NAME_FMT = "wave{}"
DATETIME_FMT = "%Y/%m/%d %H:%M"

# layout options
PADDING_OPTIONS = {'padx': 5, 'pady': 5}
SCRLBAR_COLUMN = 1  # column which contains scroll bar in main window

# operation button array
OPERATION_BUTTON_TEXTS = {'open': "Open...", 'remove': "Remove",
                          'clear': "Clear", 'convert': "Convert",
                          'settings': "Settings...", 'exit': "Exit"}

# settings of column in JobList
JOBLIST_COLUMNS = ('src_file', 'detector_name', 'shape',
                   'date', 'out_name')
JOBLIST_COLUMN_TEXTS = {'src_file': "Source file", 'detector_name': "Detector",
                        'shape': "Array size", 'date': "Acquisition date",
                        'out_name': "Output name"}
JOBLIST_COLUMN_WIDTH = {'src_file': 400, 'detector_name': 100,
                        'shape': 120, 'date': 120, 'out_name': 150}
JOBLIST_STRETCHABLE_COLUMN = 'src_file'

# output options
DEFAULT_SPECTRAL_AXIS_NAMES = {'nm': "Wavelength", 'cm-1': "RamanShift",
                               'GHz': "BrillouinShift"}

Direction = Literal['Up', 'Down']


def uniformize_grids(widget: tk.Misc):
    """set weight of all columns and rows to 1

    Args:
        master (tk.Misc): widget which settings to be changed
    """
    columns, rows = widget.grid_size()
    for column in range(columns):
        widget.columnconfigure(column, weight=1)
    for row in range(rows):
        widget.rowconfigure(row, weight=1)


class OperationButtonArray(ttk.Frame):
    def __init__(self, master: tk.Misc, commands: Dict[str, Callable],
                 command_texts: Dict[str, str], *args, **kwargs) -> None:
        """Frame which contain buttons for main operations

        Args:
            master (tk.Misc): container of this widget
            commmands (Dict[str, Any]): names of commands and
                                        functions called with buttons
            command_texts (Dict[str, str]): button text for each command
        """
        kwargs['master'] = master
        super().__init__(*args, **kwargs)
        self.__commands = commands
        self.__command_texts = command_texts

        self.__create_buttons()

    def __create_buttons(self):
        """create button for each command"""
        self.__buttons: Dict[str, ttk.Button] = {}
        for i, cmd_name in enumerate(self.__commands.keys()):
            button = ttk.Button(
                self, text=self.__command_texts[cmd_name],
                command=self.__commands[cmd_name])
            self.__buttons[cmd_name] = button
            button.grid(row=0, column=i, padx=5)

    def enable(self, cmd_name: str) -> None:
        self.__buttons[cmd_name].configure(state=tk.NORMAL)

    def disable(self, cmd_name: str) -> None:
        self.__buttons[cmd_name].configure(state=tk.DISABLED)


class JobList(ttk.Treeview):
    def __init__(self, master: tk.Misc, jobs: List[ConvertJob],
                 select_cmd: Any, *args, **kwargs):
        """Treeview which displays convert jobs

        Args:
            master (tk.Misc): container of this widget
            jobs (List[ConvertJob]): reference to list of jobs
            select_cmd (Any): command run on select item
        """
        kwargs['master'] = master
        super().__init__(columns=JOBLIST_COLUMNS, selectmode=tk.BROWSE,
                         show='headings', *args, **kwargs)
        self.bind('<<TreeviewSelect>>', self.handle_item_select)

        # variables
        self.jobs = jobs
        self.select_cmd = select_cmd
        self.jobs_dict: Dict[str, ConvertJob] = {}

        self.__layout_columns()
        self.update_contents()

    def __layout_columns(self):
        for column in JOBLIST_COLUMNS:
            self.heading(column, text=JOBLIST_COLUMN_TEXTS[column])
            self.column(
                column, width=JOBLIST_COLUMN_WIDTH[column], stretch=False)
        self.column(   # let one column stretchable
            JOBLIST_STRETCHABLE_COLUMN, stretch=True)

    def update_contents(self):
        """update display"""
        self.reset_contents()

        # show contents
        self.jobs_dict.clear()
        for job in self.jobs:
            row = (job.src_path, job.selected_detector_name_with_id,
                   str(job.shape), job.creation_time.strftime(DATETIME_FMT),
                   job.output_name)
            id_ = self.insert('', tk.END, values=row)
            self.jobs_dict[id_] = job

    def reset_contents(self):
        self.delete(*self.get_children())

    @property
    def selected_job(self) -> ConvertJob:
        selected_id = self.selection()[0]
        return self.jobs_dict[selected_id]

    def select_job(self, job: ConvertJob) -> None:
        self.selection_remove(self.selection())
        item_id_idx = list(self.jobs_dict.values()).index(job)
        item_id = list(self.jobs_dict.keys())[item_id_idx]
        self.selection_add(item_id)

    def handle_item_select(self, event) -> None:
        self.select_cmd(self.selected_job)


class OutputOptionsFrame(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, cmd_on_update: Any,
                 dst_var: tk.StringVar, seek_cmd: Any,
                 *args, **kwargs) -> None:
        kwargs['master'] = master
        super().__init__(text="Options", *args, **kwargs)

        # variables
        self.current_job: ConvertJob = None
        self.cmd_on_update = cmd_on_update

        # tk variables
        self.dst_var = dst_var
        self.seek_cmd = seek_cmd
        self.selected_detector = tk.StringVar()
        self.output_name = tk.StringVar()
        self.selected_unit = tk.StringVar(value=SPECTRAL_UNITS[0])
        self.spaxis_region_text = tk.StringVar()
        self.sp_outname = tk.StringVar()

        self.__create_widgets()
        self.disable_widgets()

    def __create_widgets(self):
        self.__create_row0()
        self.__create_row1()

    def __create_row0(self):
        row = 0
        # Combobox to select detector
        detector_label = ttk.Label(self, text="Detector:")
        detector_label.grid(row=row, column=0, sticky=tk.E, **PADDING_OPTIONS)
        self.detector_cb = ttk.Combobox(
            self, state='readonly', width=25,
            textvariable=self.selected_detector)
        self.detector_cb.bind('<<ComboboxSelected>>',
                              self.handle_detector_select)
        self.detector_cb.grid(row=row, column=1, columnspan=2,
                              sticky=tk.EW, **PADDING_OPTIONS)

        # Entry to set output name
        outname_label = ttk.Label(self, text="→ Output name:")
        outname_label.grid(row=row, column=3, sticky=tk.E, **PADDING_OPTIONS)
        self.outname_entry = ttk.Entry(
            self, textvariable=self.output_name)
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
            row=row, column=4, sticky=tk.E, **PADDING_OPTIONS)

    def __create_row1(self):
        row = 1
        # label to display max and min of spectral axis
        spaxis_label = ttk.Label(self, text="Spectral axis:")
        spaxis_label.grid(row=row, column=0, sticky=tk.E, **PADDING_OPTIONS)
        self.spaxis_region_label = ttk.Label(
            self, textvariable=self.spaxis_region_text)
        self.spaxis_region_label.grid(
            row=row, column=1, sticky=tk.E, **PADDING_OPTIONS)

        # Combobox to select unit of spectral axis
        self.unit_cb = ttk.Combobox(self, values=SPECTRAL_UNITS,
                                    textvariable=self.selected_unit,
                                    state='readonly', width=5)
        self.unit_cb.bind('<<ComboboxSelected>>', self.handle_unit_select)
        self.unit_cb.grid(row=row, column=2, sticky=tk.E, **PADDING_OPTIONS)

        # Entry to set output name of spectral axis
        sp_outname_label = ttk.Label(self, text="→ Save as ibw:")
        sp_outname_label.grid(
            row=row, column=3, sticky=tk.W, **PADDING_OPTIONS)
        self.sp_outname_entry = ttk.Entry(self, textvariable=self.sp_outname)
        self.sp_outname_entry.grid(
            row=row, column=4, sticky=tk.E, **PADDING_OPTIONS)

        # Button to save spectral axis wave
        self.sp_save_btn = ttk.Button(
            self, text="Save", command=self.handle_spsave_btn)
        self.sp_save_btn.grid(
            row=row, column=5, sticky=tk.W, **PADDING_OPTIONS)

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

    def update_target_job(self, job: ConvertJob):
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

    def handle_detector_select(self, event) -> None:
        detector_id = int(self.selected_detector.get().split(':')[0])
        self.current_job.select_detector(detector_id)
        self.update_spaxis_region()

        self.cmd_on_update()

    def handle_outname_enter(self, event: tk.Event) -> None:
        if event.keysym == 'Up' or event.keysym == 'Down':
            return
        self.current_job.output_name = self.output_name.get()
        self.cmd_on_update()

    def handle_outname_arrow(self, direction: Direction):
        self.seek_cmd(direction)

    def update_spaxis_region(self) -> None:
        if self.current_job:
            unit = self.selected_unit.get()
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

                self.unit_cb.configure(state='readonly')
                self.sp_outname_entry.configure(state=tk.NORMAL)
                self.sp_save_btn.configure(state=tk.NORMAL)

    def handle_unit_select(self, *args):
        self.update_spaxis_region()

    def handle_spsave_btn(self):
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
        if dst_path:
            ibw = self.current_job.spectra_axis_ibw(
                unit=self.selected_unit.get(), name=self.sp_outname.get())
            ibw.save(dst_path)
            print(f"Saved: {dst_path}")


class DestinationSelector(ttk.Frame):
    def __init__(self, master: tk.Misc, dst_var: tk.StringVar,
                 *args, **kwargs):
        kwargs['master'] = master
        super().__init__(*args, **kwargs)

        # variables
        self.__dst_dir = dst_var

        # grid configures
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)

        self.__create_widgets()

    def __create_widgets(self):
        label = ttk.Label(self, text="Save to:")
        label.grid(row=0, column=0, sticky=tk.E, padx=5)

        self.dst_entry = ttk.Entry(
            self, textvariable=self.__dst_dir)
        self.dst_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)

        self.browse_btn = ttk.Button(
            self, text="Browse...", command=self.__handle_browsebtn,
            # state=tk.DISABLED
        )
        self.browse_btn.grid(row=0, column=2, sticky=tk.W, padx=5)

    def __handle_browsebtn(self):
        dst = askdirectory()
        if dst:
            self.__dst_dir.set(os.path.abspath(dst) + "/")

    def get(self) -> str:
        return self.__dst_dir.get()

    def reset(self):
        self.__dst_dir.set("")
        # self.browse_btn.configure(state=tk.DISABLED)


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
        self.job_list.grid(row=1, column=0, sticky=tk.NSEW, **PADDING_OPTIONS)

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
        print("test")

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
