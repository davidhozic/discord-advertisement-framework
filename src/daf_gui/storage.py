"""
Modules contains storage container widgets.
"""
from typing import Union, Any, List
from .convert import ObjectInfo
from .utilities import gui_confirm_action

import ttkbootstrap as ttk
import tkinter as tk
import ttkbootstrap.dialogs.dialogs as tkdiag


class Text(tk.Text):
    def get(self) -> str:
        return super().get("1.0", tk.END).strip()


class ComboBoxText(ttk.Frame):
    def __init__(self, text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ttk.Label(self, text=text).pack(fill=tk.X, expand=True)
        self.combo = ComboBoxObjects(self)
        self.combo.pack(fill=tk.X, expand=True)


class ListBoxObjects(tk.Listbox):
    class NoClipBoard:
        pass

    clipboard = NoClipBoard  # Clipboard is common to all listboxes

    def __init__(self, *args, **kwargs):
        self._original_items = []
        super().__init__(*args, **kwargs)
        self.configure(selectmode=tk.EXTENDED)

        self.bind("<Control-c>", lambda e: self.save_to_clipboard())
        self.bind("<BackSpace>", lambda e: self.delete_selected())
        self.bind("<Delete>", lambda e: self.delete_selected())
        self.bind("<Control-v>", lambda e: self.paste_from_clipboard())

    def current(self) -> int:
        "Returns index of the first currently selected element or -1 if none selected."
        selection = self.curselection()
        return selection[0] if len(selection) else -1

    def get(self, first: int = 0, last: int = None) -> list:
        slice_range = slice(first, last)
        return self._original_items[slice_range]

    def insert(self, index: Union[str, int], *elements: Union[str, float]) -> None:
        _ret = super().insert(index, *elements)
        if isinstance(index, str):
            index = len(self._original_items) if index == "end" else 0

        old_data = self._original_items[index:]
        self._original_items[index:] = list(elements) + old_data

        return _ret

    def delete(self, *indexes: int) -> None:
        def create_ranges() -> List[tuple]:
            start_i = indexes[0]
            len_indexes = len(indexes)
            for i in range(1, len_indexes):
                if indexes[i] > indexes[i - 1] + 1:  # Current index more than 1 bigger than previous
                    to_yield = start_i, indexes[i - 1]
                    yield to_yield

                    # After element is erased, all items' indexes get shifted to the left
                    # from the deleted item forward (right) -> Need to shift our list of indexes also.
                    for j in range(i, len_indexes):
                        indexes[j] -= (to_yield[1] - to_yield[0] + 1)

                    start_i = indexes[i]

            yield start_i, indexes[-1]

        if indexes[-1] == "end":
            indexes = range(indexes[0], len(self._original_items))

        indexes = list(indexes)
        for range_ in create_ranges():
            super().delete(*range_)
            del self._original_items[range_[0]:range_[1] + 1]

    def count(self) -> int:
        return len(self._original_items)

    @gui_confirm_action(True)
    def delete_selected(self):
        sel: List[int] = self.curselection()
        if len(sel):
            self.delete(*sel)
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!", parent=self)

    def clear(self) -> None:
        super().delete(0, tk.END)
        self._original_items.clear()

    def save_to_clipboard(self):
        selection = self.curselection()
        if len(selection):
            object_: Union[ObjectInfo, Any] = self.get()[min(selection):max(selection) + 1]
            ListBoxObjects.clipboard = object_
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!", parent=self)

    def paste_from_clipboard(self):
        if ListBoxObjects.clipboard is self.NoClipBoard:
            return  # Clipboard empty

        self.insert(tk.END, *ListBoxObjects.clipboard)

    def move(self, index: int, direction: int):
        if direction == -1 and index == 0 or direction == 1 and index == len(self._original_items) - 1:
            return

        value = self._original_items[index]
        self.delete(index)
        index += direction
        self.insert(index, value)
        self.selection_set(index)

    def move_selection(self, direction: int):
        """
        Moves the selected element up inside the listbox.
        """
        if len(selection := self.curselection()) == 1:
            self.move(selection[0], direction)
        else:
            tkdiag.Messagebox.show_error("Select ONE item!", "Selection error", parent=self)


class ListBoxScrolled(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent)
        listbox = ListBoxObjects(self, *args, **kwargs)
        self.listbox = listbox

        listbox.pack(side="left", fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)
        scrollbar.config(command=listbox.yview)

        listbox.config(yscrollcommand=scrollbar.set)

    def __getattr__(self, name: str):
        """
        Getter method that only get's called if the current
        implementation does not have the requested attribute.
        """
        return getattr(self.listbox, name)


class ComboBoxObjects(ttk.Combobox):
    def __init__(self, *args, **kwargs):
        self._original_items = []
        super().__init__(*args, **kwargs)

    def get(self, *args, **kwargs) -> Any:
        index = self.current()
        if isinstance(index, int) and index >= 0:
            return self._original_items[index]

        return super().get(*args, **kwargs)

    def delete(self, index: int) -> None:
        self["values"].pop(index)
        super().delete(index)
        self["values"] = self["values"]  # Update the text list, NOT a code mistake

    def insert(self, index: Union[int, str], element: Any) -> None:
        if index == tk.END:
            self._original_items.append(element)
        else:
            self._original_items.insert(index, element)

        self["values"] = self._original_items

    def count(self) -> int:
        "Returns number of elements inside the ComboBox"
        return len(self._original_items)

    def __setitem__(self, key: str, value) -> None:
        if key == "values":
            self._original_items = list(value)
            value = [str(x)[:200] for x in value]

        return super().__setitem__(key, value)

    def __getitem__(self, key: str):
        if key == "values":
            return self._original_items

        return super().__getitem__(key)


class ComboEditFrame(ttk.Frame):
    def __init__(
        self,
        edit_method: Any,
        values: List[ObjectInfo] = [],
        master=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, master=master, **kwargs)
        combo = ComboBoxObjects(self)
        ttk.Button(self, text="Edit", command=self._edit).pack(side="right")
        combo.pack(side="left", fill=tk.X, expand=True)
        self.combo = combo
        self.edit_method = edit_method
        self.set_values(values)

    def set_values(self, values: List[ObjectInfo] = []):
        self.combo["values"] = values
        self.combo.current(0)

    def _edit(self):
        selection = self.combo.current()
        if selection >= 0:
            object_: ObjectInfo = self.combo.get()
            self.edit_method(
                object_.class_,
                self.combo,
                old_data=object_,
            )
        else:
            tkdiag.Messagebox.show_error("Select atleast one item!", "Empty list!")
