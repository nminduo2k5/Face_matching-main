# c/cConst.py

import os

class Const:
    det_weight = './weights/det_10g.onnx'
    rec_weight = "./weights/w600k_r50.onnx"
    similarity_thresh = 0.4 #reg #0.47
    confidence_thresh = 0.35 #det #0.7
    faces_dir = "./faces5/"
    # If you switch back to camera input in the future, uncomment and adjust the source
    # source = "rtsp://admin:ZSolution@2024@192.168.0.22:554/streaming/channels/101/"
    #source = 0  #cam
    input_images_dir = "./input_images/"
    output_images_dir = "./output_images/"
    max_num = 0
    max_frame = 3
    
    # MongoDB configuration
    connection_string = "mongodb://obdadmin:zW7c0pw22NnzFLDqulvrbQbIiuSPWWb@chamcong.opms.tech:27257/AttOBD?retryWrites=true&w=majority&readPreference=secondaryPreferred&maxStalenessSeconds=120"
    client = 'AttOBD'
    db = 'MccAttLog' 

   