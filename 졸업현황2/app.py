"""Local HTML interface with JSON endpoints for OCR and graduation checks."""
import csv
import io
import json
import secrets
import threading
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, Request, jsonify, render_template, request, send_file
from itsdangerous import BadSignature, URLSafeSerializer
from werkzeug.exceptions import HTTPException
from graduation.engine import CATEGORIES, audit, parse_lines_with_review
from graduation.ocr import recognize

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'data/curriculum.json').read_text(encoding='utf-8'))
PROFILES = {p['id']: p for p in DATA['profiles']}
class MemoryRequest(Request):
    def _get_file_stream(self, total_content_length, content_type, filename=None, content_length=None):
        # Bounded uploads stay in memory, including multipart files.
        return io.BytesIO()


app = Flask(__name__)
app.request_class = MemoryRequest
app.config.update(MAX_CONTENT_LENGTH=76 * 1024 * 1024, MAX_FORM_MEMORY_SIZE=2 * 1024 * 1024)
signer = URLSafeSerializer(secrets.token_hex(32), salt='review')
ocr_lock = threading.Lock()


@app.before_request
def local_requests():
    if request.host.split(':')[0] not in {'localhost', '127.0.0.1'}:
        return jsonify(error='로컬 주소로 접속하세요.'), 400
    if request.method == 'POST':
        origin = request.headers.get('Origin')
        if request.headers.get('X-Requested-With') != 'graduation-html' or (origin and urlparse(origin).netloc != request.host):
            return jsonify(error='앱 화면에서 다시 요청하세요.'), 403


@app.after_request
def response_headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
    return response


def profile_for(value):
    if not isinstance(value, str) or value not in PROFILES:
        raise ValueError('입학연도와 트랙을 다시 선택하세요.')
    return PROFILES[value]


def candidates_response(profile, rows, rejected, raw=None):
    if len(rows) > 500:
        raise ValueError('한 번에 최대 500개 과목을 검토할 수 있습니다.')
    return jsonify(rows=rows, rejected=rejected, raw=raw or [],
                   review_token=signer.dumps({'profile': profile['id'], 'rejected': len(rejected)}))


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/api/config')
def config():
    return jsonify(profiles=DATA['profiles'], categories=CATEGORIES)


@app.get('/reference')
def reference():
    return send_file(ROOT / 'reference' / DATA['source'], as_attachment=True)


@app.post('/api/parse')
def parse():
    if not request.is_json:
        raise ValueError('JSON 입력이 필요합니다.')
    body = request.get_json()
    if not isinstance(body, dict):
        raise ValueError('잘못된 입력 형식입니다.')
    profile = profile_for(body.get('profile'))
    text = body.get('text', '')
    if not isinstance(text, str) or len(text) > 100000:
        raise ValueError('텍스트는 10만 자 이내로 입력하세요.')
    rows, rejected = parse_lines_with_review(text.splitlines(), profile)
    return candidates_response(profile, rows, rejected)


@app.post('/api/csv')
def parse_csv():
    profile = profile_for(request.form.get('profile'))
    upload = request.files.get('file')
    if not upload:
        raise ValueError('CSV 파일을 선택하세요.')
    content = upload.read(2 * 1024 * 1024 + 1)
    if len(content) > 2 * 1024 * 1024:
        raise ValueError('CSV는 2MB 이하로 올려주세요.')
    try:
        reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
        if not {'과목명', '학점', '이수구분', '성적'}.issubset(reader.fieldnames or []):
            raise ValueError('과목명·학점·이수구분·성적 열이 필요합니다.')
        rows = []
        for record in reader:
            if len(rows) >= 500:
                raise ValueError('CSV는 500행 이하로 올려주세요.')
            row = {key: (record.get(key) or '') for key in ['과목명', '학점', '이수구분', '성적']}
            row.update({'확인': False, '인식신뢰도': 1.0, '메모': 'CSV 입력'})
            rows.append(row)
    except UnicodeError:
        raise ValueError('UTF-8 형식으로 저장한 CSV를 사용하세요.') from None
    return candidates_response(profile, rows, [])


