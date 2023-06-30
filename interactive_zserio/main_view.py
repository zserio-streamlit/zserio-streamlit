import os
import shutil
import streamlit as st
import zserio

from tempfile import TemporaryDirectory

from interactive_zserio.widget import Widget
from interactive_zserio.workspace import Workspace
from interactive_zserio.urlutil import URLUtil
from interactive_zserio.share_rtdb import ShareRTDB
from interactive_zserio.uploader import Uploader
from interactive_zserio.file_manager import FileManager
from interactive_zserio.editor import Editor
from interactive_zserio.generator import Generator
from interactive_zserio.sources_viewer import SourcesViewer
from interactive_zserio.python_runner import PythonRunner
from interactive_zserio.downloader import Downloader

class MainView(Widget):
    def __init__(self):
        super().__init__("main_view")

        if self._key("temp_dir") not in st.session_state:
            # TemporaryDirectory will be automatically deleted when the session is ended,
            # thus we won't spoil the temp.
            st.session_state[self._key("temp_dir")] = TemporaryDirectory(prefix="interactive_zserio_")
            self._log("created new temp directory:", st.session_state[self._key("temp_dir")])

        self._urlutil = URLUtil()
        self._workspace = Workspace(os.path.join(self._tmp_dir, "workspace"))
        self._zip_name = "workspace.zip"

        self._uploader = Uploader(self._tmp_dir, self._workspace.ws_dir, self._workspace.zs_dir)
        self._schema_file_manager = FileManager("schema_file_manager", self._workspace.zs_dir, "zs",
                                                self._new_schema_file_callback)
        self._schema_editor = Editor("schema_editor", self._workspace.zs_dir)
        self._generator = Generator(self._workspace.zs_dir, self._workspace.gen_dir)
        self._sources_viewer = SourcesViewer(self._workspace.gen_dir)

        self._python_runner = PythonRunner(os.path.join(self._workspace.gen_dir, "python"),
                                           os.path.join(self._workspace.src_dir, "python"))

        self._share = ShareRTDB(self._workspace, self._generator, self._python_runner)

        self._workspace_downloader = Downloader("workspace_downloader",
                                                self._tmp_dir, self._workspace.ws_dir, self._zip_name,
                                                label="Download workspace",
                                                help="Download whole workspace as a zip file.",
                                                exclude_extensions=["zip"])

        if self._key("schema_mode") not in st.session_state:
            # initialize on the first run or after refresh (F5)
            st.set_page_config(layout="wide", page_title="Interactive Zserio", page_icon="./img/zs.png")
            self._workspace.create()

            query_params = self._urlutil.get_url_params()
            share_id = query_params["share_id"][0] if ("share_id") in query_params else None
            if not (share_id and self._restore_share(share_id)):
                st.session_state[self._key("schema_mode")] = "sample"
                self._share.restore_sample()

    @property
    def _tmp_dir(self):
        return st.session_state[self._key("temp_dir")].name

    @property
    def _schema_mode(self):
        return st.session_state[self._key("schema_mode")]

    def render(self):
        self._log("render")

        st.write(f"""
            <h1>Interactive Zserio<sup style="top: -2em;">{zserio.VERSION_STRING}</sup> Compiler!</h1>
        """, unsafe_allow_html=True)

        schema_modes = { "write": "Write schema", "upload": "Upload schema or workspace", "sample": "Sample" }
        st.selectbox("Schema", schema_modes, format_func=lambda x: schema_modes[x],
                     key=self._key("schema_mode"), on_change=self._schema_mode_on_change)
        if self._schema_mode == "upload":
            self._uploader.render()

        self._schema_file_manager.render()

        self._schema_editor.set_file(self._schema_file_manager.selected_file)
        self._schema_editor.render()

        self._generator.set_zs_file_path(self._schema_file_manager.selected_file)
        self._generator.render()

        self._sources_viewer.set_generators(self._generator.generators)
        self._sources_viewer.render()

        self._python_runner.set_python_generated(self._generator.generators["python"])
        self._python_runner.render()

        self._workspace_downloader.render()
        share_button = st.button("Save & Share Workspace")
        if share_button:
            self._share.delete_old_shares()

            st.session_state[self._key("share_id")] = self._share.new_id()
            self._urlutil.set_url_params({"share_id": st.session_state[self._key("share_id")]})
            if self._share.share(st.session_state[self._key("share_id")]):
                st.code(self._urlutil.get_current_url() + f"?share_id={st.session_state[self._key('share_id')]}")
            else:
                del st.session_state[self._key("share_id")]
                st.warning("sharing failed, please report an issue!")

    def _new_schema_file_callback(self, folder, file_path):
        package_definition = ".".join(os.path.splitext(file_path)[0].split(os.sep))
        self._log("new schema file:", package_definition)
        with open(os.path.join(folder, file_path), "w") as new_file:
            new_file.write(f"package {package_definition};\n")

    def _schema_mode_on_change(self):
        self._generator.reset()
        self._workspace.reset()

        if st.session_state[self._key("schema_mode")] == "sample":
            self._share.restore_sample()

    def _restore_share(self, share_id):
        if self._share.restore(share_id):
            st.session_state[self._key("schema_mode")] = "write"
            st.session_state[self._key("share_id")] = share_id
            return True

        st.warning(f"Failed to restore shared workspace with share_id={share_id}")
        return False
