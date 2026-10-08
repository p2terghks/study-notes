#!/usr/bin/env python3
"""Verify two local application containers share a login session. No AWS access."""
import http.client
import json
import secrets
import subprocess
import sys
import time
from http.cookies import SimpleCookie
from urllib.parse import urlencode

image = sys.argv[1] if len(sys.argv) > 1 else 'campus:ecs-check'
prefix = 'campus-smoke-' + secrets.token_hex(4)
network = prefix + '-net'
database = prefix + '-db'
apps = [prefix + '-a', prefix + '-b']
created = []
network_created = False
password = secrets.token_hex(24)

def docker(*args, input=None):
    return subprocess.check_output(['docker', *args], input=input, text=True).strip()

def request(port, path, method='GET', body=None, cookie='', token=None, form=False):
    headers = {'X-Forwarded-Proto': 'https'}
    if cookie:
        # Simulate the trusted HTTPS ALB forwarding the client's Secure cookie.
        headers['Cookie'] = cookie
    if token:
        headers[token['headerName']] = token['token']
    if body is not None:
        headers['Content-Type'] = 'application/x-www-form-urlencoded' if form else 'application/json'
        body = urlencode(body) if form else json.dumps(body)
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    try:
        connection.request(method, path, body, headers)
        response = connection.getresponse()
        data = response.read()
        cookies = SimpleCookie()
        for key, value in response.getheaders():
            if key.lower() == 'set-cookie':
                cookies.load(value)
        if 'SESSION' in cookies:
            assert cookies['SESSION']['secure'] and cookies['SESSION']['httponly']
            cookie = 'SESSION=' + cookies['SESSION'].value
        return response.status, json.loads(data) if data else None, cookie
    finally:
        connection.close()

try:
    docker('network', 'create', network)
    network_created = True
    docker('run', '-d', '--name', database, '--network', network,
           '-e', 'POSTGRES_DB=campus', '-e', 'POSTGRES_USER=campus_admin',
           '-e', 'POSTGRES_PASSWORD=' + password, 'postgres:17-alpine')
    created.append(database)
    for _ in range(60):
        check = subprocess.run(['docker', 'exec', database, 'pg_isready', '-U', 'campus_admin', '-d', 'campus'], capture_output=True)
        if check.returncode == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError('PostgreSQL startup timed out')
    from pathlib import Path
    bootstrap = (Path(__file__).parent / 'bootstrap-db.sql').read_text()
    bootstrap += "\n\\getenv app_password APP_TEST_PASSWORD\nALTER ROLE campus_app PASSWORD :'app_password';\n"
    docker('exec', '-i', '-e', 'APP_TEST_PASSWORD=' + password, database,
           'psql', '-v', 'ON_ERROR_STOP=1', '-U', 'campus_admin', '-d', 'campus', input=bootstrap)
    ports = []
    # Launch together to exercise concurrent Flyway startup against the same database.
    for app in apps:
        docker('run', '-d', '--platform', 'linux/amd64', '--name', app, '--network', network,
               '-p', '127.0.0.1::8080', '-e', 'SPRING_PROFILES_ACTIVE=prod',
               '-e', f'DB_URL=jdbc:postgresql://{database}:5432/campus?sslmode=disable',
               '-e', 'DB_USERNAME=campus_app', '-e', 'DB_PASSWORD=' + password, image)
        created.append(app)
        ports.append(int(docker('port', app, '8080/tcp').rsplit(':', 1)[1]))
    for port in ports:
        for _ in range(120):
            try:
                if request(port, '/actuator/health/readiness')[0] == 200:
                    break
            except (OSError, ValueError, http.client.HTTPException):
                pass
            time.sleep(1)
        else:
            raise RuntimeError('Application startup timed out; inspect the Docker image')
    status, csrf, cookie = request(ports[0], '/api/csrf')
    assert status == 200
    account = {'studentNo': '20990001', 'name': 'Container Test', 'password': secrets.token_hex(12)}
    assert request(ports[0], '/api/register', 'POST', account, cookie, csrf)[0] == 201
    status, _, cookie = request(ports[0], '/api/login', 'POST',
                                {'username': account['studentNo'], 'password': account['password']}, cookie, csrf, True)
    assert status == 204
    status, state, _ = request(ports[1], '/api/state', cookie=cookie)
    assert status == 200 and state['student']['studentNo'] == account['studentNo']
    assert state['courses'] == []
    assert request(ports[1], '/api/config')[1] == {'demoEnabled': False}
    print('PASS: amd64 image, concurrent Flyway startup, restricted DB role, health checks, signup/login, secure cookie, cross-container session, demo disabled')
finally:
    for container in reversed(created):
        subprocess.run(['docker', 'rm', '-f', container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if network_created:
        subprocess.run(['docker', 'network', 'rm', network], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
