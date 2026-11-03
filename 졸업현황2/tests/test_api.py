import io
import unittest
from unittest.mock import patch
from PIL import Image
from app import app

HEADERS={'X-Requested-With':'graduation-html'}
PROFILE='2025-인공지능빅데이터'

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
    def post(self,path,data):
        return self.client.post(path,json=data,headers=HEADERS)
    def parse(self,text='JAVA 3 A+'):
        return self.post('/api/parse',{'profile':PROFILE,'text':text}).get_json()
    def payload(self,text='JAVA 3 A+'):
        parsed=self.parse(text)
        for row in parsed['rows']:row['확인']=True
        return {'profile':PROFILE,'rows':parsed['rows'],'review_token':parsed['review_token'],'consent':True,'resolved':False}
    def test_html_and_assets(self):
        r=self.client.get('/')
        self.assertEqual(r.status_code,200)
        self.assertIn(b'/static/app.js',r.data)
        for path in ['/static/style.css', '/reference']:
            with self.client.get(path) as response:
                self.assertEqual(response.status_code,200)
    def test_all_profiles(self):
        profiles=self.client.get('/api/config').get_json()['profiles']
        self.assertEqual(len(profiles),12)
        for p in profiles:
            r=self.post('/api/parse',{'profile':p['id'],'text':'JAVA 3 A+'})
            self.assertEqual(r.status_code,200)
    def test_audit_success(self):
        r=self.post('/api/audit',self.payload())
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.get_json()['total'],3)
    def test_unconfirmed_not_counted(self):
        p=self.payload();p['rows'][0]['확인']=False
        self.assertEqual(self.post('/api/audit',p).get_json()['total'],0)
    def test_wrong_catalog_blocks(self):
        p=self.payload();p['rows'][0]['학점']=30
        r=self.post('/api/audit',p).get_json()
        self.assertEqual(r['total'],0);self.assertTrue(r['issues'])
    def test_review_and_consent_required(self):
        p=self.payload('JAVA 3 A+\nJAVA 3 BO')
        self.assertEqual(self.post('/api/audit',p).status_code,400)
        p['resolved']=True
        self.assertEqual(self.post('/api/audit',p).status_code,200)
        p['consent']=False
        self.assertEqual(self.post('/api/audit',p).status_code,400)
    def test_token_tamper_and_profile_change(self):
        p=self.payload();p['profile']='2024-인공지능빅데이터'
        self.assertEqual(self.post('/api/audit',p).status_code,400)
        p=self.payload();p['review_token']='fake'
        self.assertEqual(self.post('/api/audit',p).status_code,400)
    def test_csv_ignores_supplied_confirmation(self):
        content='과목명,학점,이수구분,성적,확인\nJAVA,3,전공필수,A+,True\n'
        r=self.client.post('/api/csv',data={'profile':PROFILE,'file':(io.BytesIO(content.encode('utf-8-sig')),'test.csv')},headers=HEADERS)
        self.assertEqual(r.status_code,200);self.assertIs(r.get_json()['rows'][0]['확인'],False)
    def test_csv_required_columns(self):
        r=self.client.post('/api/csv',data={'profile':PROFILE,'file':(io.BytesIO(b'a,b\n1,2'),'test.csv')},headers=HEADERS)
        self.assertEqual(r.status_code,400)
    def test_ocr_route_with_stubbed_model(self):
        image=io.BytesIO();Image.new('RGB',(20,20)).save(image,format='PNG');image.seek(0)
        with patch('app.recognize',return_value=([{'text':'JAVA 3 A+','confidence':.9}],[])):
            r=self.client.post('/api/ocr',data={'profile':PROFILE,'photos':(image,'photo.png')},headers=HEADERS)
        self.assertEqual(r.status_code,200);self.assertEqual(r.get_json()['rows'][0]['과목명'],'JAVA')
    def test_bad_photo(self):
        r=self.client.post('/api/ocr',data={'profile':PROFILE,'photos':(io.BytesIO(b'not an image'),'photo.png')},headers=HEADERS)
        self.assertEqual(r.status_code,400)
    def test_bad_inputs_return_400(self):
        for key,value in [('rows',[None]),('rows',[{'과목명':[], '성적':'A+','학점':3,'이수구분':'전공필수'}]),('mandatory',[{}]),('advanced','yes')]:
            p=self.payload();p[key]=value
            self.assertEqual(self.post('/api/audit',p).status_code,400)
        self.assertEqual(self.post('/api/parse',[]).status_code,400)
    def test_cross_origin_and_host_rejected(self):
        self.assertEqual(self.client.post('/api/parse',json={}).status_code,403)
        self.assertEqual(self.client.post('/api/parse',json={},headers={**HEADERS,'Origin':'http://evil.invalid'}).status_code,403)
        self.assertEqual(self.client.get('/api/config',headers={'Host':'evil.invalid'}).status_code,400)
    def test_request_size_limit(self):
        old=app.config['MAX_CONTENT_LENGTH'];app.config['MAX_CONTENT_LENGTH']=100
        try:self.assertEqual(self.post('/api/parse',{'text':'x'*101}).status_code,413)
        finally:app.config['MAX_CONTENT_LENGTH']=old

if __name__=='__main__':unittest.main()
