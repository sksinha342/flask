import os
import uuid
import re
import qrcode
from flask import render_template, request, url_for

page_title = "Q Code Generator"
page_description = "Text, Call or WhatsApp — scan karke turant action (call/chat) start ho jaye."
image_path = "/static/qr.jpg"  # homepage card thumbnail (optional)

# directory to save temporary QR images
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'Data')
os.makedirs(DATA_DIR, exist_ok=True)

def sanitize_number(raw):
    # keep only digits and leading + if present
    raw = raw.strip()
    plus = '+' if raw.startswith('+') else ''
    digits = re.sub(r'\D', '', raw)
    return plus + digits if plus else digits

def make_qr_payload(mode, text, number, wa_message):
    """
    mode: 'text' | 'call' | 'whatsapp'
    return: payload string to encode into QR
    """
    if mode == 'text':
        return text
    elif mode == 'call':
        # tel: link (include + if user added)
        num = sanitize_number(number)
        # ensure tel: includes plus if originally provided
        if num.startswith('+'):
            return f"tel:{num}"
        else:
            return f"tel:+{num}" if num else ''
    elif mode == 'whatsapp':
        # whatsapp wa.me link requires country code + number without plus
        num = sanitize_number(number)
        num_digits = num.lstrip('+')
        msg = wa_message or ''
        from urllib.parse import quote
        qmsg = quote(msg)
        return f"https://wa.me/{num_digits}?text={qmsg}"
    else:
        return text

def clear_old_qr():
    # optionally keep, but we serve+delete on access; still we can prune old files
    for fname in os.listdir(DATA_DIR):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            path = os.path.join(DATA_DIR, fname)
            try:
                # delete files older than 1 day (optional), or delete all
                os.remove(path)
            except:
                pass

def render_page():
    # Handles GET and POST via the global Flask request object
    qr_url = None
    message = None

    if request.method == 'POST':
        mode = request.form.get('mode', 'text')
        text = request.form.get('text', '').strip()
        number = request.form.get('number', '').strip()
        wa_message = request.form.get('wa_message', '').strip()

        # prepare payload
        payload = make_qr_payload(mode, text, number, wa_message)
        if not payload:
            message = "Invalid input — please provide required details."
        else:
            # optional: clear_old_qr()  # keep or remove
            # create QR image
            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # unique filename
            fname = f"qr_{uuid.uuid4().hex[:12]}.jpg"
            save_path = os.path.join(DATA_DIR, fname)
            try:
                img.save(save_path, format='JPEG', quality=90)
                # set URL to special endpoint that serves+deletes the file on access
                qr_url = url_for('serve_temp_qr', filename=fname)
            except Exception as e:
                message = f"Error saving QR: {e}"

    # render template (template file must exist under templates/qr.html)
    return render_template('qr.html', qr_url=qr_url, message=message)