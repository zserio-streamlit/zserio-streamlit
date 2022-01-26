import os
import re
import shutil
from glob import glob
import streamlit as st

import zserio

gen_dir = "gen"
st.set_page_config(layout="wide", page_title="Interactive Zserio")

def checked_langs(languages, languages_checks):
    langs = []
    for i, lang in enumerate(languages):
        pass

def get_package(zs):
    m = re.search("package (.*);", zs)
    if m:
        return m.group(1)
    return None

def compile(zs, langs, extra_args):
    pkg = get_package(zs)
    if not pkg:
        st.error("Cannot parse package name!")
        return False
    zs_name = pkg + ".zs"
    if not os.path.exists(gen_dir):
        os.mkdir(gen_dir)
    zs_filename = os.path.join(gen_dir, zs_name)
    with open(zs_filename, "w") as zs_file:
        zs_file.write(zs)

    args=[]
    args+=extra_args
    args+=["-src", gen_dir]
    args.append(zs_name)
    for lang in langs:
        args+=["-" + lang, os.path.join(gen_dir, lang)]

    completed_process = zserio.run_compiler(args)
    if completed_process.returncode != 0:
        st.error(completed_process.stderr)
        return False

    return True

def display_sources(lang):
    st.caption(lang)
    generated = glob(gen_dir + "/" + lang + "/**", recursive=True)
    for gen in generated:
        if os.path.isfile(gen):
            with open(gen, "r") as source:
                with st.expander(gen):
                    st.code(source.read(), lang if lang != "doc" else "html")

st.write("""
# Interactive Zserio Compiler!
""")

zs = st.text_area("Zserio Schema")
extra_args = st.text_input("Extra Arguments:").split()

langs = (
    "python", "cpp", "java", "xml", "doc"
)

langs_cols = st.columns(len(langs))

langs_checks = []
for i, lang in enumerate(langs):
    with langs_cols[i]:
        langs_checks.append(st.checkbox(lang))

checked_langs = []
for i, checked in enumerate(langs_checks):
    if checked:
        checked_langs.append(langs[i])

shutil.rmtree(gen_dir, ignore_errors=True)

with st.spinner("Compiling..."):
    if not compile(zs, checked_langs, extra_args):
        st.stop()

cols = st.columns(len(checked_langs))
for i, checked in enumerate(langs_checks):
    if checked:
        with cols[i]:
            display_sources(langs[i])
