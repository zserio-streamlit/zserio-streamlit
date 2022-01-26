import os
import re
import shutil
from glob import glob
import streamlit as st

import zserio

st.set_page_config(layout="wide", page_title="Interactive Zserio", page_icon="./img/zs.png")

def get_package_names(zs):
    m = re.search("package (.*);", zs)
    if m:
        return m.group(1).split(".")
    return ["default"]

def compile(zs, gen_dir, langs, extra_args):
    if not len(zs):
        return False

    package_names = get_package_names(zs)
    zs_path = os.path.join(gen_dir, "zs")
    zs_file_path = os.path.join(*package_names[0:-1], package_names[-1] + ".zs")
    os.makedirs(os.path.join(zs_path, *package_names[0:-1]))
    with open(os.path.join(zs_path, zs_file_path), "w") as zs_file:
        zs_file.write(zs)

    args=[]
    args+=extra_args
    args+=["-src", zs_path]
    args.append(zs_file_path)
    for lang in langs:
        args+=["-" + lang, os.path.join(gen_dir, lang)]

    completed_process = zserio.run_compiler(args)
    if completed_process.returncode != 0:
        st.error(completed_process.stderr)
        return False

    return True

def display_sources(gen_dir, lang):
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

uploaded_schema = st.file_uploader("Upload schema", type="zs")
if uploaded_schema:
    schema = uploaded_schema.getvalue().decode("utf8")
    uploaded_schema.close()
else:
    with open("sample/sample.zs", "r") as sample:
        schema = sample.read()
zs = st.text_area("Zserio Schema", value=schema, height=150)

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

gen_dir = "gen"
shutil.rmtree(gen_dir, ignore_errors=True)
with st.spinner("Compiling..."):
    if not compile(zs, gen_dir, checked_langs, extra_args):
        st.stop()

if len(checked_langs):
    cols = st.columns(len(checked_langs))
    for i, lang in enumerate(checked_langs):
        with cols[i]:
            display_sources(gen_dir, lang)
