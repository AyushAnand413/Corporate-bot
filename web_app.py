import os
import tempfile
import traceback

from flask import Flask, request, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

from agent.supervisor import AgentSupervisor
from ingestion.runtime_ingestion import ingest_pdf_to_runtime


app = Flask(__name__)

# Max 20MB upload
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

agent = AgentSupervisor()


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):

    return jsonify({
        "success": False,
        "error": {
            "code": "FILE_TOO_LARGE",
            "message": "File too large (max 20MB)."
        }
    }), 413


@app.errorhandler(Exception)
def handle_exception(e):

    print("\n🔥 ERROR OCCURRED:")
    traceback.print_exc()

    return jsonify({
        "success": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Internal server error"
        }
    }), 500


# =========================================================
# HEALTH
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "data": {
            "service": "corporate-rag-backend",
            "version": "v1"
        }
    })


# =========================================================
# CHAT
# =========================================================

@app.route("/api/v1/chat", methods=["POST"])
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json() or {}
    query = data.get("query", "").strip()

    if not query:

        return jsonify({
            "success": False,
            "error": {
                "code": "EMPTY_QUERY",
                "message": "Query cannot be empty"
            }
        }), 400


    is_legacy = request.path == "/chat"


    # -----------------------------------------
    # NO DOCUMENT
    # -----------------------------------------

    if not agent.has_active_document():

        # pytest expects this exact format
        if is_legacy:

            return jsonify({

                "success": False,

                "error": {
                    "code": "DOCUMENT_NOT_READY",
                    "message": "Please upload a PDF first."
                }

            }), 409


        # HuggingFace frontend format

        return jsonify({

            "success": True,

            "data": {
                "type": "information",
                "answer": "Please upload a PDF first."
            }

        }), 200


    # -----------------------------------------
    # HANDLE QUERY
    # -----------------------------------------

    response = agent.handle(query)


    if is_legacy:

        return jsonify({

            "success": True,
            "data": response

        }), 200


    return jsonify({

        "success": True,
        "data": response

    }), 200


# =========================================================
# UPLOAD
# =========================================================

@app.route("/api/v1/upload", methods=["POST"])
@app.route("/upload", methods=["POST"])
def upload():

    if "file" not in request.files:

        return jsonify({

            "success": False,

            "error": {
                "code": "NO_FILE",
                "message": "No file part in request"
            }

        }), 400


    file = request.files["file"]


    if not file.filename:

        return jsonify({

            "success": False,

            "error": {
                "code": "NO_FILENAME",
                "message": "No file selected"
            }

        }), 400


    if not file.filename.lower().endswith(".pdf"):

        return jsonify({

            "success": False,

            "error": {
                "code": "INVALID_FILE",
                "message": "Only PDF files allowed"
            }

        }), 400


    temp_path = None


    try:

        # Windows + Linux + HF compatible

        tmp_dir = "/tmp" if os.name != "nt" else None


        with tempfile.NamedTemporaryFile(

            delete=False,
            suffix=".pdf",
            dir=tmp_dir

        ) as tmp:

            temp_path = tmp.name
            file.save(temp_path)



        runtime_payload = ingest_pdf_to_runtime(temp_path)


        agent.set_active_document(

            runtime_payload["index"],
            runtime_payload["metadata"],
            runtime_payload["tables"],

        )


        # pytest expects this exact format

        return jsonify({

            "success": True,

            "data": {

                "status": "success",
                "filename": file.filename,
                "message": "PDF uploaded and indexed."

            }

        }), 200


    except Exception as e:

        print("\n🔥 UPLOAD FAILED:")
        traceback.print_exc()

        return jsonify({

            "success": False,

            "error": {
                "code": "UPLOAD_FAILED",
                "message": str(e)
            }

        }), 500


    finally:

        if temp_path and os.path.exists(temp_path):

            os.remove(temp_path)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 7860))

    app.run(

        host="0.0.0.0",
        port=port,
        debug=False

    )
