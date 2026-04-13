"""
MPXJ File Converter - Web App
Uses org.mpxj.* package (correct for mpxj >= 13.x)
"""
import os, tempfile, traceback, glob, jpype

# Boot JVM once at startup with all mpxj jars on the classpath
def _start_jvm():
    if jpype.isJVMStarted():
        return
    import mpxj as _mpxj
    for jar in glob.glob(os.path.join(_mpxj.mpxj_dir, '*.jar')):
        jpype.addClassPath(jar)
    jpype.startJVM(convertStrings=True)

_start_jvm()

from flask import Flask, request, send_file, jsonify, render_template

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

OUTPUT_FORMATS = {
    "mspdi":   ("MS Project XML",   ".xml"),
    "mpx":     ("MPX",              ".mpx"),
    "xer":     ("Primavera XER",    ".xer"),
    "pmxml":   ("Primavera P6 XML", ".xml"),
    "sdef":    ("SDEF",             ".sdef"),
    "planner": ("Planner",          ".xml"),
}

# Lazy-load Java classes after JVM is running
def _get_classes():
    JClass = jpype.JClass
    return {
        "reader": JClass('org.mpxj.reader.UniversalProjectReader'),
        "mspdi":   JClass('org.mpxj.mspdi.MSPDIWriter'),
        "mpx":     JClass('org.mpxj.mpx.MPXWriter'),
        "xer":     JClass('org.mpxj.primavera.PrimaveraXERFileWriter'),
        "pmxml":   JClass('org.mpxj.primavera.PrimaveraPMFileWriter'),
        "sdef":    JClass('org.mpxj.sdef.SDEFWriter'),
        "planner": JClass('org.mpxj.planner.PlannerWriter'),
    }

_classes = None

def get_classes():
    global _classes
    if _classes is None:
        _classes = _get_classes()
    return _classes

def convert_file(input_path, output_path, fmt_id):
    classes = get_classes()
    project = classes["reader"]().read(input_path)
    classes[fmt_id]().write(project, output_path)

@app.route("/")
def index():
    return render_template("index.html", formats=OUTPUT_FORMATS)

@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    fmt_id = request.form.get("format", "mspdi")
    if fmt_id not in OUTPUT_FORMATS:
        return jsonify({"error": f"Unsupported format: {fmt_id}"}), 400
    uploaded = request.files["file"]
    ext = OUTPUT_FORMATS[fmt_id][1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.filename)[1]) as tmp_in:
        uploaded.save(tmp_in.name)
        input_path = tmp_in.name
    output_path = input_path + "_out" + ext
    try:
        convert_file(input_path, output_path, fmt_id)
        out_filename = os.path.splitext(uploaded.filename)[0] + ext
        return send_file(output_path, as_attachment=True, download_name=out_filename, mimetype="application/octet-stream")
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "jvm": jpype.isJVMStarted()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
