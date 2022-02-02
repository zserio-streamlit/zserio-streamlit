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

        self._extra_arguments = ""
        self._generators = {
            "python": True,
            "cpp": False,
            "java": False,
            "xml": False,
            "doc" : False
        }

    def set_zs_file_path(self, zs_file_path):
        self._zs_file_path = zs_file_path

    def render(self):
        self._log("render")

        self._extra_args = st.text_input("Extra Arguments").split()

        generators_cols = st.columns(len(self._generators))
        generators_checks = []
        for i, (generator, generator_enabled) in enumerate(self._generators.items()):
            with generators_cols[i]:
                generators_checks.append(st.checkbox(generator, value=generator_enabled))

        for i, generator in enumerate(self._generators):
            self._generators[generator] = generators_checks[i]

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
        return self._generators

    def reset(self):
        self._log("reset")
        if self._key("recompile_params") in st.session_state:
            del st.session_state[self._key("recompile_params")]

    def _needs_recompilation(self):
        with open(os.path.join(self._zs_dir, self._zs_file_path), "r") as zs_file:
            recompile_params = (self._generators, self._extra_args, self._zs_file_path,
                                zs_file.read())

        self._log("recompile_params:", recompile_params)

        if (self._key("recompile_params") not in st.session_state or
            st.session_state[self._key("recompile_params")] != recompile_params):
            st.session_state[self._key("recompile_params")] = recompile_params
            return True

        return False

    def _compile(self):
        args = []
        args += self._extra_args
        args += ["-src", self._zs_dir]
        args.append(self._zs_file_path)
        for generator, checked in self._generators.items():
            if checked:
                args += ["-" + generator, os.path.join(self._gen_dir, generator)]

        self._log("compile:", args)
        completed_process = zserio.run_compiler(args)
        if completed_process.returncode != 0:
            st.error(completed_process.stderr)
            return False

        return True
