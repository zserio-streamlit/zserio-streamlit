import os
import re
import shutil
import sys
import streamlit as st
import zserio

from datetime import datetime
from glob import glob
from zipfile import ZipFile

# needed for python code
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

st.set_page_config(layout="wide", page_title="Interactive Zserio", page_icon="./img/zs.png")

def init_session_variable(name, value=None):
    if name not in st.session_state:
        st.session_state[name] = value

init_session_variable("schema_mode_changed", True)
init_session_variable("upload_schema_changed", False)
init_session_variable("zs_code", None)
init_session_variable("selected_file", None)
init_session_variable("recompile_params", None)
init_session_variable("py_code", None)

def log(*args):
    print(datetime.now().strftime("%H:%M:%S.%f: "), *args, file=sys.stderr)

def schema_mode_on_change():
    st.session_state.zs_code = None
    st.session_state.selected_file = None
    st.session_state.recompile_params = None
    st.session_state.py_code = None

    st.session_state.schema_mode_changed = True


def cleanup_workspace(ws_dir, zs_dir):
    shutil.rmtree(ws_dir, ignore_errors=True)
    os.makedirs(zs_dir)

def write_schema(ws_dir, zs_dir):
    if not st.session_state.schema_mode_changed:
        return

    cleanup_workspace(ws_dir, zs_dir)

def upload_schema_on_change():
    st.session_state.upload_schema_changed = True

def upload_schema(ws_dir, zs_dir):
    upload_help="Upload either a simple schema file *.zs, or complex schema as a *.zip."
    uploaded_schema = st.file_uploader("Upload schema", type=["zs","zip"], help=upload_help,
                                       on_change=upload_schema_on_change)
    if not st.session_state.schema_mode_changed and not st.session_state.upload_schema_changed:
        return

    if not uploaded_schema:
        cleanup_workspace(ws_dir, zs_dir)
        st.stop()

    if st.session_state.upload_schema_changed:
        cleanup_workspace(ws_dir, zs_dir)
        with ZipFile(uploaded_schema, "r") as zip_file:
            zip_file.extractall(zs_dir)
        st.session_state.upload_schema_changed = False

def sample_schema(ws_dir, zs_dir):
    if not st.session_state.schema_mode_changed:
        return

    cleanup_workspace(ws_dir, zs_dir)
    shutil.copy("sample_src/sample.zs", zs_dir)

def list_schema_files(folder):
    listed_files = []
    for root, _, files in os.walk(folder):
        for listed_file in files:
            if listed_file.endswith(".zs"):
                listed_files.append(os.path.relpath(os.path.join(root, listed_file), folder))
    listed_files.sort()
    return listed_files

def create_new_file(zs_dir):
    file_path = st.text_input("Choose file path", help="Enter relative path of the schema file to create.")
    if not file_path:
        st.stop()

    if not file_path.endswith(".zs"):
        st.error("Extension must be *.zs")
        st.stop()

    file_full_path = os.path.join(zs_dir, file_path)
    path, file_name = os.path.split(file_full_path)
    os.makedirs(path, exist_ok=True)
    with open(file_full_path, "w") as new_file:
        package_definition = ".".join(os.path.splitext(file_path)[0].split(os.sep))
        new_file.write(f"package {package_definition};\n")

    st.session_state.zs_code = None
    return file_path

def choose_file_on_change():
    st.session_state.zs_code = None

def selected_file_index(schema_files):
    if st.session_state.selected_file is None:
        return 0

    index = schema_files.index(st.session_state.selected_file)
    log("index:", st.session_state.selected_file, index)
    st.session_state.selected_file = None
    return index

def choose_file(zs_dir):
    schema_files = list_schema_files(zs_dir)
    if schema_files:
        index = selected_file_index(schema_files)

        create_new = "Create new..."
        schema_files.append(create_new)

        cols = st.columns([7, 1])
        choose_help="Choose file to edit. The selected file will be used as root schema file for compilation."
        selected_file = cols[0].selectbox("Choose schema file", options=schema_files, index=index,
                                          on_change=choose_file_on_change, help=choose_help)
        cols[1].title("")
        remove_file = cols[1].button("❌ Delete", disabled=(selected_file == create_new),
                                     help="Remove the selected file.")
        if remove_file:
            os.remove(os.path.join(zs_dir, selected_file))
            st.experimental_rerun()

    if not schema_files or selected_file == create_new:
        st.session_state.selected_file = create_new_file(zs_dir)
        st.experimental_rerun()

    return selected_file

def edit_file(zs_dir, file_path):
    if st.session_state.zs_code is None:
        log("read schema file:", file_path)
        with open(os.path.join(zs_dir, file_path), "r") as f:
            st.session_state.zs_code = f.read()

    new_content = st.text_area(file_path, height=250, key="zs_code")
    with open(os.path.join(zs_dir, file_path), "w") as f:
        log("write schema file:", file_path)
        f.write(new_content)

def compile(zs_dir, root_zs_file_path, gen_dir, generators, extra_args):
    args=[]
    args+=extra_args
    args+=["-src", zs_dir]
    args.append(root_zs_file_path)
    for generator, checked in generators.items():
        if checked:
            args+=["-" + generator, os.path.join(gen_dir, generator)]

    completed_process = zserio.run_compiler(args)
    if completed_process.returncode != 0:
        st.error(completed_process.stderr)
        return False

    return True

