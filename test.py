# threading_main.py

import threading
import queue
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
# from c.bot_telegram import TelegramNotificationBot
import asyncio
import msvcrt  # For detecting keypresses on Windows

# Initialize constants and logging
var = Const()

def monitor_directory(directory, queue_embeddings, stop_event, logger):
    """
    Monitors directory for changes in number of files/folders using threading.
    """
    path_logs = "./logs/directory_monitor"
    os.makedirs(path_logs, exist_ok=True)
    file_name = os.path.join(path_logs, "logs_directory_changes.log")  # Ensure '.log' extension
    # log_obj = Logger_Days(file_name)  # Removed due to centralized logging

    initial_folders, initial_files = count_directories_and_files(directory)
    logger.info(f"Initial state - Folders: {initial_folders}, Files: {initial_files}")

    while not stop_event.is_set():
        current_folders, current_files = count_directories_and_files(directory)
        
        if initial_folders != current_folders or initial_files != current_files:
            logger.info("Directory change detected!")
            logger.info(f"Previous state - Folders: {initial_folders}, Files: {initial_files}")
            logger.info(f"Current state - Folders: {current_folders}, Files: {current_files}")

            try:
                logger.info("Starting model reload and target building process...")
                
                detector, recognizer = load_model()
                logger.info("Model loaded successfully")
                
                targets = build_targets(detector, recognizer, directory)
                logger.info(f"Built targets successfully. Total targets: {len(targets)}")
                
                # Add new targets to queue
                queue_embeddings.put(targets)
                logger.info("New targets added to queue")

                # Release memory
                del detector, recognizer
                torch.cuda.empty_cache()
                logger.info("GPU memory cleared")

            except Exception as e:
                logger.error(f"Error in embedding update process: {str(e)}")
            
            # Update initial state
            initial_folders, initial_files = current_folders, current_files
        
        # Sleep to prevent high CPU usage
        time.sleep(5)

def process_changes(queue_embeddings, queue_faces, link_camera, name_camera, logger, stop_event):
    """
    Main processing function using threading
    """
    path_logs = os.path.join("./logs", str(name_camera))
    os.makedirs(path_logs, exist_ok=True)
    file_name = os.path.join(path_logs, "logs_original.log")
    # log_obj = Logger_Days(file_name)  # Removed due to centralized logging

    collection = connect_to_mongo(logger)
    
    detector, recognizer = load_model()
    targets = build_targets(detector, recognizer, var.faces_dir)
    colors = {name: (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) 
             for _, name in targets}

    cap = None
    last_connection_check = time.time()
    connection_check_interval = 60  # Check connection every 60 seconds

    while not stop_event.is_set():
        # Check and establish camera connection
        current_time = time.time()
        if cap is None or (current_time - last_connection_check >= connection_check_interval):
            if cap is not None:
                if not check_camera_connection(cap):
                    logger.info("Lost camera connection - Attempting to reconnect...")
                    cap.release()
                    cap = None
                
            if cap is None:
                cap = connect_camera(link_camera, logger)
                if cap is None:
                    logger.info("Cannot connect to camera - Will retry in 5 seconds:")
                    time.sleep(5)
                    continue
            last_connection_check = current_time

        # Read and process frame
        ret, frame = cap.read()
        if not ret:
            logger.info("Cannot read frame from camera:")
            cap.release()
            cap = None
            continue

        # Update targets from queue
        try:
            if not queue_embeddings.empty():
                logger.info("---Number of files in directory has changed.---")
                logger.info("---UPDATE TARGETS EMBEDDINGS---")
                targets = queue_embeddings.get_nowait()
        except queue.Empty:
            pass

        # Process frame
        try:
            processed_frame = frame_processor(
                frame, detector, recognizer, targets, 
                colors, collection, var, name_camera, logger, path_logs, queue_faces
            )
        except Exception as e:
            error_msg = f"Error processing image frame: {str(e)}"
            logger.error(error_msg)
            processed_frame = frame  # Fallback to original frame in case of error

        # Display the processed frame
        cv2.imshow(f"Recognition - {name_camera}", processed_frame)

        # Handle OpenCV window events and check for 'q' keypress in OpenCV window
        if cv2.waitKey(1) & 0xFF == ord('q'):
            logger.info("Exit signal received from OpenCV window. Shutting down...")
            stop_event.set()
            break

        # Small sleep to prevent high CPU usage
        time.sleep(0.01)

    # Release camera and destroy OpenCV windows when stopping
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()

def keyboard_listener(stop_event):
    """
    Listens for the 'q' keypress to signal threads to stop.
    """
    print("Press 'q' to exit the application.")
    while not stop_event.is_set():
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key.lower() == b'q':
                print("Exit signal received. Shutting down...")
                stop_event.set()
        time.sleep(0.1)  # Slight delay to prevent high CPU usage

# def run_telegram_bot(queue_faces):
#     """
#     Telegram bot running in a separate thread
#     """
#     # ... existing Telegram bot code ...
#     pass

def main():
    # Setup centralized logging
    log_file = os.path.join("./logs", "app.log")
    logger = Logger_Days(log_file)  # Initialize Logger_Days with UTF-8 encoding
    
    # Assign necessary attributes
    link_camera_01, path_to_face = var.source, var.faces_dir  # Ensure var.source is set correctly
    
    # Create queues for inter-thread communication
    queue_embeddings = queue.Queue()
    queue_faces = queue.Queue()

    # Create a stop event for graceful shutdown
    stop_event = threading.Event()

    # Create and start threads
    monitor_thread = threading.Thread(
        target=monitor_directory, 
        args=(path_to_face, queue_embeddings, stop_event, logger), 
        daemon=True,
        name='MonitorThread'  # Optional: Assign a name for easier debugging
    )
    
    camera_01_thread = threading.Thread(
        target=process_changes, 
        args=(queue_embeddings, queue_faces, link_camera_01, "cam01", logger, stop_event), 
        daemon=True,
        name='Camera01Thread'  # Optional: Assign a name for easier debugging
    )
    
    keyboard_thread = threading.Thread(
        target=keyboard_listener, 
        args=(stop_event,), 
        daemon=True,
        name='KeyboardListenerThread'
    )
    
    # If you decide to use the Telegram bot in the future, uncomment and adjust accordingly
    # telegram_thread = threading.Thread(
    #     target=run_telegram_bot, 
    #     args=(queue_faces,), 
    #     daemon=True,
    #     name='TelegramBotThread'  # Optional: Assign a name for easier debugging
    # )

    # Start the threads
    monitor_thread.start()
    camera_01_thread.start()
    keyboard_thread.start()
    # telegram_thread.start()

    logger.info("Application started. Press 'q' to exit.")
    print("Application started. Press 'q' to exit.")

    # Keep the main program running until stop_event is set
    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Stopping threads...")
        stop_event.set()
    
    # Wait for threads to finish
    monitor_thread.join()
    camera_01_thread.join()
    keyboard_thread.join()
    # telegram_thread.join()

    logger.info("Application has been terminated gracefully.")
    print("Application has been terminated gracefully.")

if __name__ == "__main__":
    main()
