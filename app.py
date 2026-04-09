"""
MPXJ File Converter - Web App
Deployable to Railway.app with zero configuration.
"""

from flask import Flask, request, send_file, jsonify, render_template
import tempfile, os, traceback

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

OUTPUT_FORMATS = {
    "mspdi":   ("MS Project XML",         ".xml"),
    "mpx":     ("MPX",                    ".mpx"),
    "xer":     ("Primavera XER",          ".xer"),
    "pmxml":   ("Primavera P6 XML",       ".xml"),
    "sdef":    ("SDEF",                   ".sdef"),
    "planner": ("Planner",                ".xml"),
}

def get_writer(fmt_id):
    import mpxj
    writers = {
        "mspdi":   mpxj.MSPDIWriter,
        "mpx":     mpxj.MPXWriter,
        "xer":     mpxj.PrimaveraXERFileWriter,
        "pmxml":   mpxj.PrimaveraPMFileWriter,
        "sdef":    mpxj.SDEFWriter,
        "planner": mpxj.PlannerWriter,
    }
    cls = writers.get(fmt_id)
    if cls is None:
        raise ValueError(f"Unknown output format: {fmt_id}")
    return cls()

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
    _, (_, ext) = fmt_id, OUTPUT_FORMATS[fmt_id]
    ext = OUTPUT_FORMATS[fmt_id][1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.filename)[1]) as tmp_in:
        uploaded.save(tmp_in.name)
        input_path = tmp_in.name

    output_path = input_path + "_out" + ext

    try:
        from mpxj.reader import UniversalProjectReader
        project = UniversalProjectReader().read(input_path)
        writer = get_writer(fmt_id)
        writer.write(project, output_path)

        out_filename = os.path.splitext(uploaded.filename)[0] + ext
        return send_file(
            output_path,
            as_attachment=True,
            download_name=out_filename,
            mimetype="application/octet-stream"
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        # cleanup output after send (best effort)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
