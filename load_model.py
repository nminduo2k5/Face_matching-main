<<<<<<< HEAD
import torch
import onnxruntime
from c.cConst import Const
from models import SCRFD, ArcFace

var = Const()

def load_model():
    # Sử dụng GPU với ONNX Runtime
    detector_session = onnxruntime.InferenceSession(var.det_weight, providers=['CUDAExecutionProvider'])
    recognizer_session = onnxruntime.InferenceSession(var.rec_weight, providers=['CUDAExecutionProvider'])

    detector = SCRFD(session=detector_session, model_path=var.det_weight, input_size=(640, 640), conf_thres=var.confidence_thresh)
    recognizer = ArcFace(session=recognizer_session)
=======
import torch
import onnxruntime
from c.cConst import Const
from models import SCRFD, ArcFace

var = Const()

def load_model():
    # Sử dụng GPU với ONNX Runtime
    detector_session = onnxruntime.InferenceSession(var.det_weight, providers=['CUDAExecutionProvider'])
    recognizer_session = onnxruntime.InferenceSession(var.rec_weight, providers=['CUDAExecutionProvider'])

    detector = SCRFD(session=detector_session, model_path=var.det_weight, input_size=(640, 640), conf_thres=var.confidence_thresh)
    recognizer = ArcFace(session=recognizer_session)
>>>>>>> 5d431b77047d5b9927032e46055144c35f132e21
    return detector, recognizer