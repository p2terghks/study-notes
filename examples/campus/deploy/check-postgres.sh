#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
container="campus-pg-test-$$"
# Disposable test database only; never point this suite at production data.
cleanup() { docker rm -f "$container" >/dev/null 2>&1 || true; }
trap cleanup EXIT
password="$(openssl rand -hex 24)"
docker run --detach --name "$container" -e POSTGRES_DB=campus_test -e POSTGRES_USER=campus_admin \
  -e "POSTGRES_PASSWORD=$password" -p 127.0.0.1::5432 postgres:17-alpine >/dev/null
ready=false
for attempt in {1..60}; do
  if docker exec "$container" pg_isready -U campus_admin -d campus_test >/dev/null 2>&1; then ready=true; break; fi
  sleep 1
done
if [[ "$ready" != true ]]; then echo 'Test PostgreSQL failed to start.' >&2; exit 1; fi
# Match the production bootstrap: migrations/tests use a restricted schema owner.
docker exec -i "$container" psql -v ON_ERROR_STOP=1 -U campus_admin -d campus_test <<'SQL'
CREATE ROLE campus_app LOGIN;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE campus_test TO campus_app;
GRANT USAGE, CREATE ON SCHEMA public TO campus_app;
SQL
docker exec -i -e "APP_TEST_PASSWORD=$password" "$container" psql -v ON_ERROR_STOP=1 -U campus_admin -d campus_test <<'SQL'
\getenv app_password APP_TEST_PASSWORD
ALTER ROLE campus_app PASSWORD :'app_password';
SQL
port="$(docker port "$container" 5432/tcp | sed 's/.*://')"
export TEST_POSTGRES_URL="jdbc:postgresql://127.0.0.1:$port/campus_test"
export TEST_POSTGRES_USERNAME=campus_app
export TEST_POSTGRES_PASSWORD="$password"
./mvnw -B test "$@"
