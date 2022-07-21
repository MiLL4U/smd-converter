import tkinter as tk
from tkinter import ttk
from typing import Callable, Tuple, Union

from .constants import PADDING_OPTIONS
from .okcancelbuttonarray import OKCancelButtonArray

DEFAULT_LENGTH = 30
DEFAULT_TITLE = "Edit value"


def uniformize_grids(widget: tk.Misc, on_columns: bool = True,
                     on_rows: bool = True) -> None:
    """set weight of all columns and rows to 1

    Args:
        widget (tk.Misc): widget which settings to be changed
        on_row (bool, optional): Whether to apply to rows.
                                 Defaults to True.
        on_column (bool, optional): Whether to apply to columns.
                                    Defaults to True.
    """
    columns, rows = widget.grid_size()
    if on_columns:
        for column in range(columns):
            widget.columnconfigure(column, weight=1)
    if on_rows:
        for row in range(rows):
            widget.rowconfigure(row, weight=1)


class ChangeValueDialog(tk.Toplevel):
    # dialog to change values
    def __init__(self, master: tk.Misc,
                 descriptions: Tuple[str, ...], values: Tuple[str, ...],
                 changeable_flags: Tuple[bool, ...] = None,
                 title: str = DEFAULT_TITLE, entry_length: int = DEFAULT_LENGTH,
                 empty_ok: bool = False, *args, **kwargs) -> None:
        kwargs['master'] = master
        super().__init__(*args, **kwargs)

        self.__descriptions = descriptions
        self.__values: Union[Tuple[str, ...], None] = values
        if not changeable_flags:  # if not specified, all values can be changed
            changeable_flags = tuple((True for _ in range(len(values))))
        self.__changeable_flags = changeable_flags
        self.__entry_length = entry_length
        self.__empty_ok = empty_ok  # whether to allow empty values

        self.title(title)

        # grid settings
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  # labels and entries
        self.rowconfigure(1, weight=0)  # ok and cancel buttons

        self.__create_widgets()
        self.focus()
        self.grab_set()  # make this window modal
        self.transient()  # Disable this window on the taskbar
        self.resizable(False, False)
        self.bind('<Return>', self.__handle_return_key)
        self.bind('<Escape>', self.__cancel_command)

        self.__update_widgets()

    def __create_widgets(self) -> None:
        if not self.__values:
            raise ValueError("got None as value")
        self.values_frame = ChangeValueFrame(
            master=self, descriptions=self.__descriptions, values=self.__values,
            changeable_flags=self.__changeable_flags,
            entry_length=self.__entry_length,
            entry_command=self.__update_widgets)
        self.values_frame.grid(
            column=0, row=0, sticky=tk.NSEW, **PADDING_OPTIONS)

        self.okcancel_btns = OKCancelButtonArray(
            master=self, ok_command=self.__ok_command,
            cancel_command=self.__cancel_command)
        self.okcancel_btns.disable_ok_btn()
        self.okcancel_btns.grid(
            column=0, row=1, sticky=tk.EW)

    @property
    def values(self) -> Tuple[str, ...]:
        return self.values_frame.values

    def __ok_command(self, event: tk.Event = None) -> None:
        self.__values = self.values
        self.destroy()

    def __cancel_command(self, event: tk.Event = None) -> None:
        self.__values = None
        self.destroy()

    def __handle_return_key(self, event: tk.Event = None) -> None:
        if self.validate_values():
            self.__ok_command()

    def __update_widgets(self, event: tk.Event = None) -> None:
        if self.validate_values():
            self.okcancel_btns.enable_ok_btn()
        else:
            self.okcancel_btns.disable_ok_btn()

    def validate_values(self) -> bool:  # override this to suit the purpose
        if self.__empty_ok:
            return True
        if all(self.values):  # verify velues are not empty
            return True
        else:
            return False

    def show(self) -> Union[Tuple[str, ...], None]:
        self.wm_deiconify()
        self.wait_window()
        return self.__values


class ChangeValueFrame(ttk.Frame):
    def __init__(self, master: tk.Misc,
                 descriptions: Tuple[str, ...], values: Tuple[str, ...],
                 changeable_flags: Tuple[bool, ...],
                 entry_length: int = DEFAULT_LENGTH,
                 entry_command: Callable[[tk.Event], None] = None,
                 *args, **kwargs) -> None:
        kwargs['master'] = master
        super().__init__(*args, **kwargs)
        self.__descriptions = descriptions
        self.__changeable_flags = changeable_flags
        self.__entry_length = entry_length
        self.__entry_command = entry_command  # command called on entry

        # grid settings
        self.rowconfigure(0, weight=0)  # labels
        self.rowconfigure(1, weight=1)  # entries

        # variables
        self.__vars = tuple((tk.StringVar(value=value)
                             for value in values))

        self.__create_widgets()
        uniformize_grids(self, on_columns=False, on_rows=True)

    def __create_widgets(self) -> None:
        for row, (key, var, is_changeable) in enumerate(
                zip(self.__descriptions, self.__vars, self.__changeable_flags)):
            key_label = ttk.Label(
                master=self, text=key+": ")
            key_label.grid(
                column=0, row=row, sticky=tk.EW, **PADDING_OPTIONS)

            var_entry = ttk.Entry(
                master=self, textvariable=var, width=self.__entry_length)
            state = tk.NORMAL if is_changeable else tk.DISABLED
            var_entry.configure(state=state)
            if self.__entry_command:
                var_entry.bind('<KeyRelease>', self.__entry_command)
            var_entry.grid(
                column=1, row=row, sticky=tk.EW, **PADDING_OPTIONS)

    @property
    def values(self) -> Tuple[str, ...]:
        return tuple((var.get() for var in self.__vars))
