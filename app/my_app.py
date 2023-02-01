# Only needed for access to command line arguments
from enum import Enum
import customtkinter as c_tk

from tkinter import RIGHT
from tkinter import LEFT

# Setup of application configuration
c_tk.set_appearance_mode("System")
c_tk.set_default_color_theme("green")


class FileHandle(Enum):
    """Differentiates save and load

    Args:
        Enum (_type_): Enum handling
    """

    SAVE = "Save"
    LOAD = "Load"


def set_frame(parent: c_tk.CTk, padding: tuple[int, int]) -> c_tk.CTkFrame:
    """Creates a frame
    Args:
        parent (c_tk.CTk): parented container
        padding (tuple[int, int]): x, y : int, int padding

    Returns:
        c_tk.CTkFrame: the frame
    """
    frame = c_tk.CTkFrame(master=parent)
    frame.pack(pady=padding[1], padx=padding[0], fill="both")
    return frame


def set_label(
    label: str, frame: c_tk.CTkFrame, padding: tuple[int, int]
) -> c_tk.CTkLabel:
    """Creates a label

    Args:
        label (str): label name
        frame (c_tk.CTkFrame): parent frame
        padding (tuple[int, int]): x, y : int, int padding

    Returns:
        c_tk.CTkLabel: the label
    """
    label = c_tk.CTkLabel(master=frame, text=label)
    label.pack(pady=padding[1], padx=padding[0], side=RIGHT)
    return label


def browse_dir(label: c_tk.CTkLabel, handle_type: FileHandle) -> str:
    """Setup browsing of directories

    Args:
        label (c_tk.CTkLabel):parent label
        type (fileHandle): type of handling of directory

    Returns:
        str: the path to the directory
    """
    m_dir = c_tk.filedialog.askdirectory()
    if len(m_dir) > 0:
        label.configure(text=f"{handle_type} directory: {m_dir}")
    return m_dir


class App(c_tk.CTk):
    """The main class of the application

    Args:
        c_tk (_type_): customTkinter application type
    """

    def __init__(self) -> None:
        super().__init__()
        self.geometry(f"{1100}x{580}")
        self.title("Dead time cleaner")

        frame_getdirs = set_frame(self, padding=(60, 20))
        label_load = set_label("Load directory", frame_getdirs, padding=(10, 10))

        def browse_load():
            browse_dir(label_load, FileHandle.LOAD.value)

        button_get_load_dir = c_tk.CTkButton(
            master=frame_getdirs,
            text="Browse Directories",
            command=browse_load,
        )
        button_get_load_dir.pack(side=LEFT)

        label_save = set_label("Save directory", frame_getdirs, padding=(10, 10))

        def browse_save():
            browse_dir(label_save, FileHandle.SAVE.value)

        button_get_save_dir = c_tk.CTkButton(
            master=frame_getdirs,
            text="Browse Directories",
            command=browse_save,
        )
        button_get_save_dir.pack(side=LEFT)

        # subframe = c_tk.CTkFrame(master=frame_getdirs)
        # subject = c_tk.CTkLabel(subframe, text="Subject")
        # subject.place(relx=0.5, rely=0.5, anchor=CENTER)
        # subframe.pack(expand=True, fill=BOTH, side=LEFT)


if __name__ == "__main__":
    app = App()
    app.mainloop()