@app.post('/api/ocr')
def ocr():
    profile = profile_for(request.form.get('profile'))
    photos = request.files.getlist('photos')
    if not 1 <= len(photos) <= 5:
        raise ValueError('사진은 한 번에 1~5장 선택하세요.')
    if not ocr_lock.acquire(blocking=False):
        return jsonify(error='다른 사진을 인식 중입니다. 잠시 후 다시 시도하세요.'), 409
    try:
        rows, rejected, raw = [], [], []
        for photo in photos:
            content = photo.read(15 * 1024 * 1024 + 1)
            if len(content) > 15 * 1024 * 1024:
                raise ValueError('사진 한 장은 15MB 이하로 올려주세요.')
            from PIL import Image, UnidentifiedImageError
            try:
                image = Image.open(io.BytesIO(content))
                if image.format not in {'JPEG', 'PNG', 'WEBP'}:
                    raise ValueError('JPG·PNG·WEBP 사진만 사용할 수 있습니다.')
                image.close()
                lines, _ = recognize(content)
            except (UnidentifiedImageError, OSError):
                raise ValueError('사진을 읽을 수 없습니다. 파일을 확인하세요.') from None
            candidates, failures = parse_lines_with_review(lines, profile)
            rows.extend(candidates)
            rejected.extend(failures)
            raw.extend(lines)
        return candidates_response(profile, rows, rejected, raw)
    finally:
        ocr_lock.release()


@app.post('/api/audit')
def check():
    body = request.get_json()
    if not isinstance(body, dict):
        raise ValueError('잘못된 입력 형식입니다.')
    profile = profile_for(body.get('profile'))
    try:
        token = signer.loads(body.get('review_token', ''))
    except (BadSignature, TypeError):
        raise ValueError('입력을 다시 불러온 뒤 검토하세요.') from None
    if token.get('profile') != profile['id']:
        raise ValueError('교육과정이 바뀌었습니다. 입력을 다시 불러오세요.')
    if body.get('consent') is not True or (token['rejected'] and body.get('resolved') is not True):
        raise ValueError('원문 및 미해석 행 검토를 완료하세요.')
    rows = body.get('rows')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
        raise ValueError('검토할 과목을 1~500개 입력하세요.')
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('과목 정보 형식이 올바르지 않습니다.')
        for key in ['과목명', '이수구분', '성적']:
            if not isinstance(row.get(key), str) or len(row[key]) > 300:
                raise ValueError('과목명·구분·성적은 300자 이내 문자열로 입력하세요.')
        if not isinstance(row.get('학점'), (str, int, float)) or isinstance(row.get('학점'), bool):
            raise ValueError('학점은 숫자로 입력하세요.')
    if not any(row['과목명'].strip() for row in rows):
        raise ValueError('과목명을 입력하세요.')
    mandatory = body.get('mandatory', [])
    allowed = {c['name'] for c in profile['courses'] if c['category'] == '전공필수'}
    if not isinstance(mandatory, list) or any(not isinstance(x, str) or x not in allowed for x in mandatory):
        raise ValueError('의무 과목 선택을 확인하세요.')
    advanced = body.get('advanced', False)
    if not isinstance(advanced, bool) or (advanced and profile['optional_advanced'] is None):
        raise ValueError('이 교육과정에서는 전공심화 추가 검사를 선택할 수 없습니다.')
    return jsonify(audit(rows, profile, mandatory, advanced))


@app.errorhandler(ValueError)
def invalid(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(HTTPException)
def http_error(error):
    return jsonify(error='파일 크기 또는 요청 형식을 확인하세요.' if error.code in (400, 413, 415) else error.description), error.code


@app.errorhandler(Exception)
def server_error(error):
    app.logger.exception('Request failed')
    return jsonify(error='처리를 완료하지 못했습니다. 사진 형식과 OCR 모델 준비 상태를 확인하세요. 텍스트·CSV 입력도 사용할 수 있습니다.'), 500


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8504)
    args = parser.parse_args()
    app.run(host='127.0.0.1', port=args.port, debug=False)
