import re
from PIL import Image
import io
import os

is_photo_detected = False
decompressed_bytes=""
photo_path = None

# if r["result"]["data"]["format"]=='bigint':
#     decompressed_bytes = r["result"]["data"]["qr_values"][-1]
#     r["result"]["data"]["qr_values"].pop()
#     print(decompressed_bytes)

#     data = decompressed_bytes   

#     try:
#         # ---- 1. Find JPEG2000 codestream (starts with 0xFF4F and ends with 0xFFD9 or similar) ----
#         start_marker = b'\xff\x4f'
#         start = data.find(start_marker)

#         if start == -1:
#             raise ValueError("JPEG2000 start marker not found")

#         jp2_data = data[start:]  # take till end (works for most Aadhaar blobs)

#         # ---- 2. Open with PIL (requires pillow with jpeg2000 support / openjpeg) ----
#         image = Image.open(io.BytesIO(jp2_data))

#         # ---- 3. Save as PNG ----
#         photo_path = "profile_photo.png"

#         image.save(photo_path)

#         print("Saved as profile_photo.png")

#         if os.path.exists(photo_path) and os.path.getsize(photo_path) > 0:
#                 is_photo_detected = True

#     except Exception as e:
#         print(f"⚠️ Photo extraction failed: {e}")
#         is_photo_detected = False

import re

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def is_valid_date(s):
    return bool(re.match(r'\d{2}[-/]\d{2}[-/]\d{4}', str(s)))


def clean_qr_list(fields):
    cleaned = []

    for f in fields:
        if f is None:
            continue

        f = str(f).strip()

        if not f:
            continue

        # remove garbage binary chars
        if any(ord(c) < 32 for c in f):
            continue

        # skip very small noise
        if len(f) < 2:
            continue

        cleaned.append(f)

    return cleaned


# ─────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────

def is_valid_qr(data):
    if not data:
        return False

    fmt = data.get("format")

    # ── XML ───────────────────────────────────────────────────
    if fmt == "xml":
        return (
            data.get("name") and
            data.get("gender") and
            (data.get("dob") or data.get("yob"))
        )

    # ── BIGINT (UPDATED ✅) ───────────────────────────────────
    elif fmt == "bigint":
        fields = data.get("qr_values", [])

        if not fields or len(fields) < 6:
            return False

        # ⚠️ DO NOT CLEAN HERE
        name = str(fields[3]).strip() if len(fields) > 3 else ""
        dob  = str(fields[4]).strip() if len(fields) > 4 else ""

        # Basic checks
        if not name or name.isdigit():
            return False

        if len(name) < 3:
            return False

        # Flexible date check (important 🔥)
        if not re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', dob):
            return False

        return True
    return False


# ─────────────────────────────────────────────────────────────
# BEST QR SELECTION
# ─────────────────────────────────────────────────────────────

def select_best_qr(results):
    valid_results = []

    for r in results:
        res = r["result"]
        print("\n🔍 Checking:", r["image"])
        print(res)

        if not res.get("success"):
            continue

        data = res.get("data", {})

        if is_valid_qr(data):
            print("   ✅ VALID QR")
            valid_results.append(res)
        else:
            print("   ❌ INVALID QR")

    # 🥇 Prefer XML
    for r in valid_results:
        if r["data"]["format"] == "xml":
            print("\n🏆 Selected XML QR")
            return r

    # 🥈 Else take best BigInt (first valid)
    if valid_results:
        print("\n🏆 Selected BigInt QR")
        return valid_results[0]

    return None


# ─────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────



def convert_qr_to_list(qr_result):
    if not qr_result.get("success"):
        return []

    data = qr_result["data"]
    fmt = data.get("format")

    qr_list = []

    # ================= XML =================
    if fmt == "xml":
        qr_list = [
            data.get("uid"),
            data.get("name"),
            data.get("gender"),
            data.get("yob") or data.get("dob"),
            data.get("co"),
            data.get("house"),
            data.get("street"),
            data.get("loc"),
            data.get("vtc"),
            data.get("po"),
            data.get("dist"),
            data.get("subdist"),
            data.get("state"),
            data.get("pc"),
        ]

    # ================= BIGINT (UPDATED ✅) =================
    elif fmt == "bigint":
        fields = data.get("qr_values", [])

        if len(fields) >= 6:
            qr_list = [
                fields[2],   # UID
                fields[3],   # Name
                fields[4],   # DOB
                fields[5],   # Gender
                fields[6],   # C/O

                # Address parts (keep separate 🔥)
                fields[7] if len(fields) > 7 else None,
                fields[8] if len(fields) > 8 else None,
                fields[9] if len(fields) > 9 else None,
                fields[10] if len(fields) > 10 else None,

                fields[11] if len(fields) > 11 else None,  # PIN
                fields[12] if len(fields) > 12 else None,
                fields[13] if len(fields) > 13 else None,
                fields[14] if len(fields) > 14 else None,

                fields[17] if len(fields) > 17 else None,  # masked UID
            ]

    # ================= CLEAN =================
    cleaned = []
    for x in qr_list:
        if not x:
            continue

        x = str(x).strip()

        # remove garbage
        if len(x) < 2:
            continue
        if any(ord(c) < 32 for c in x):
            continue

        cleaned.append(x)

    return cleaned

def qr_data_extract(results):
    best_qr = select_best_qr(results)

    print("\n================ FINAL QR =================")

    if best_qr:
        print("✅ Final QR Data:")
        print(best_qr)

        # 🔥 Extract qr_values for your OCR pipeline
        data = best_qr["data"]

        if data["format"] == "xml":
            qr_values = list(data.values())

        elif data["format"] == "bigint":
            qr_values = clean_qr_list(data["qr_values"])

        else:
            qr_values = []

        print("\n📋 QR VALUES FOR MATCHING:")
        print(qr_values)

    else:
        print("❌ No valid QR found")
        return []
    best_qr_list = convert_qr_to_list(qr_result=best_qr)
    print(best_qr_list)
    return best_qr_list
