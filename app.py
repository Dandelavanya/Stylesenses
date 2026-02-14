"""
StyleAI - AI-powered fashion styling web application.
Run locally: python app.py
"""
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory

from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from utils.validators import validate_upload
from utils.skin_tone import detect_skin_tone
from utils.groq_client import get_recommendations

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)


@app.route("/")
def index():
    """Serve home/landing page."""
    return render_template("home.html")


@app.route("/styling")
def styling():
    """Serve styling/upload page."""
    return render_template("styling.html")


@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/testimonials")
def testimonials():
    return render_template("testimonials.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Accept image upload + gender; return skin tone, RGB, and recommendations.
    Expects: multipart/form-data with 'image' (file) and 'gender' (Male|Female).
    """
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image provided."}), 400
    if "gender" not in request.form:
        return jsonify({"success": False, "error": "Gender not selected."}), 400

    file = request.files["image"]
    gender = (request.form.get("gender") or "Female").strip()
    if gender not in ("Male", "Female"):
        gender = "Female"

    is_valid, err = validate_upload(file)
    if not is_valid:
        return jsonify({"success": False, "error": err}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = Path(app.config["UPLOAD_FOLDER"]) / safe_name
    try:
        file.save(str(save_path))
    except Exception as e:
        return jsonify({"success": False, "error": "Failed to save upload."}), 500

    try:
        skin_result = detect_skin_tone(str(save_path))
    except Exception:
        skin_result = {
            "skin_tone": "Medium",
            "rgb": [150, 120, 100],
            "r": 150, "g": 120, "b": 100,
            "face_detected": False,
            "message": "Analysis failed; using default.",
        }
    finally:
        try:
            if save_path.exists():
                save_path.unlink()
        except Exception:
            pass

    try:
        recs = get_recommendations(
            skin_result["skin_tone"],
            gender,
            skin_result["rgb"],
        )
    except Exception:
        recs = get_recommendations(
            skin_result["skin_tone"],
            gender,
            skin_result["rgb"],
        )

    return jsonify({
        "success": True,
        "skin_tone": skin_result["skin_tone"],
        "rgb": skin_result["rgb"],
        "r": skin_result["r"],
        "g": skin_result["g"],
        "b": skin_result["b"],
        "face_detected": skin_result["face_detected"],
        "message": skin_result.get("message", ""),
        "gender": gender,
        "recommendations": recs,
    })


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve uploaded files (if needed for preview)."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.errorhandler(413)
def too_large(e):
    return jsonify({"success": False, "error": "File too large. Maximum size is 10MB."}), 413


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
