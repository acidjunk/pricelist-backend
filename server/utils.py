import qrcode


def generate_qr_image(url="www.google.com"):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)

    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    return img
