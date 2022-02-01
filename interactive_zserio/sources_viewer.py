import os
import streamlit as st

from glob import glob

from interactive_zserio.widget import Widget

class SourcesViewer(Widget):
    def __init__(self, gen_dir, generators):
        super().__init__("sources_viewer")
        self._gen_dir = gen_dir
        self._generators = generators

    def render(self):
        checked_generators = [generator for generator in self._generators if self._generators[generator]]
        self._log("render", checked_generators)
        if len(checked_generators):
            cols = st.columns(len(checked_generators))
            for i, generator in enumerate(checked_generators):
                with cols[i]:
                    self._display_sources(generator)

    def _display_sources(self, generator):
        st.caption(generator)
        generated_sources = glob(self._gen_dir + "/" + generator + "/**", recursive=True)
        for source in generated_sources:
            if os.path.isfile(source):
                with open(source, "r") as source_file:
                    with st.expander(source):
                        st.code(source_file.read(), self._map_highlighting(generator))

    def _map_highlighting(self, generator):
        if generator == "doc":
            return "html"
        return generator

