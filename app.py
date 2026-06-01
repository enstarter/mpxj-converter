import os, tempfile, traceback, glob, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from flask import Flask, request, send_file, jsonify, render_template

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

OUTPUT_FORMATS = {
    "mspdi":   ("MS Project XML",   ".xml"),
    "mpx":     ("MPX",              ".mpx"),
    "xer":     ("Primavera XER",    ".xer"),
    "pmxml":   ("Primavera P6 XML", ".xml"),
    "sdef":    ("SDEF",             ".sdef"),
    "planner": ("Planner",          ".xml"),
}

_jvm_started = False
_classes = None

def ensure_jvm():
    global _jvm_started, _classes
    if _jvm_started:
        return
    import jpype
    import mpxj as _mpxj
    if not jpype.isJVMStarted():
        for jar in glob.glob(os.path.join(_mpxj.mpxj_dir, '*.jar')):
            jpype.addClassPath(jar)
        jpype.startJVM(convertStrings=True)
        logger.info("JVM started")
    JC = jpype.JClass
    _classes = {
        "reader":  JC('org.mpxj.reader.UniversalProjectReader'),
        "mspdi":   JC('org.mpxj.mspdi.MSPDIWriter'),
        "mpx":     JC('org.mpxj.mpx.MPXWriter'),
        "xer":     JC('org.mpxj.primavera.PrimaveraXERFileWriter'),
        "pmxml":   JC('org.mpxj.primavera.PrimaveraPMFileWriter'),
        "sdef":    JC('org.mpxj.sdef.SDEFWriter'),
        "planner": JC('org.mpxj.planner.PlannerWriter'),
    }
    _jvm_started = True

def save_to_cloudinary(file_path, original_filename):
    try:
        import cloudinary, cloudinary.uploader
        cloudinary.config(
            cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
            api_key=os.environ.get("CLOUDINARY_API_KEY"),
            api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
            secure=True,
        )
        if not os.environ.get("CLOUDINARY_API_SECRET"):
            logger.warning("Cloudinary not configured - skipping")
            return
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in os.path.splitext(original_filename)[0])
        result = cloudinary.uploader.upload(file_path, public_id=f"mpxj-uploads/{safe}", resource_type="raw", unique_filename=True, overwrite=False)
        logger.info(f"Saved to Cloudinary: {result.get('secure_url')}")
    except Exception as e:
        logger.error(f"Cloudinary upload failed (non-fatal): {e}")

@app.route("/")
def index():
    fmt_json = {k: {"name": v[0], "ext": v[1]} for k, v in OUTPUT_FORMATS.items()}
    return render_template("index.html", formats=fmt_json)

@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    fmt_id = request.form.get("format", "mspdi")
    if fmt_id not in OUTPUT_FORMATS:
        return jsonify({"error": f"Unsupported format: {fmt_id}"}), 400
    uploaded = request.files["file"]
    ext = OUTPUT_FORMATS[fmt_id][1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.filename)[1]) as tmp:
        uploaded.save(tmp.name)
        input_path = tmp.name
    output_path = input_path + "_out" + ext
    try:
        save_to_cloudinary(input_path, uploaded.filename)
        ensure_jvm()
        project = _classes["reader"]().read(input_path)
        _classes[fmt_id]().write(project, output_path)
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
    return jsonify({"status": "ok", "jvm": _jvm_started, "cloudinary": "SET" if os.environ.get("CLOUDINARY_API_SECRET") else "NOT SET"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
