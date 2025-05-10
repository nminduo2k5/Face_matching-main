import os
import cv2
import random
import warnings
import argparse
import logging
import numpy as np

from typing import Union, List, Tuple
from models import SCRFD, ArcFace
from utils.helpers import compute_similarity, draw_bbox_info, draw_bbox
import json
import os
import time
from datetime import datetime, timezone
from utils.utils import remove_expired_names
from service.db_processor import log_to_mongo_if_not_in_json


def is_bbox_significant(frame: np.ndarray, bbox: np.ndarray):
    
    # Kích thước của khung hình
    frame_height, frame_width = frame.shape[:2]

    # Tính diện tích của khung hình
    frame_area = frame_height * frame_width
    # Tách các giá trị từ bbox
    x_min, y_min, x_max, y_max = map(int, bbox)
    
    # Tính diện tích của bounding box
    bbox_width = x_max - x_min
    bbox_height = y_max - y_min
    bbox_area = bbox_width * bbox_height
    
    # Tính tỷ lệ diện tích
    area_ratio = (bbox_area / frame_area)*100
    
    # Kiểm tra xem tỷ lệ diện tích có vượt quá ngưỡng hay không
    return area_ratio

#Cập nhật hàm frame_processor
def frame_processor(
    frame: np.ndarray,
    detector: SCRFD,
    recognizer: ArcFace,
    targets: List[Tuple[np.ndarray, str]],
    colors: dict,
    collection,
    var,
    name_camera,
    log_obj,
    path_logs,
    queue_faces,
    detected_faces=None
) -> np.ndarray:
    # Xóa các tên đã quá hạn 1 phút trước khi xử lý khung hình
    remove_expired_names(path_logs)

    bboxes, kpss = detector.detect(frame, var.max_num)
    
    # Initialize counters
    total_faces = len(bboxes)
    recognized_faces = 0

    for bbox, kps in zip(bboxes, kpss):
        *bbox, conf_score = bbox.astype(np.int32)
        
        if True:
            embedding = recognizer(frame, kps)

            max_similarity = 0
            best_match_name = "Unknown"
            for target, name in targets:
                similarity = compute_similarity(target, embedding)
                if similarity > max_similarity and similarity > var.similarity_thresh:
                    max_similarity = similarity
                    best_match_name = name
            if detected_faces is not None:
                detected_faces.append({"Name": best_match_name, "Confidence": max_similarity})

            current_datetime = datetime.now(timezone.utc)
            if best_match_name != "Unknown":
                recognized_faces += 1
                print(f"Nhận diện: {best_match_name} vào ngày {current_datetime}")
                log_obj.info(f"Nhận diện: {best_match_name} vào ngày {current_datetime}")
                color = colors[best_match_name]
                draw_bbox_info(frame, bbox, similarity=max_similarity, name=best_match_name, color=color)

                try:
                    log_to_mongo_if_not_in_json(best_match_name, current_datetime, collection, name_camera, path_logs, queue_faces)
                except Exception as e:
                    error_msg = f"Lỗi khi xử lý log_to_mongo_if_not_in_json: {str(e)}"
                    print(error_msg)
    
    # Calculate recognition rate
    recognition_rate = (recognized_faces / total_faces) * 100 if total_faces > 0 else 0
    print(f"Số mặt nhận diện: {recognized_faces}, Tổng số mặt: {total_faces}, Tỉ lệ nhận diện: {recognition_rate:.2f}%")
    log_obj.info(f"Số mặt nhận diện: {recognized_faces}, Tổng số mặt: {total_faces}, Tỉ lệ nhận diện: {recognition_rate:.2f}%")
    
    return frame
