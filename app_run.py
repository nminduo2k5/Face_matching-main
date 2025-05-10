<<<<<<< HEAD
import multiprocessing
import time
import os
import cv2
import random
import torch
from pymongo import MongoClient
from load_model import load_model
from c.cConst import Const
from service.processing import build_targets
from service.frame_processor import frame_processor

from utils.save_log import Logger_Days, Logger_maxBytes
from utils.utils import count_directories_and_files
from utils.process_db import connect_to_mongo
from utils.process_camera import check_camera_connection, connect_camera
from c.bot_telegram import TelegramNotificationBot
import asyncio

# Initialize constants and logging
var = Const()

# def monitor_directory(directory, queue):
#     """
#     Monitors directory for changes in number of files/folders.
#     When changes detected, reloads model and updates targets.
#     """
#     initial_folders, initial_files = count_directories_and_files(directory)
#     while True:
#         current_folders, current_files = count_directories_and_files(directory)
#         if initial_folders != current_folders or initial_files != current_files:
#             detector, recognizer = load_model()
#             targets = build_targets(detector, recognizer, var.faces_dir)
#             queue.put(targets)
#             initial_folders, initial_files = current_folders, current_files
#             del detector, recognizer
#             torch.cuda.empty_cache()

def monitor_directory(directory, queue):
    """
    Monitors directory for changes in number of files/folders.
    When changes detected, reloads model and updates targets.
    """
    # Tạo logger riêng cho monitor directory
    path_logs = "./logs/directory_monitor"
    if not os.path.exists(path_logs):
        os.makedirs(path_logs)
    file_name = path_logs + "/logs_directory_changes"
    log_obj = Logger_Days(file_name)

    initial_folders, initial_files = count_directories_and_files(directory)
    log_obj.info(f"Initial state - Folders: {initial_folders}, Files: {initial_files}")

    while True:
        current_folders, current_files = count_directories_and_files(directory)
        
        if initial_folders != current_folders or initial_files != current_files:
            log_obj.info(f"Directory change detected!")
            log_obj.info(f"Previous state - Folders: {initial_folders}, Files: {initial_files}")
            log_obj.info(f"Current state - Folders: {current_folders}, Files: {current_files}")

            try:
                # Bắt đầu quá trình cập nhật embedding
                log_obj.info("Starting model reload and target building process...")
                
                detector, recognizer = load_model()
                log_obj.info("Model loaded successfully")
                
                targets = build_targets(detector, recognizer, directory)
                log_obj.info(f"Built targets successfully. Total targets: {len(targets)}")
                
                # Đưa targets mới vào queue
                queue.put(targets)
                log_obj.info("New targets added to queue")

                # Giải phóng bộ nhớ
                del detector, recognizer
                torch.cuda.empty_cache()
                log_obj.info("GPU memory cleared")

            except Exception as e:
                log_obj.info(f"Error in embedding update process: {str(e)}")
            
            # Cập nhật trạng thái ban đầu
            initial_folders, initial_files = current_folders, current_files