def recompile_params_changed(zs_dir, root_zs_file_path, generators, extra_args):
    with open(os.path.join(zs_dir, root_zs_file_path), "r") as root_zs_file:
        recompile_params = (root_zs_file_path, root_zs_file.read(), generators, extra_args)

    if st.session_state.recompile_params != recompile_params:
        st.session_state.recompile_params = recompile_params
        return True
    return False

def recompile(zs_dir, root_zs_file_path, gen_dir, generators, extra_args):
    if recompile_params_changed(zs_dir, root_zs_file_path, generators, extra_args):
        for generator in generators:
            shutil.rmtree(os.path.join(gen_dir, generator), ignore_errors=True)
        with st.spinner("Compiling..."):
            if not compile(zs_dir, root_zs_file_path, gen_dir, generators, extra_args):
                st.stop()
    else:
        st.info("No recompilation needed")

def create_zip(ws_dir, zip_filename):
    zip_path = os.path.join(ws_dir, zip_filename)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    files_to_zip = []
    for root, dirs, files in os.walk(ws_dir):
        for f in files:
            files_to_zip.append(os.path.join(root, f))
    with ZipFile(zip_path, "w") as zip_file:
        for f in files_to_zip:
            zip_file.write(f)

def map_highlighting(generator):
    if generator == "doc":
        return "html"
    return generator

def display_sources(gen_dir, generator):
    st.caption(generator)
    generated = glob(gen_dir + "/" + generator + "/**", recursive=True)
    for gen in generated:
        if os.path.isfile(gen):
            with open(gen, "r") as source:
                with st.expander(gen):
                    st.code(source.read(), map_highlighting(generator))

def add_zip_download(zip_path):
    with open(zip_path, "rb") as zip_file:
        st.download_button("Download workspace", zip_file, mime="application/zip",
                           help="Download whole workspace as a zip file.")

st.write("""
# Interactive Zserio Compiler!
""")

ws_dir = "workspace"
zs_dir = os.path.join(ws_dir, "zs")
gen_dir = os.path.join(ws_dir, "gen")
src_dir = os.path.join(ws_dir, "src")
code_filename = "code.py"
zip_filename = "all.zip"

schema_modes = { "write": "Write schema", "upload": "Upload schema", "sample": "Sample" }
schema_mode = st.selectbox("Schema", schema_modes, format_func=lambda x: schema_modes[x], index=2,
                           on_change=schema_mode_on_change)
if schema_mode == "write":
    write_schema(ws_dir, zs_dir)
elif schema_mode == "upload":
    upload_schema(ws_dir, zs_dir)
elif schema_mode == "sample":
    sample_schema(ws_dir, zs_dir)
else:
    log("unknown schema mode!", schema_mode)
    st.error("Unknown schema mode!")
st.session_state.schema_mode_changed = False

zs_root_file_path = choose_file(zs_dir)

edit_file(zs_dir, zs_root_file_path)

extra_args = st.text_input("Extra Arguments").split()

generators = {
    "python": True,
    "cpp": False,
    "java": False,
    "xml": False,
    "doc" : False
}

generators_cols = st.columns(len(generators))

generators_checks = []
for i, (generator, generator_enabled) in enumerate(generators.items()):
    with generators_cols[i]:
        generators_checks.append(st.checkbox(generator, value=generator_enabled))

for i, generator in enumerate(generators):
    generators[generator] = generators_checks[i]

recompile(zs_dir, zs_root_file_path, gen_dir, generators, extra_args)

checked_generators = [generator for generator in generators if generators[generator]]
if len(checked_generators):
    cols = st.columns(len(checked_generators))
    for i, generator in enumerate(checked_generators):
        with cols[i]:
            display_sources(gen_dir, generator)

python_code_check = st.checkbox("Experimental python code", help="Python generator must be enabled", value=True)

if python_code_check and generators["python"]:
    os.makedirs(src_dir, exist_ok=True)
    code_file_path = os.path.join(src_dir, code_filename)
    if not os.path.exists(code_file_path):
        if schema_mode == "sample":
            shutil.copy(os.path.join("sample_src", "sample.py"), code_file_path)
        else:
            open(code_file_path, "w").close()

    sys.dont_write_bytecode = True
    gen_path = os.path.join(gen_dir, "python")
    if sys.path[-1] != gen_path:
        sys.path.append(gen_path)

    modules_keys = set(sys.modules.keys())

    if st.session_state.py_code is None:
        with open(code_file_path, "r") as code_file:
            log("read code file:", code_file_path)
            st.session_state.py_code = code_file.read()

    new_py_code = st.text_area("Python code", height=250, key="py_code")
    with open(code_file_path, "w") as code_file:
        log("write code file:", code_file_path)
        code_file.write(new_py_code)

    with StringIO() as out, redirect_stdout(out):
        st.caption("Python output")
        try:
            exec(new_py_code)
            st.text(out.getvalue())
        except Exception as e:
            st.error(e)

    # allow to reload modules imported by the python code
    new_modules_keys = set(sys.modules.keys())
    modules_to_remove = new_modules_keys - modules_keys
    for module_to_remove in modules_to_remove:
        sys.modules.pop(module_to_remove)

create_zip(ws_dir, zip_filename)
add_zip_download(os.path.join(ws_dir, zip_filename))
