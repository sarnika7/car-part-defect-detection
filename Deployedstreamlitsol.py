import os
import json
import streamlit as st
from PIL import Image
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.config import get_cfg
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
import cv2
import matplotlib.pyplot as plt
from detectron2.utils.visualizer import Visualizer
import torch
import numpy as np
# Define the dataset registration function
def get_car_parts_dicts(img_dir, ann_dir):
    category_mapping = {
        "Dent": 1,
        "Scratch": 2,
        "Broken part": 3,
        "Paint chip": 4,
        "Missing part": 5,
        "Flaking": 6,
        "Corrosion": 7,
        "Cracked": 8
    }
    dataset_dicts = []
    for idx, image_filename in enumerate(os.listdir(img_dir)):
        if not image_filename.endswith(".jpg") and not image_filename.endswith(".png"):
            continue

        image_path = os.path.join(img_dir, image_filename)
        annotation_path = os.path.join(ann_dir, image_filename + ".json")
        
        with Image.open(image_path) as img:
            width, height = img.size
        
        record = {
            "file_name": image_path,
            "image_id": idx,
            "height": height,
            "width": width,
            "annotations": []
        }
        
        with open(annotation_path) as f:
            objs = json.load(f)["objects"]

        for obj in objs:
            px = [point[0] for point in obj["points"]["exterior"]]
            py = [point[1] for point in obj["points"]["exterior"]]
            poly = [(x, y) for x, y in zip(px, py)]
            poly = [p for x in poly for p in x]

            category_id = category_mapping.get(obj["classTitle"], -1)
            if category_id == -1:
                continue
            
            bbox = [min(px), min(py), max(px) - min(px), max(py) - min(py)]
            
            record["annotations"].append({
                "bbox": bbox,
                "category_id": category_id,
                "segmentation": [poly],
                "area": bbox[2] * bbox[3],
                "iscrowd": 0
            })

        dataset_dicts.append(record)
    
    return dataset_dicts

# Paths to your dataset
data_dir = "D:\\Tata Tech\\File1"
images_dir = os.path.join(data_dir, "img")
annotations_dir = os.path.join(data_dir, "ann")

# Register the dataset
for d in ["train", "val"]:
    #DatasetCatalog.register("car_parts_" + d, lambda d=d: get_car_parts_dicts(images_dir, annotations_dir))
    MetadataCatalog.get("car_parts_" + d).set(thing_classes=["Dent", "Scratch", "Broken part", "Paint chip", "Missing part", "Flaking", "Corrosion", "Cracked"])

# Load config and model
cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
cfg.DATASETS.TRAIN = ("car_parts_train",)
cfg.DATASETS.TEST = ("car_parts_val",)
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 8 
cfg.MODEL.WEIGHTS = "D:\\Tata Tech\\model_final (1).pth"
cfg.MODEL.DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Create predictor
predictor = DefaultPredictor(cfg)

# Streamlit app
st.title("Car Parts Damage Detection")
st.write("Upload an image to detect car parts damage")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png"])
if uploaded_file is not None:
    # Load the uploaded image
    image = Image.open(uploaded_file)
    im = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Make predictions
    output = predictor(im)

    # Visualize original image
    st.image(image, caption='Original Image', use_column_width=True)
    
    # Draw the predictions on the test image
    v = Visualizer(im[:, :, ::-1], metadata=MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=0.5)
    out = v.draw_instance_predictions(output["instances"].to("cpu"))

    # Show the image with predictions
    st.image(out.get_image()[:, :, ::-1], caption='Predicted Image', use_column_width=True)
