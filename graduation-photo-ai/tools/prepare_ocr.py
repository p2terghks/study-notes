"""Download official EasyOCR weights into this project's .models folder."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from graduation.ocr import get_reader
if __name__=='__main__':
    get_reader()
    print('한국어·영어 OCR 모델 준비 완료')
