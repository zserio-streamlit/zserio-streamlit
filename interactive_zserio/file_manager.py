import os
import streamlit as st

from interactive_zserio.widget import Widget

class FileManager(Widget):
    def __init__(self, name, folder, extension):
        super().__init__(name)
        self._folder = folder
        self._extension = extension
        self._selected_file = None

    def render(self):
        self._log("render")
        options = self._list_files()

        if options:
            if self._key("initial_option") in st.session_state:
                st.session_state[self._key("selected_file")] = st.session_state[self._key("initial_option")]

            options.append("Create new...")

            cols = st.columns([7, 1])
            selected_file = cols[0].selectbox("File chooser", options, key=self._key("selected_file"),
                                              on_change=self._selected_file_on_change,
                                              help="Choose file to edit.")

            cols[1].title("")
            remove_file = cols[1].button("❌ Delete", disabled=(selected_file == "Create new..."),
                                         key=self._key("delete_button"), help="Remove the selected file.")
            if remove_file:
                self._log("removing file:", selected_file)
                os.remove(os.path.join(self._folder, selected_file))
                st.experimental_rerun()

        if not options or selected_file == "Create new...":
            new_file = self._create_new_file()
            if new_file:
                st.session_state[self._key("initial_option")] = new_file
                st.experimental_rerun()

        self._log("selected_file:", selected_file)
        self._selected_file = selected_file

    @property
    def selected_file(self):
        return self._selected_file

    def _selected_file_on_change(self):
        if self._key("initial_option") in st.session_state:
            del st.session_state[self._key("initial_option")]

    def _create_new_file(self):
        self._log("about to create file")
        new_file_path = st.text_input(f"Choose *.{self._extension} file path to create",
                                      key=self._key("new_file_path"),
                                      help="Enter relative path of the file to create.")
        if not new_file_path:
            st.stop()
        if not new_file_path.endswith("." + self._extension):
            st.error("Must have *." + self._extension + " extension!")
            st.stop()

        self._log("creating file:", new_file_path)
        open(os.path.join(self._folder, new_file_path), "w").close()

        return new_file_path

    def _list_files(self):
        listed_files = []
        for root, _, files in os.walk(self._folder):
            for listed_file in files:
                if listed_file.endswith("." + self._extension):
                    listed_files.append(os.path.relpath(os.path.join(root, listed_file), self._folder))
        listed_files.sort()
        return listed_files
