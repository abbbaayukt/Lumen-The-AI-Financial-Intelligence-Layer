# document_bp.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from model import db, Document, Transaction
import os
from llm import LLM
from ocr import extract
import uuid
from gst_check import api_keys, lookup_gstin_using_keys
from datetime import datetime

document_bp = Blueprint("document", __name__, url_prefix="/document")


def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


@document_bp.get("/")
@jwt_required()
def get_documents():
    user_id = int(get_jwt_identity())

    # pagination
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    query = Document.query.filter_by(user_id=user_id).order_by(Document.uploaded_at.desc())
    paginated = query.paginate(page=page, per_page=limit, error_out=False)

    documents = [
        {
            "id": d.id,
            "file_name": d.file_name,
            "file_url": d.file_url,
            "vendor_name": d.vendor_name,
            "category": d.category,
            "notes": d.notes,
            "status": d.status,
            "transaction_id": d.transaction_id,
            "uploaded_at": d.uploaded_at.isoformat(),
        }
        for d in paginated.items
    ]

    return jsonify({
        "documents": documents,
        "page": paginated.page,
        "total_pages": paginated.pages,
        "total": paginated.total,
    }), 200


@document_bp.post("/add")
@jwt_required()
def add_document():
    """
    Upload file -> OCR -> LLM extraction -> GST lookup -> create Transaction & Document.
    Returns rich payload including llm output and gst_details (if any).
    """
    user_id = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({"error": "File is required"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Invalid file name"}), 400

    allowed_ext = {"pdf", "png", "jpg", "jpeg", "webp"}
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_ext:
        return jsonify({"error": "Unsupported file format"}), 400

    # Save file
    upload_folder = os.path.join(os.getcwd(), "documents")
    os.makedirs(upload_folder, exist_ok=True)
    new_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(upload_folder, new_filename)
    try:
        file.save(file_path)
    except Exception as e:
        current_app.logger.exception("Failed to save uploaded file")
        return jsonify({"error": "Failed to save file", "details": str(e)}), 500

    # OCR
    try:
        extracted_text = extract(file_path)
    except Exception as e:
        current_app.logger.exception("OCR failed")
        return jsonify({"error": "OCR failed", "details": str(e)}), 500

    # user hints
    user_vendor = request.form.get("vendor", "") or ""
    user_category = request.form.get("category", "") or ""
    user_notes = request.form.get("notes", "") or ""

    combined_prompt_text = (
        f"USER HINTS:\n"
        f"- Vendor: {user_vendor}\n"
        f"- Category: {user_category}\n"
        f"- Notes: {user_notes}\n\n"
        f"EXTRACTED BILL TEXT:\n{extracted_text}"
    )

    # Try several API keys (if configured) to extract using LLM
    llm_data = None
    last_exception = None
    for i in range(3):
        try:
            key_env = os.getenv(f"GEMINI_API_KEY_{i+1}")
            llm = LLM(api_key=key_env)
            llm_data = llm.extract_bill_info(combined_prompt_text)
            print(llm_data)
            break
        except Exception as e:
            last_exception = e
            current_app.logger.exception(f"LLM call failed for key index {i}")
            continue

    if llm_data is None:
        return jsonify({"error": "LLM extraction failed", "details": str(last_exception)}), 500

    # Normalize LLM output with safe defaults
    item_name = llm_data.get("item_name", "") or "Unknown Item"
    amount = safe_float(-llm_data.get("amount", 0))
    category = (llm_data.get("category") or user_category or "Uncategorized")
    payment_mode = llm_data.get("payment_mode", "") or "Unknown"
    tx_date_raw = llm_data.get("transaction_date", "")
    vendor = llm_data.get("vendor") or user_vendor or ""
    description = llm_data.get("description", "") or ""
    tags = llm_data.get("tags", "") or ""
    legitimacy = llm_data.get("legitimacy", "verified")
    legitimacy_report = llm_data.get("legitimacy_report", "")

    # parse date; fallback to today
    try:
        tx_date = datetime.strptime(tx_date_raw, "%Y-%m-%d").date()
    except Exception:
        try:
            # try common alternate formats
            tx_date = datetime.strptime(tx_date_raw, "%d-%m-%Y").date()
        except Exception:
            tx_date = datetime.utcnow().date()

    # GST lookup
    gst_details = None
    gstin = (llm_data.get("gst_number") or "").strip()
    if gstin:
        try:
            gst_response = lookup_gstin_using_keys(api_keys, gstin)
            result_data = gst_response.get("result") or {}
            # map known fields (adjust keys depending on gst_check response shape)
            pradr = result_data.get("pradr", {}) or {}
            addr = (pradr.get("addr") or {}) if isinstance(pradr, dict) else {}
            gst_details = {
                "legal_name": result_data.get("lgnm", "") or "",
                "trade_name": result_data.get("tradeNam", "") or "",
                "status": result_data.get("sts", "") or "",
                "address": addr.get("bnm", "") or addr.get("addr1", "") or "",
                "state": result_data.get("stj", "") or "",
                "district": result_data.get("dst", "") or "",
                "pincode": addr.get("pncd", "") or "",
                "constitution": result_data.get("ctb", "") or "",
                "pan": result_data.get("pan", "") or "",
                "registration_date": result_data.get("rgdt", "") or "",
                "last_updated": result_data.get("lstupdt", "") or "",
                "raw": result_data
            }
        except Exception:
            current_app.logger.exception("GST lookup failed")
            gst_details = None

    # create transaction & document in DB
    try:
        new_tx = Transaction(
            user_id=user_id,
            item_name=item_name,
            amount=amount,
            category=category,
            payment_mode=payment_mode,
            transaction_date=tx_date,
            vendor=vendor,
            description=description,
            tags=tags
        )
        db.session.add(new_tx)
        db.session.flush()  # get new_tx.id

        status = "verified" if str(legitimacy).lower() == "verified" else "rejected"

        doc = Document(
            user_id=user_id,
            transaction_id=new_tx.id,
            file_name=new_filename,
            file_url=f"/documents/{new_filename}",
            vendor_name=vendor,
            category=category,
            notes=user_notes,
            status=status
        )

        db.session.add(doc)
        db.session.commit()

        response_payload = {
            "message": "Document processed successfully",
            "transaction_id": new_tx.id,
            "document_id": doc.id,
            "status": status,
            "llm": {
                "item_name": item_name,
                "amount": amount,
                "category": category,
                "payment_mode": payment_mode,
                "transaction_date": tx_date.isoformat(),
                "vendor": vendor,
                "description": description,
                "tags": tags,
                "legitimacy": legitimacy,
                "legitimacy_report": legitimacy_report,
                "gst_number": gstin,
            },
            "gst_details": gst_details,
            "file_url": doc.file_url
        }

        return jsonify(response_payload), 201

    except Exception as e:
        current_app.logger.exception("Failed to create DB records")
        db.session.rollback()
        return jsonify({"error": "Failed to persist records", "details": str(e)}), 500
