from pathlib import Path
from functools import lru_cache

ROOT=Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def get_reader():
    import os
    import certifi
    os.environ.setdefault('SSL_CERT_FILE',certifi.where())
    import easyocr
    import torch
    # CPU is portable and avoids unsupported MPS operators in OCR detection.
    return easyocr.Reader(['ko','en'],gpu=torch.cuda.is_available(),
        model_storage_directory=str(ROOT/'.models'),
        user_network_directory=str(ROOT/'.models'/'user_network'),verbose=False)

def recognize(image_bytes):
    import io
    import numpy as np
    from PIL import Image, ImageOps
    source = Image.open(io.BytesIO(image_bytes))
    if source.width*source.height>24_000_000:
        raise ValueError('이미지는 2,400만 화소 이하로 줄여주세요.')
    image=ImageOps.exif_transpose(source).convert('RGB')
    image.thumbnail((2600,2600))
    detections=get_reader().readtext(np.array(image),detail=1,paragraph=False)
    boxes=[]
    for box,text,confidence in detections:
        xs=[p[0] for p in box]; ys=[p[1] for p in box]
        boxes.append({'x':float(min(xs)),'y':float(sum(ys)/4),'height':float(max(ys)-min(ys)),
                      'text':text,'confidence':float(confidence)})
    groups=[]
    for item in sorted(boxes,key=lambda b:b['y']):
        target=next((g for g in groups if abs(g[0]['y']-item['y'])<=max(7,min(g[0]['height'],item['height'])*.5)),None)
        if target is None: groups.append([item])
        else: target.append(item)
    lines=[{'text':' '.join(b['text'] for b in sorted(g,key=lambda b:b['x'])),
            'confidence':min(b['confidence'] for b in g)} for g in groups]
    return lines,boxes
