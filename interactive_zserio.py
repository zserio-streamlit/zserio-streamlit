import os
import sys
import re
import io
import shutil
import streamlit as st
from glob import glob
from zipfile import ZipFile

# needed for python code
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

import zserio

st.set_page_config(layout="wide", page_title="Interactive Zserio", page_icon="./img/zs.png")

def get_package_names(zs):
    m = re.search("package (.*);", zs)
    if m:
        return m.group(1).split(".")
    return ["default"]

def compile(zs_dir, root_zs_file_path, gen_dir, langs, extra_args):
    args=[]
    args+=extra_args
    args+=["-src", zs_dir]
    args.append(root_zs_file_path)
    for lang, checked in langs.items():
        if checked:
            args+=["-" + lang, os.path.join(gen_dir, lang)]

    completed_process = zserio.run_compiler(args)
    if completed_process.returncode != 0:
        st.error(completed_process.stderr)
        return False

    return True

def compress(gen_dir, zip_filename):
    zip_path = os.path.join(gen_dir, zip_filename)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    files_to_zip = []
    for root, dirs, files in os.walk(gen_dir):
        for f in files:
            files_to_zip.append(os.path.join(root, f))
    with ZipFile(zip_path, "w") as zip_file:
        for f in files_to_zip:
            zip_file.write(f)

def recompile_params_changed(zs_dir, root_zs_file_path, checked_langs, extra_args):
    with open(os.path.join(zs_dir, root_zs_file_path), "r") as root_zs_file:
        recompile_params = (root_zs_file.read(), checked_langs, extra_args)

    if not "recompile_params" in st.session_state or st.session_state.recompile_params != recompile_params:
        st.session_state.recompile_params = recompile_params
        return True
    return False

def recompile(zs_dir, root_zs_file_path, gen_dir, langs, extra_args):
    if recompile_params_changed(zs_dir, root_zs_file_path, langs, extra_args):
        for lang in langs:
            shutil.rmtree(os.path.join(gen_dir, lang), ignore_errors=True)
        with st.spinner("Compiling..."):
            if not compile(zs_dir, root_zs_file_path, gen_dir, langs, extra_args):
                st.stop()
        return True
    else:
        st.info("No recompilation needed...")
        return False

def map_highlighting(lang):
    if lang == "doc":
        return "html"
    if lang == "cpp":
        # see: https://discuss.streamlit.io/t/c-markdown-syntax-highlighting-doesnt-work/14106/2
        # streamlit seems to have problems with c++ / cpp / cxx
        return "c"
    return lang

def display_sources(gen_dir, lang):
    st.caption(lang)
    generated = glob(gen_dir + "/" + lang + "/**", recursive=True)
    for gen in generated:
        if os.path.isfile(gen):
            with open(gen, "r") as source:
                with st.expander(gen):
                    st.code(source.read(), map_highlighting(lang))

def add_zip_download(zip_path):
    with open(zip_path, "rb") as zip_file:
        st.download_button("Download sources", zip_file, mime="application/zip")

def upload_schema(zs_dir, uploaded_schema):
    if uploaded_schema.type == "application/zip":
        #complex schema within the zip file - just unpack in the zs_dir directory
        shutil.rmtree(zs_dir, ignore_errors=True)
        schema_files = []
        with ZipFile(uploaded_schema, "r") as zip_file:
            zip_file.extractall(zs_dir)
        for root, dirs, files in os.walk(zs_dir):
            for f in files:
                schema_files.append(os.path.relpath(os.path.join(root, f), zs_dir))
        return st.selectbox("Choose root file", schema_files)
    else:
        # simple schema - process content in case that the schema file contains complex package name
        schema = uploaded_schema.getvalue().decode("utf8")
        return process_simple_schema(schema, zs_dir)

def process_simple_schema(schema, zs_dir):
    zs = st.text_area("Zserio Schema", value=schema, height=150)
    if not zs.strip():
        return None

    package_names = get_package_names(zs)
    root_zs_file_path = os.path.join(*package_names[0:-1], package_names[-1] + ".zs")
    shutil.rmtree(zs_dir, ignore_errors=True)
    os.makedirs(os.path.join(zs_dir, *package_names[0:-1]))
    with open(os.path.join(zs_dir, root_zs_file_path), "w") as zs_file:
        zs_file.write(zs)
    return root_zs_file_path

st.write("""
# Interactive Zserio Compiler!
""")

gen_dir = "gen"
zs_dir = os.path.join(gen_dir, "zs")
zip_filename = "gen.zip"

st.session_state.sample_mode = False

upload_help="Upload either a simple schema file *.zs, or complex schema as a *.zip."
uploaded_schema = st.file_uploader("Upload schema", type=["zs","zip"], help=upload_help)
if uploaded_schema:
    st.session_state.sample_mode = False
    root_zs_file_path = upload_schema(zs_dir, uploaded_schema)
    uploaded_schema.close()
else:
    with open("sample_src/sample.zs", "r") as sample:
        st.session_state.sample_mode = True
        schema = sample.read()
        root_zs_file_path = process_simple_schema(schema, zs_dir)

extra_args = st.text_input("Extra Arguments").split()

langs = {
    "python": True,
    "cpp": False,
    "java": False,
    "xml": False,
    "doc" : False
}

langs_cols = st.columns(len(langs))

langs_checks = []
for i, (lang, lang_enabled) in enumerate(langs.items()):
    with langs_cols[i]:
        langs_checks.append(st.checkbox(lang, value=lang_enabled))

for i, lang in enumerate(langs):
    langs[lang] = langs_checks[i]

if not root_zs_file_path:
    st.info("No schema provided...")
    st.stop()

if recompile(zs_dir, root_zs_file_path, gen_dir, langs, extra_args):
    compress(gen_dir, zip_filename)

checked_langs = [lang for lang in langs if langs[lang]]
if len(checked_langs):
    cols = st.columns(len(checked_langs))
    for i, lang in enumerate(checked_langs):
        with cols[i]:
            display_sources(gen_dir, lang)
    add_zip_download(os.path.join(gen_dir, zip_filename))

python_code_check = st.checkbox("Experimental python code", help="Python generator must be enabled", value=True)

if python_code_check and "python" in checked_langs:
    sys.dont_write_bytecode = True
    gen_path = os.path.join(gen_dir, "python")
    if sys.path[-1] != gen_path:
        sys.path.append(gen_path)

    modules_keys = set(sys.modules.keys())

    if st.session_state.sample_mode:
        if not "py_sample_code" in st.session_state:
            with open("sample_src/sample.py", "r") as sample:
                st.session_state.py_sample_code = sample.read()
        py_code = st.session_state.py_sample_code
    else:
        py_code = ""

    py_code = st.text_area("Python code", value=py_code, height=250)

    if st.session_state.sample_mode:
        st.session_state.py_sample_code = py_code

    with StringIO() as out, redirect_stdout(out):
        st.caption("Python output")
        try:
            exec(py_code)
            st.text(out.getvalue())
        except Exception as e:
            st.error(e)

    # allow to reload modules imported by the python code
    new_modules_keys = set(sys.modules.keys())
    modules_to_remove = new_modules_keys - modules_keys
    for module_to_remove in modules_to_remove:
        sys.modules.pop(module_to_remove)
