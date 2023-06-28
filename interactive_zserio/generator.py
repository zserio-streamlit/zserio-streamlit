import os
import shutil
import streamlit as st
import zserio

from interactive_zserio.widget import Widget

class Generator(Widget):
    def __init__(self, zs_dir, gen_dir):
        super().__init__("generator")
        self._zs_dir = zs_dir
        self._gen_dir = gen_dir

        self._zs_file_path = None

    def get_state(self):
        return {"generators": self.generators, "extra_args": st.session_state[self._key("extra_args")] }

    def set_state(self, state):
        self._log("set state:", state)
        for key in state["generators"].keys():
            st.session_state[self._key("generator_" + key)] = state["generators"][key]
        if "extra_args" in state:
            st.session_state[self._key("extra_args")]= state["extra_args"]

    def set_zs_file_path(self, zs_file_path):
        self._zs_file_path = zs_file_path

    def render(self):
        self._log("render")

        st.text_input("Extra Arguments", key=self._key("extra_args"))

        generators_cols = st.columns(len(GENERATORS))
        generators_checks = []
        for i, generator in enumerate(GENERATORS):
            if self._key("generator_" + generator) not in st.session_state:
                st.session_state[self._key("generator_" + generator)] = False
            with generators_cols[i]:
                generators_checks.append(st.checkbox(generator, key=self._key("generator_" + generator)))

        if self._needs_recompilation():
            shutil.rmtree(self._gen_dir)
            os.makedirs(self._gen_dir)
            with st.spinner("Compiling..."):
                if not self._compile():
                    st.stop()
        else:
            st.info("No recompilation needed")

    @property
    def generators(self):
        generators = {}
        for generator in GENERATORS:
            generators[generator] = st.session_state[self._key("generator_" + generator)]
        return generators

    def reset(self):
        self._log("reset")
        if self._key("recompile_params") in st.session_state:
            del st.session_state[self._key("recompile_params")]

    def _needs_recompilation(self):
        with open(os.path.join(self._zs_dir, self._zs_file_path), "r") as zs_file:
            recompile_params = (self.generators, st.session_state[self._key("extra_args")],
                                self._zs_file_path, zs_file.read())

        self._log("recompile_params:", recompile_params)

        if (self._key("recompile_params") not in st.session_state or
            st.session_state[self._key("recompile_params")] != recompile_params):
            st.session_state[self._key("recompile_params")] = recompile_params
            return True

        return False

    def _compile(self):
        args = []
        args += st.session_state[self._key("extra_args")].split()
        args += ["-src", self._zs_dir]
        args.append(self._zs_file_path)
        for generator, checked in self.generators.items():
            if checked:
                args += ["-" + generator, os.path.join(self._gen_dir, generator)]

        self._log("compile:", args)
        completed_process = zserio.run_compiler(args)
        if completed_process.returncode != 0:
            # double whitespace needed before a newline for markdown to render the newline
            # see https://github.com/streamlit/streamlit/issues/868
            st.error(completed_process.stderr.replace("\n", "  \n"))
            return False

        # show zserio warnings
        if completed_process.stderr:
            st.warning(completed_process.stderr.replace("\n", "  \n"))

        return True

GENERATORS=[
    "python",
    "cpp",
    "java",
    "xml",
    "doc",
]