def process_changes(queue_embeddings, queue_faces, link_camera, name_camera):
    """
    Main processing function that:
    1. Connects to MongoDB
    2. Loads face detection/recognition models
    3. Processes video frames
    4. Updates targets when directory changes
    5. Monitors camera connection and attempts reconnection
    """
    path_logs = "./logs/" + str(name_camera)
    if not os.path.exists(path_logs):
        os.makedirs(path_logs)
    file_name = path_logs + "/logs_original"
    log_obj = Logger_Days(file_name)

    collection = connect_to_mongo(log_obj)
    
    detector, recognizer = load_model()
    targets = build_targets(detector, recognizer, var.faces_dir)
    colors = {name: (random.randint(0, 256), random.randint(0, 256), random.randint(0, 256)) 
             for _, name in targets}

    cap = None
    last_connection_check = time.time()
    connection_check_interval = 60  # Kiểm tra kết nối mỗi 60 giây

    while True:
        # Kiểm tra và thiết lập kết nối camera
        current_time = time.time()
        if cap is None or (current_time - last_connection_check >= connection_check_interval):
            if cap is not None:
                if not check_camera_connection(cap):
                    log_obj.info("Mất kết nối camera - Đang thử kết nối lại...")
                    cap.release()
                    cap = None
                
            if cap is None:
                cap = connect_camera(link_camera, log_obj)
                if cap is None:
                    log_obj.info("Không thể kết nối camera - Sẽ thử lại sau 5 giây:")
                    time.sleep(5)
                    continue
            last_connection_check = current_time

        # Đọc và xử lý frame
        ret, frame = cap.read()
        if not ret:
            log_obj.info("Không thể đọc frame từ camera:")
            cap.release()
            cap = None
            continue

        # Xử lý cập nhật targets từ queue
        if not queue_embeddings.empty():
            print(f"Số lượng file trong thư mục đã thay đổi.")
            log_obj.info("---Số lượng file trong thư mục đã thay đổi.---")
            log_obj.info("---UPDATE TARGETS EMBEDDINGS---")
            targets = queue_embeddings.get()

        # Xử lý frame
        frame_count = getattr(process_changes, 'frame_count', 0)
        if frame_count % var.max_frame == 0:
            try:
                frame = frame_processor(frame, detector, recognizer, targets, 
                                     colors, collection, var, name_camera, log_obj, path_logs, queue_faces)
            except Exception as e:
                error_msg = f"Lỗi khi xử lý frame hình ảnh: {str(e)}"
                print(error_msg)
                log_obj.info(error_msg)

        frame_count = (frame_count + 1) % 1000
        process_changes.frame_count = frame_count

async def run_telegram_bot(queue_faces):
    path_logs = "./logs"
    if not os.path.exists(path_logs):
        os.makedirs(path_logs)
    file_name = path_logs + "/logs_telegram"
    log_obj = Logger_Days(file_name)

    try:
        # Khởi tạo bot với token của bạn
        telegram_bot = TelegramNotificationBot('')
        
        log_obj.info("Starting Telegram bot...")
        
        # Khởi động bot và bắt đầu polling
        await telegram_bot.application.initialize()
        await telegram_bot.application.start()
        await telegram_bot.application.updater.start_polling()
        log_obj.info("Bot started successfully")
        
        # Xử lý queue trong vòng lặp bất đồng bộ
        while True:
            try:
                information_face = await asyncio.get_event_loop().run_in_executor(None, queue_faces.get)
                log_obj.info(f"Thông tin Face: {information_face}")
                
                best_match_name, formatted_time, name_camera = information_face
                success = await telegram_bot.send_recognition_notification(best_match_name, formatted_time)
                
                if success:
                    log_obj.info("Đã gửi cho nhân viên bằng Telegram thành công")
                else:
                    log_obj.info("Không thể gửi thông báo qua Telegram")
                
            except Exception as e:
                error_msg = f"Error processing notification: {str(e)}"
                log_obj.info(error_msg)
                
    except Exception as e:
        error_msg = f"Error initializing Telegram bot: {str(e)}"
        log_obj.info(error_msg)
    finally:
        # Cleanup
        log_obj.info("Stopping bot...")
        if telegram_bot:
            await telegram_bot.application.updater.stop()
            await telegram_bot.application.stop()
            await telegram_bot.application.shutdown()
        log_obj.info("Bot stopped")

def process_telegrams(queue_faces):
    asyncio.run(run_telegram_bot(queue_faces))

if __name__ == "__main__":
    link_camera_01, link_camera_02, path_to_face = var.source, var.source1, var.faces_dir
    # Create queue for inter-process communication
    queue_embeddings = multiprocessing.Queue()
    queue_faces = multiprocessing.Queue()

    # Create and start monitoring and processing processes
    monitor_process = multiprocessing.Process(target=monitor_directory, 
                                            args=(path_to_face, queue_embeddings))
    process_camera_01 = multiprocessing.Process(target=process_changes, 
                                            args=(queue_embeddings, queue_faces, link_camera_01, "cam01"))
    process_camera_02 = multiprocessing.Process(target=process_changes, 
                                            args=(queue_embeddings, queue_faces, link_camera_02, "cam02"))
    process_telegram = multiprocessing.Process(target=process_telegrams, 
                                            args=(queue_faces,))

    monitor_process.start()
    process_camera_01.start()
    process_camera_02.start()
    process_telegram.start()

    monitor_process.join()
    process_camera_01.join()
    process_camera_02.join()
