import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo
from typing import Callable, Dict, List

from .convertjob import ConvertJob
from .notegen import IBWNoteGenerator


class JobList(ttk.Treeview):
    COLUMN_NAMES = ('src_file', 'detector_name', 'shape',
                    'date', 'out_name')
    COLUMN_TEXTS = {'src_file': "Source file", 'detector_name': "Detector",
                    'shape': "Array size", 'date': "Acquisition date",
                    'out_name': "Output name"}
    COLUMN_WIDTH = {'src_file': 400, 'detector_name': 100,
                    'shape': 120, 'date': 120, 'out_name': 150}
    STRETCHABLE_COLUMN = 'src_file'
    DATETIME_FMT = "%Y/%m/%d %H:%M"

    def __init__(self, master: tk.Misc, jobs: List[ConvertJob],
                 select_cmd: Callable[[ConvertJob], None], *args, **kwargs):
        """Treeview which displays convert jobs

        Args:
            master (tk.Misc): container of this widget
            jobs (List[ConvertJob]): reference to list of jobs
            select_cmd (Callable[[ConvertJob], None]):
                command run on select item
        """
        kwargs['master'] = master
        super().__init__(columns=self.COLUMN_NAMES, selectmode=tk.BROWSE,
                         show='headings', *args, **kwargs)
        self.bind('<<TreeviewSelect>>', self.__handle_item_select)
        self.bind('<Double-Button-1>', self.__handle_doubleclick)

        # variables
        self.jobs = jobs
        self.select_cmd = select_cmd
        self.jobs_dict: Dict[str, ConvertJob] = {}

        self.__layout_columns()
        self.update_contents()

    def __layout_columns(self) -> None:
        for column in self.COLUMN_NAMES:
            self.heading(column, text=self.COLUMN_TEXTS[column])
            self.column(
                column, width=self.COLUMN_WIDTH[column], stretch=False)
        self.column(   # let one column stretchable
            self.STRETCHABLE_COLUMN, stretch=True)

    def update_contents(self) -> None:
        """update display"""
        self.reset_contents()

        # show contents
        self.jobs_dict.clear()
        for job in self.jobs:
            row = (job.src_path, job.selected_detector_name_with_id,
                   str(job.shape),
                   job.creation_time.strftime(
                       self.DATETIME_FMT),
                   job.output_name)
            id_ = self.insert('', tk.END, values=row)
            self.jobs_dict[id_] = job

    def reset_contents(self) -> None:
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

    def __handle_item_select(self, event: tk.Event) -> None:
        self.select_cmd(self.selected_job)

    def __handle_doubleclick(self, event: tk.Event) -> None:
        try:
            selected_job = self.selected_job
        except IndexError:
            return  # if job is not selected
        note_gen = IBWNoteGenerator(selected_job.smd_data)
        note_gen.set_detector_id(selected_job.selected_detector)
        note = note_gen.generate()

        showinfo(title="Information", message=note)
