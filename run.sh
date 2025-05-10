# nohup python3 upload_file.py > ./logs/logs_upload_file.txt 2>&1 & echo $! > ./logs/run_upload.pid
# nohup python3 run.py > ./logs/logs.txt 2>&1 & echo $! > ./logs/run.pid
nohup python3 app.py >/dev/null 2>&1 & echo $! > run.pid