=======
import multiprocessing
import time
import os
import cv2
import random
import torch
from pymongo import MongoClient
from load_model import load_model
from c.cConst import Const
from service.processing import build_targets
from service.frame_processor import frame_processor

from utils.save_log import Logger_Days, Logger_maxBytes
from utils.utils import count_directories_and_files
from utils.process_db import connect_to_mongo
from utils.process_camera import check_camera_connection, connect_camera
from c.bot_telegram import TelegramNotificationBot
import asyncio

# Initialize constants and logging
var = Const()

# def monitor_directory(directory, queue):
#     """
#     Monitors directory for changes in number of files/folders.
#     When changes detected, reloads model and updates targets.
#     """
#     initial_folders, initial_files = count_directories_and_files(directory)
#     while True:
#         current_folders, current_files = count_directories_and_files(directory)
#         if initial_folders != current_folders or initial_files != current_files:
#             detector, recognizer = load_model()
#             targets = build_targets(detector, recognizer, var.faces_dir)
#             queue.put(targets)
#             initial_folders, initial_files = current_folders, current_files
#             del detector, recognizer
#             torch.cuda.empty_cache()

def monitor_directory(directory, queue):
    """
    Monitors directory for changes in number of files/folders.
    When changes detected, reloads model and updates targets.
    """
    # Tạo logger riêng cho monitor directory
    path_logs = "./logs/directory_monitor"
    if not os.path.exists(path_logs):
        os.makedirs(path_logs)
    file_name = path_logs + "/logs_directory_changes"
    log_obj = Logger_Days(file_name)

    initial_folders, initial_files = count_directories_and_files(directory)
    log_obj.info(f"Initial state - Folders: {initial_folders}, Files: {initial_files}")

    while True:
        current_folders, current_files = count_directories_and_files(directory)
        
        if initial_folders != current_folders or initial_files != current_files:
            log_obj.info(f"Directory change detected!")
            log_obj.info(f"Previous state - Folders: {initial_folders}, Files: {initial_files}")
            log_obj.info(f"Current state - Folders: {current_folders}, Files: {current_files}")

            try:
                # Bắt đầu quá trình cập nhật embedding
                log_obj.info("Starting model reload and target building process...")
                
                detector, recognizer = load_model()
                log_obj.info("Model loaded successfully")
                
                targets = build_targets(detector, recognizer, directory)
                log_obj.info(f"Built targets successfully. Total targets: {len(targets)}")
                
                # Đưa targets mới vào queue
                queue.put(targets)
                log_obj.info("New targets added to queue")

                # Giải phóng bộ nhớ
                del detector, recognizer
                torch.cuda.empty_cache()
                log_obj.info("GPU memory cleared")

            except Exception as e:
                log_obj.info(f"Error in embedding update process: {str(e)}")
            
            # Cập nhật trạng thái ban đầu
            initial_folders, initial_files = current_folders, current_files

def process_changes(queue_embeddings, queue_faces, link_camera, name_camera):
    """
    Main processing function that:
    1. Connects to MongoDB
    2. Loads face detection/recognition models
    3. Processes video frames
    4. Updates targets when directory changes
    5. Monitors camera connection and attempts reconnection
    """
    path_logs = "./logs/" + str(name_camera)
    if not os.path.exists(path_logs):
        os.makedirs(path_logs)
    file_name = path_logs + "/logs_original"
    log_obj = Logger_Days(file_name)

    collection = connect_to_mongo(log_obj)
    
    detector, recognizer = load_model()
    targets = build_targets(detector, recognizer, var.faces_dir)
    colors = {name: (random.randint(0, 256), random.randint(0, 256), random.randint(0, 256)) 
             for _, name in targets}

    cap = None
    last_connection_check = time.time()
    connection_check_interval = 60  # Kiểm tra kết nối mỗi 60 giây

    while True:
        # Kiểm tra và thiết lập kết nối camera
        current_time = time.time()
        if cap is None or (current_time - last_connection_check >= connection_check_interval):
            if cap is not None:
                if not check_camera_connection(cap):
                    log_obj.info("Mất kết nối camera - Đang thử kết nối lại...")
                    cap.release()
                    cap = None
                
            if cap is None:
                cap = connect_camera(link_camera, log_obj)
                if cap is None:
                    log_obj.info("Không thể kết nối camera - Sẽ thử lại sau 5 giây:")
                    time.sleep(5)
                    continue
            last_connection_check = current_time

        # Đọc và xử lý frame
        ret, frame = cap.read()
        if not ret:
            log_obj.info("Không thể đọc frame từ camera:")
            cap.release()
            cap = None
            continue

        # Xử lý cập nhật targets từ queue
        if not queue_embeddings.empty():
            print(f"Số lượng file trong thư mục đã thay đổi.")
            log_obj.info("---Số lượng file trong thư mục đã thay đổi.---")
            log_obj.info("---UPDATE TARGETS EMBEDDINGS---")
            targets = queue_embeddings.get()

        # Xử lý frame
        frame_count = getattr(process_changes, 'frame_count', 0)
        if frame_count % var.max_frame == 0:
            try:
                frame = frame_processor(frame, detector, recognizer, targets, 
                                     colors, collection, var, name_camera, log_obj, path_logs, queue_faces)
            except Exception as e:
                error_msg = f"Lỗi khi xử lý frame hình ảnh: {str(e)}"
                print(error_msg)
                log_obj.info(error_msg)

        frame_count = (frame_count + 1) % 1000
        process_changes.frame_count = frame_count

