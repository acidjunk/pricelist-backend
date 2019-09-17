import csv
import uuid
from typing import Union

import qrcode
from database import Price, db


def generate_qr_image(url="www.google.com"):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)

    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    return img


def import_prices(file):
    with open(file, mode="r") as csv_file_in:
        with open("prijzen_updated.csv", mode="w") as csv_file_out:
            csv_reader = csv.DictReader(csv_file_in)
            csv_writer = csv.DictWriter(csv_file_out, fieldnames=csv_reader.fieldnames)
            line_count = 0
            csv_writer.writeheader()
            for row in csv_reader:
                if row["id"]:
                    print(f"Updating {row['id']}")
                    price = Price.query.filter_by(id=row["id"]).first()
                    for key, value in row.items():
                        if key in ["half", "one", "two_five", "five", "piece", "joint"]:
                            value = convert_price_string_to_float(value)
                        if key == "internal_product_id":
                            value = int(value)
                        setattr(price, key, value)
                    db.session.add(price)
                else:
                    row["id"] = str(uuid.uuid4())
                    print(f"Adding {row['id']}")
                    price = Price(
                        id=row["id"],
                        internal_product_id=int(row["internal_product_id"]),
                        piece=convert_price_string_to_float(row["piece"]),
                        half=convert_price_string_to_float(row["half"]),
                        one=convert_price_string_to_float(row["one"]),
                        two_five=convert_price_string_to_float(row["two_five"]),
                        five=convert_price_string_to_float(row["five"]),
                        joint=convert_price_string_to_float(row["joint"]),
                    )
                    db.session.add(price)
                csv_writer.writerow({**row})
                db.session.commit()
                line_count += 1
            print(f"Processed {line_count} lines.")


def convert_price_string_to_float(price: str) -> Union[float, None]:
    print("***")
    try:
        price = price.replace(",", ".")
        return float(price)
    except ValueError:
        return None
