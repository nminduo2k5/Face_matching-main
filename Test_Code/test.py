import json
from pymongo import MongoClient
from datetime import datetime, timezone

# Kết nối tới MongoDB
connection_string = "mongodb://obdadmin:zW7c0pw22NnzFLDqulvrbQbIiuSPWWb@chamcong.opms.tech:27257/AttOBD?retryWrites=true&w=majority&readPreference=secondaryPreferred&maxStalenessSeconds=120"
client = MongoClient(connection_string)

# Chọn database và collection
db = client['AttOBD']
collection = db['MccAttLog']

# Hàm để lấy dữ liệu từ MongoDB và lưu vào file JSON
def export_to_json(output_file):
    try:
        # Lấy toàn bộ dữ liệu từ collection
        data = list(collection.find())

        # Xử lý dữ liệu (nếu cần) - chuyển ObjectId và datetime về kiểu string
        for record in data:
            record['_id'] = str(record['_id'])  # Chuyển ObjectId thành string
            for key, value in record.items():
                if isinstance(value, datetime):
                    record[key] = value.isoformat()  # Chuyển datetime thành ISO format

        # Ghi dữ liệu vào file JSON
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        print(f"Dữ liệu đã được lưu vào file {output_file}")
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

# Gọi hàm xuất dữ liệu
export_to_json('output.json')