async def run_telegram_bot(queue_faces):
    path_logs = "./logs"
    if not os.path.exists(path_logs):
        os.makedirs(path_logs)
    file_name = path_logs + "/logs_telegram"
    log_obj = Logger_Days(file_name)

    try:
        # Khởi tạo bot với token của bạn
        telegram_bot = TelegramNotificationBot('')
        
        log_obj.info("Starting Telegram bot...")
        
        # Khởi động bot và bắt đầu polling
        await telegram_bot.application.initialize()
        await telegram_bot.application.start()
        await telegram_bot.application.updater.start_polling()
        log_obj.info("Bot started successfully")
        
        # Xử lý queue trong vòng lặp bất đồng bộ
        while True:
            try:
                information_face = await asyncio.get_event_loop().run_in_executor(None, queue_faces.get)
                log_obj.info(f"Thông tin Face: {information_face}")
                
                best_match_name, formatted_time, name_camera = information_face
                success = await telegram_bot.send_recognition_notification(best_match_name, formatted_time)
                
                if success:
                    log_obj.info("Đã gửi cho nhân viên bằng Telegram thành công")
                else:
                    log_obj.info("Không thể gửi thông báo qua Telegram")
                
            except Exception as e:
                error_msg = f"Error processing notification: {str(e)}"
                log_obj.info(error_msg)
                
    except Exception as e:
        error_msg = f"Error initializing Telegram bot: {str(e)}"
        log_obj.info(error_msg)
    finally:
        # Cleanup
        log_obj.info("Stopping bot...")
        if telegram_bot:
            await telegram_bot.application.updater.stop()
            await telegram_bot.application.stop()
            await telegram_bot.application.shutdown()
        log_obj.info("Bot stopped")

def process_telegrams(queue_faces):
    asyncio.run(run_telegram_bot(queue_faces))

if __name__ == "__main__":
    link_camera_01, link_camera_02, path_to_face = var.source, var.source1, var.faces_dir
    # Create queue for inter-process communication
    queue_embeddings = multiprocessing.Queue()
    queue_faces = multiprocessing.Queue()

    # Create and start monitoring and processing processes
    monitor_process = multiprocessing.Process(target=monitor_directory, 
                                            args=(path_to_face, queue_embeddings))
    process_camera_01 = multiprocessing.Process(target=process_changes, 
                                            args=(queue_embeddings, queue_faces, link_camera_01, "cam01"))
    process_camera_02 = multiprocessing.Process(target=process_changes, 
                                            args=(queue_embeddings, queue_faces, link_camera_02, "cam02"))
    process_telegram = multiprocessing.Process(target=process_telegrams, 
                                            args=(queue_faces,))

    monitor_process.start()
    process_camera_01.start()
    process_camera_02.start()
    process_telegram.start()

    monitor_process.join()
    process_camera_01.join()
    process_camera_02.join()
>>>>>>> 5d431b77047d5b9927032e46055144c35f132e21
    process_telegram.join()