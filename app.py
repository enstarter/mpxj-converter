"""
MPXJ File Converter - Web App
Saves original uploads to Cloudinary.
"""
import os, tempfile, traceback, glob, jpype
import cloudinary
import cloudinary.uploader

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
)

# Boot JVM once at startup
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

_classes = None

def get_classes():
    global _classes
    if _classes is None:
        JClass = jpype.JClass
        _classes = {
            "reader":  JClass('org.mpxj.reader.UniversalProjectReader'),
            "mspdi":   JClass('org.mpxj.mspdi.MSPDIWriter'),
            "mpx":     JClass('org.mpxj.mpx.MPXWriter'),
            "xer":     JClass('org.mpxj.primavera.PrimaveraXERFileWriter'),
            "pmxml":   JClass('org.mpxj.primavera.PrimaveraPMFileWriter'),
            "sdef":    JClass('org.mpxj.sdef.SDEFWriter'),
            "planner": JClass('org.mpxj.planner.PlannerWriter'),
        }
    return _classes

def save_to_cloudinary(file_path, original_filename):
    """Upload original file to Cloudinary for archiving."""
    try:
        public_id = f"mpxj-uploads/{os.path.splitext(original_filename)[0]}"
        cloudinary.uploader.upload(
            file_path,
            public_id=public_id,
            resource_type="raw",  # non-image file
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
        print(f"Saved to Cloudinary: {public_id}")
    except Exception as e:
        # Don't fail the conversion if Cloudinary upload fails
        print(f"Cloudinary upload failed (non-fatal): {e}")

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
        # Save original to Cloudinary before converting
        save_to_cloudinary(input_path, uploaded.filename)

        # Convert
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
