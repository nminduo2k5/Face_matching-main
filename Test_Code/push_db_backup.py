import json
from pymongo import MongoClient
from datetime import datetime, timezone

# Kết nối tới MongoDB
connection_string = "mongodb+srv://f99Developer:HShpJCwpdLEDv2EE@f99.j87vx.mongodb.net/AttOBD?retryWrites=true&w=majority&readPreference=secondaryPreferred&maxStalenessSeconds=120"
client = MongoClient(connection_string)

# Chọn database và collection
db = client['AttOBD']
collection = db['MccAttLog']

# Đọc file JSON
with open('../logs/cam01/backup_db_2122_11_24.json', 'r') as file:
    data = json.load(file)

# Đẩy dữ liệu lên MongoDB
if isinstance(data, list):  # Nếu dữ liệu là một danh sách các đối tượng JSON
    collection.insert_many(data)
else:  # Nếu dữ liệu chỉ là một đối tượng JSON
    collection.insert_one(data)

print("Dữ liệu đã được đẩy thành công.")
