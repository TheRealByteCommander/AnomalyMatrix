#!/usr/bin/env bash
# =============================================================================
# AnomalyMatrix — Autonomous Linux Installer (bare OS → running stack)
# =============================================================================
#
# Empfohlenes OS:  Ubuntu Server 24.04 LTS (x86_64)
# Unterstützt:     Ubuntu 22.04 / 24.04 LTS, Debian 12 (bookworm)
#
# Frisches System (Beispiel):
#   curl -fsSL https://raw.githubusercontent.com/TheRealByteCommander/AnomalyMatrix/master/scripts/install.sh \
#     | sudo bash
#
# Oder aus dem Repo:
#   sudo ./scripts/install.sh --mode prod --host 192.168.1.50
#
# Private Repos:
#   sudo GITHUB_TOKEN=ghp_xxx ./scripts/install.sh
#
# =============================================================================
set -euo pipefail

APP_NAME="AnomalyMatrix"
APP_DIR_DEFAULT="/opt/anomalymatrix"
REPO_URL_DEFAULT="https://github.com/TheRealByteCommander/AnomalyMatrix.git"
BRANCH_DEFAULT="master"
VERSION_DEFAULT="1.0.0"

MODE="prod"                 # prod | dev
APP_DIR="${APP_DIR:-$APP_DIR_DEFAULT}"
REPO_URL="${REPO_URL:-$REPO_URL_DEFAULT}"
BRANCH="${BRANCH:-$BRANCH_DEFAULT}"
INSTALL_HOST=""             # IP or DNS for CORS / printed URLs
ENABLE_FIREWALL="true"
ENABLE_TLS="false"          # COOKIE_SECURE + https CORS hint
SKIP_CLONE="false"
SKIP_DOCKER_INSTALL="false"
FORCE_SECRETS="false"       # overwrite existing .env.production
NON_INTERACTIVE="true"
CAMERA_DRIVER_DEFAULT="synthetic"  # safe on machines without cameras
COMPOSE_PROJECT="anomalymatrix"

CREDENTIALS_FILE=""
LOG_FILE=""

log()  { echo "[$APP_NAME] $*"; }
ok()   { echo "[$APP_NAME] ✓ $*"; }
warn() { echo "[$APP_NAME][WARN] $*" >&2; }
err()  { echo "[$APP_NAME][ERROR] $*" >&2; }

usage() {
  cat <<EOF
Usage: sudo $0 [options]

Options:
  --mode prod|dev       Installationsmodus (default: prod)
  --host HOST           Öffentliche IP/DNS für HMI/CORS (default: Primär-IP)
  --app-dir DIR         Installationsverzeichnis (default: $APP_DIR_DEFAULT)
  --branch BRANCH       Git-Branch (default: $BRANCH_DEFAULT)
  --repo-url URL        Git-Remote (default: GitHub)
  --skip-clone          Vorhandenes Repo in --app-dir / CWD nutzen
  --skip-docker         Docker nicht installieren (bereits vorhanden)
  --force-secrets       Bestehende .env.production neu generieren (gefährlich)
  --no-firewall         UFW nicht konfigurieren
  --tls                 HTTPS/TLS erwartet (COOKIE_SECURE=true)
  --help                Diese Hilfe

Umgebungsvariablen:
  GITHUB_TOKEN          Für private Repos (HTTPS-Clone)
  REPO_URL / BRANCH / APP_DIR
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mode) MODE="${2:-}"; shift 2 ;;
      --host) INSTALL_HOST="${2:-}"; shift 2 ;;
      --app-dir) APP_DIR="${2:-}"; shift 2 ;;
      --branch) BRANCH="${2:-}"; shift 2 ;;
      --repo-url) REPO_URL="${2:-}"; shift 2 ;;
      --skip-clone) SKIP_CLONE="true"; shift ;;
      --skip-docker) SKIP_DOCKER_INSTALL="true"; shift ;;
      --force-secrets) FORCE_SECRETS="true"; shift ;;
      --no-firewall) ENABLE_FIREWALL="false"; shift ;;
      --tls) ENABLE_TLS="true"; shift ;;
      --help|-h) usage; exit 0 ;;
      *) err "Unbekanntes Argument: $1"; usage; exit 2 ;;
    esac
  done
  if [[ "$MODE" != "prod" && "$MODE" != "dev" ]]; then
    err "--mode muss prod oder dev sein"
    exit 2
  fi
}

require_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    err "Bitte als root ausführen: sudo $0 ..."
    exit 1
  fi
}

detect_os() {
  if [[ ! -f /etc/os-release ]]; then
    err "Kein /etc/os-release — nur Linux mit systemd/apt wird unterstützt."
    exit 1
  fi
  # shellcheck disable=SC1091
  . /etc/os-release
  OS_ID="${ID:-}"
  OS_VERSION_ID="${VERSION_ID:-}"
  OS_CODENAME="${VERSION_CODENAME:-}"
  ARCH="$(uname -m)"

  case "$OS_ID" in
    ubuntu)
      case "$OS_VERSION_ID" in
        22.04|24.04) ok "OS erkannt: Ubuntu $OS_VERSION_ID ($ARCH)" ;;
        *)
          warn "Ubuntu $OS_VERSION_ID ist nicht offiziell getestet — fahre mit 24.04-Pfad fort."
          ;;
      esac
      ;;
    debian)
      case "$OS_VERSION_ID" in
        12) ok "OS erkannt: Debian $OS_VERSION_ID ($ARCH)" ;;
        *)
          warn "Debian $OS_VERSION_ID ist nicht offiziell getestet."
          ;;
      esac
      ;;
    *)
      err "Nicht unterstütztes OS: ${PRETTY_NAME:-$OS_ID}."
      err "Empfohlen: Ubuntu Server 24.04 LTS. Alternativ: Ubuntu 22.04 oder Debian 12."
      exit 1
      ;;
  esac

  if [[ "$ARCH" != "x86_64" && "$ARCH" != "amd64" && "$ARCH" != "aarch64" ]]; then
    warn "Architektur $ARCH — Docker-Images sind primär für amd64/arm64 gebaut."
  fi
}

detect_host() {
  if [[ -n "$INSTALL_HOST" ]]; then
    return 0
  fi
  INSTALL_HOST="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [[ -z "$INSTALL_HOST" ]]; then
    INSTALL_HOST="127.0.0.1"
  fi
  log "Host für CORS/URLs: $INSTALL_HOST"
}

rand_secret() {
  local bytes="${1:-32}"
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 "$bytes" | tr -d '\n' | tr '/+' 'Ab'
  else
    head -c "$bytes" /dev/urandom | base64 | tr -d '\n' | tr '/+' 'Ab'
  fi
}

rand_alnum() {
  local len="${1:-32}"
  tr -dc 'A-Za-z0-9' </dev/urandom | head -c "$len"
}

install_base_packages() {
  log "Systempakete aktualisieren..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    git \
    openssl \
    jq \
    ufw \
    apt-transport-https \
    software-properties-common
  ok "Basispakete installiert"
}

install_docker() {
  if [[ "$SKIP_DOCKER_INSTALL" == "true" ]]; then
    log "Docker-Installation übersprungen (--skip-docker)"
  elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    ok "Docker + Compose bereits vorhanden: $(docker --version)"
  else
    log "Docker Engine + Compose Plugin installieren..."
    install -m 0755 -d /etc/apt/keyrings
    if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
      curl -fsSL "https://download.docker.com/linux/${OS_ID}/gpg" -o /etc/apt/keyrings/docker.asc
      chmod a+r /etc/apt/keyrings/docker.asc
    fi
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${OS_ID} ${OS_CODENAME} stable" \
      > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
    ok "Docker installiert: $(docker --version)"
  fi

  if ! docker compose version >/dev/null 2>&1; then
    err "'docker compose' nicht verfügbar — Installation abgebrochen."
    exit 1
  fi

  # Allow invoking user (if sudo) to use docker without re-login later
  if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
    usermod -aG docker "$SUDO_USER" || true
    log "Benutzer $SUDO_USER zur Gruppe 'docker' hinzugefügt (neu anmelden für Wirkung)."
  fi
}

resolve_source_tree() {
  local script_path="${BASH_SOURCE[0]:-}"
  local maybe_root=""

  # When piped (curl | bash), BASH_SOURCE is a fd — skip local-copy path and clone.
  if [[ -n "$script_path" && -f "$script_path" && "$script_path" != /dev/fd/* && "$script_path" != /proc/self/fd/* ]]; then
    local script_dir
    script_dir="$(cd "$(dirname "$script_path")" && pwd)"
    maybe_root="$(cd "$script_dir/.." && pwd)"
  fi

  if [[ "$SKIP_CLONE" == "true" ]]; then
    if [[ -f "$APP_DIR/docker-compose.yml" ]]; then
      ok "Nutze vorhandenes Repo in $APP_DIR"
      return 0
    fi
    if [[ -n "$maybe_root" && -f "$maybe_root/docker-compose.yml" ]]; then
      APP_DIR="$maybe_root"
      ok "Nutze lokales Repo in $APP_DIR (--skip-clone)"
      return 0
    fi
    if [[ -f "./docker-compose.yml" ]]; then
      APP_DIR="$(pwd)"
      ok "Nutze CWD-Repo in $APP_DIR"
      return 0
    fi
    err "--skip-clone gesetzt, aber kein Repo gefunden."
    exit 1
  fi

  # If installer runs from a checkout, prefer syncing into APP_DIR
  if [[ -n "$maybe_root" && -f "$maybe_root/docker-compose.yml" && "$maybe_root" != "$APP_DIR" ]]; then
    log "Kopiere lokales Repo nach $APP_DIR ..."
    mkdir -p "$APP_DIR"
    if ! command -v rsync >/dev/null 2>&1; then
      apt-get install -y rsync >/dev/null
    fi
    rsync -a --delete \
      --exclude '.git' \
      --exclude 'frontend/node_modules' \
      --exclude 'backend/.venv' \
      --exclude 'frontend/dist' \
      --exclude '.env' \
      --exclude '.env.production' \
      --exclude 'CREDENTIALS.txt' \
      "$maybe_root/" "$APP_DIR/"
    if [[ -d "$maybe_root/.git" && ! -d "$APP_DIR/.git" ]]; then
      cp -a "$maybe_root/.git" "$APP_DIR/.git"
    fi
    ok "Repo bereit unter $APP_DIR"
    return 0
  fi

  if [[ -n "$maybe_root" && -f "$maybe_root/docker-compose.yml" && "$maybe_root" == "$APP_DIR" ]]; then
    ok "Nutze Repo in $APP_DIR"
    return 0
  fi

  clone_or_update_repo
}

clone_or_update_repo() {
  local clone_url="$REPO_URL"
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    if [[ "$clone_url" =~ ^https://github.com/ ]]; then
      clone_url="https://x-access-token:${GITHUB_TOKEN}@github.com/${clone_url#https://github.com/}"
    fi
  fi

  if [[ -d "$APP_DIR/.git" ]]; then
    log "Aktualisiere bestehendes Repo in $APP_DIR ($BRANCH)..."
    git -C "$APP_DIR" remote set-url origin "$REPO_URL" || true
    git -C "$APP_DIR" fetch origin
    git -C "$APP_DIR" checkout "$BRANCH"
    git -C "$APP_DIR" pull --ff-only origin "$BRANCH" || git -C "$APP_DIR" reset --hard "origin/$BRANCH"
  else
    log "Klone $REPO_URL → $APP_DIR (Branch $BRANCH)..."
    mkdir -p "$(dirname "$APP_DIR")"
    rm -rf "$APP_DIR"
    git clone --branch "$BRANCH" --single-branch "$clone_url" "$APP_DIR"
    # Remove token from remote URL if embedded
    git -C "$APP_DIR" remote set-url origin "$REPO_URL" || true
  fi
  ok "Quellcode bereit"
}

read_version() {
  if [[ -f "$APP_DIR/VERSION" ]]; then
    tr -d '\r\n' < "$APP_DIR/VERSION"
  else
    echo "$VERSION_DEFAULT"
  fi
}

write_env_prod() {
  local env_file="$APP_DIR/.env.production"
  CREDENTIALS_FILE="$APP_DIR/CREDENTIALS.txt"

  if [[ -f "$env_file" && "$FORCE_SECRETS" != "true" ]]; then
    ok "Bestehende Secrets behalten ($env_file)"
    warn "Neu generieren nur mit --force-secrets (ändert DB-Passwort und bricht bestehende Volumes)"
    return 0
  fi

  local jwt service_token license_admin admin_pw db_pw minio_pw influx_token influx_pw opcua_key
  jwt="$(rand_secret 48)"
  service_token="$(rand_alnum 40)"
  license_admin="$(rand_alnum 32)"
  admin_pw="$(rand_alnum 20)"
  db_pw="$(rand_alnum 28)"
  minio_pw="$(rand_alnum 28)"
  influx_token="$(rand_alnum 40)"
  influx_pw="$(rand_alnum 28)"
  opcua_key="$(rand_alnum 32)"

  local scheme="http"
  local cookie_secure="false"
  if [[ "$ENABLE_TLS" == "true" ]]; then
    scheme="https"
    cookie_secure="true"
  fi
  local cors="${scheme}://${INSTALL_HOST}"
  if [[ "$INSTALL_HOST" != "127.0.0.1" && "$INSTALL_HOST" != "localhost" ]]; then
    cors="${cors},${scheme}://${INSTALL_HOST}:80,${scheme}://127.0.0.1"
  fi

  umask 077
  cat > "$env_file" <<EOF
# Generated by AnomalyMatrix installer $(date -u +%Y-%m-%dT%H:%M:%SZ)
# DO NOT COMMIT
ANOMALYMATRIX_ENV=prod
LOG_LEVEL=INFO

JWT_SECRET=${jwt}
RBAC_ENFORCE=true
LICENSE_ENFORCE=true
LICENSE_ADMIN_TOKEN=${license_admin}
SERVICE_AUTH_TOKEN=${service_token}
COOKIE_SECURE=${cookie_secure}

AMX_CORS_ORIGINS=${cors}

DATABASE_URL=postgresql://anomaly:${db_pw}@postgres:5432/anomalymatrix
POSTGRES_DB=anomalymatrix
POSTGRES_USER=anomaly
POSTGRES_PASSWORD=${db_pw}

ANOMALYMATRIX_INFERENCE_PROVIDER=patchcore

EDGE_ACQUISITION_URL=http://edge-acquisition:8091
OPCUA_GATEWAY_URL=http://opcua-gateway:8092
OPCUA_SECURITY_ENABLED=true
OPCUA_CERT_DIR=/app/certs
CAMERA_DRIVER=${CAMERA_DRIVER_DEFAULT}
CAMERA_SOURCE=0
OPCUA_API_KEY=${opcua_key}

INFLUX_URL=http://influxdb:8086
INFLUX_TOKEN=${influx_token}
INFLUX_ORG=anomalymatrix
INFLUX_BUCKET=inspection_metrics
INFLUX_USERNAME=anomaly
INFLUX_PASSWORD=${influx_pw}

MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_BASE=/artifacts
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=${minio_pw}
MINIO_SECURE=false

AMX_ADMIN_PASSWORD=${admin_pw}
EOF
  chmod 600 "$env_file"

  cat > "$CREDENTIALS_FILE" <<EOF
AnomalyMatrix credentials (generated $(date -u +%Y-%m-%dT%H:%M:%SZ))
=================================================================
HMI URL:              ${scheme}://${INSTALL_HOST}/
API (local):          http://127.0.0.1:8080/api/v1/health
Admin login:          admin-1
Admin password:       ${admin_pw}
License admin token:  ${license_admin}
OPC-UA API key:       ${opcua_key}
Service auth token:   ${service_token}

Files:
  Env:          ${env_file}
  Credentials:  ${CREDENTIALS_FILE}

IMPORTANT:
  - Rotate these secrets after first login
  - Delete or encrypt ${CREDENTIALS_FILE} once stored in your vault
  - For HTTPS: put a reverse proxy in front and re-run with --tls (or set COOKIE_SECURE=true)
  - Re-running the installer keeps this file unless --force-secrets is set
EOF
  chmod 600 "$CREDENTIALS_FILE"
  ok "Produktions-Secrets geschrieben ($env_file)"
}

write_env_dev() {
  local env_file="$APP_DIR/.env"
  if [[ ! -f "$env_file" ]]; then
    cp "$APP_DIR/.env.example" "$env_file"
    chmod 600 "$env_file"
  fi
  CREDENTIALS_FILE="$APP_DIR/CREDENTIALS.txt"
  cat > "$CREDENTIALS_FILE" <<EOF
AnomalyMatrix DEV credentials
=============================
HMI (vite, separate):  http://${INSTALL_HOST}:5173
API:                   http://${INSTALL_HOST}:8080/api/v1/health
Dev users:             admin-1 / changeme (JSON/Postgres seed)
EOF
  chmod 600 "$CREDENTIALS_FILE"
  ok "Dev-.env bereit"
}

compose_cmd() {
  if [[ "$MODE" == "prod" ]]; then
    docker compose \
      -p "$COMPOSE_PROJECT" \
      -f "$APP_DIR/docker-compose.yml" \
      -f "$APP_DIR/docker-compose.prod.yml" \
      --env-file "$APP_DIR/.env.production" \
      "$@"
  else
    docker compose \
      -p "$COMPOSE_PROJECT" \
      -f "$APP_DIR/docker-compose.yml" \
      -f "$APP_DIR/docker-compose.dev.yml" \
      --env-file "$APP_DIR/.env" \
      "$@"
  fi
}

start_stack() {
  log "Docker-Images bauen und Stack starten (das kann mehrere Minuten dauern)..."
  cd "$APP_DIR"
  compose_cmd pull || true
  compose_cmd up -d --build
  ok "Stack gestartet"
}

wait_for_health() {
  local url="http://127.0.0.1:8080/api/v1/health"
  log "Warte auf API-Health ($url)..."
  local i
  for i in $(seq 1 60); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      ok "API healthy"
      return 0
    fi
    sleep 3
  done
  err "API Health-Check fehlgeschlagen. Logs:"
  compose_cmd logs --tail=80 api || true
  return 1
}

sync_opcua_api_key() {
  # Gateway authenticates with OPCUA_API_KEY; API looks up users.api_key in Postgres.
  # Seed keys (amx-key-*) must be rotated so the generated key matches operator-1.
  [[ "$MODE" == "prod" ]] || return 0
  local env_file="$APP_DIR/.env.production"
  local opcua_key qa_key eng_key adm_key
  opcua_key="$(grep -E '^OPCUA_API_KEY=' "$env_file" | cut -d= -f2-)"
  [[ -n "$opcua_key" ]] || {
    warn "OPCUA_API_KEY fehlt — DB-Sync übersprungen."
    return 0
  }
  # Keys are alphanumeric from rand_alnum — safe for SQL literals.
  qa_key="$(rand_alnum 32)"
  eng_key="$(rand_alnum 32)"
  adm_key="$(rand_alnum 32)"
  log "OPC-UA API-Key in Postgres synchronisieren (Seed-Keys rotieren)..."
  if compose_cmd exec -T postgres psql -U anomaly -d anomalymatrix -v ON_ERROR_STOP=1 <<SQL >/dev/null
UPDATE users SET api_key = '${opcua_key}' WHERE user_id = 'operator-1';
UPDATE users SET api_key = '${qa_key}' WHERE user_id = 'qa-1';
UPDATE users SET api_key = '${eng_key}' WHERE user_id = 'engineer-1';
UPDATE users SET api_key = '${adm_key}' WHERE user_id = 'admin-1';
SQL
  then
    ok "API-Keys in Postgres aktualisiert (operator-1 = OPCUA_API_KEY)"
  else
    warn "API-Key-Sync fehlgeschlagen — OPC-UA-Inspektionen ggf. 401. Manuell users.api_key setzen."
  fi
}

activate_license() {
  [[ "$MODE" == "prod" ]] || return 0
  local env_file="$APP_DIR/.env.production"
  local admin_pw license_admin license_key cookie_jar
  admin_pw="$(grep -E '^AMX_ADMIN_PASSWORD=' "$env_file" | cut -d= -f2-)"
  license_admin="$(grep -E '^LICENSE_ADMIN_TOKEN=' "$env_file" | cut -d= -f2-)"
  license_key="AMX-INSTALL-$(rand_alnum 16)"
  cookie_jar="$(mktemp)"

  log "Admin-Login + Lizenz-Aktivierung..."
  # Give bootstrap a moment after API healthy
  sleep 2
  if ! curl -fsS -c "$cookie_jar" -X POST "http://127.0.0.1:8080/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"admin-1\",\"password\":\"${admin_pw}\"}" >/tmp/amx-login.json 2>/dev/null; then
    warn "Login fehlgeschlagen — Lizenz später manuell aktivieren."
    rm -f "$cookie_jar"
    return 0
  fi

  local token
  token="$(jq -r '.data.access_token // empty' /tmp/amx-login.json 2>/dev/null || true)"
  if [[ -z "$token" ]]; then
    warn "Kein Access-Token — Lizenz-Aktivierung übersprungen."
    rm -f "$cookie_jar" /tmp/amx-login.json
    return 0
  fi

  if curl -fsS -b "$cookie_jar" -X POST "http://127.0.0.1:8080/api/v1/license/activate" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${token}" \
    -H "X-License-Admin-Token: ${license_admin}" \
    -d "{\"license_key\":\"${license_key}\"}" >/tmp/amx-license.json 2>/dev/null; then
    ok "Lizenz aktiviert"
    echo "Bootstrap license key: ${license_key}" >> "$CREDENTIALS_FILE"
  else
    warn "Lizenz-Aktivierung fehlgeschlagen (siehe API-Logs)."
  fi
  rm -f "$cookie_jar" /tmp/amx-login.json /tmp/amx-license.json
}

smoke_inspection() {
  [[ "$MODE" == "prod" ]] || return 0
  local env_file="$APP_DIR/.env.production"
  local admin_pw token
  admin_pw="$(grep -E '^AMX_ADMIN_PASSWORD=' "$env_file" | cut -d= -f2-)"
  token="$(curl -fsS -X POST "http://127.0.0.1:8080/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"admin-1\",\"password\":\"${admin_pw}\"}" \
    | jq -r '.data.access_token // empty')"
  if [[ -z "$token" ]]; then
    warn "Smoke-Inspektion übersprungen (kein Token)."
    return 0
  fi
  if curl -fsS -X POST "http://127.0.0.1:8080/api/v1/inspections/run" \
    -H "Authorization: Bearer ${token}" \
    -H "Content-Type: application/json" \
    -d '{"camera_id":"cam-01","recipe_id":"recipe-default"}' >/dev/null; then
    ok "Smoke-Inspektion OK"
  else
    warn "Smoke-Inspektion fehlgeschlagen — Stack läuft ggf. trotzdem."
  fi
}

configure_firewall() {
  if [[ "$ENABLE_FIREWALL" != "true" ]]; then
    log "Firewall-Setup übersprungen"
    return 0
  fi
  if ! command -v ufw >/dev/null 2>&1; then
    warn "ufw nicht installiert — Firewall übersprungen"
    return 0
  fi
  log "UFW konfigurieren (SSH + HMI 80, optional OPC-UA 4840)..."
  ufw allow OpenSSH >/dev/null 2>&1 || ufw allow 22/tcp >/dev/null 2>&1 || true
  ufw allow 80/tcp >/dev/null 2>&1 || true
  if [[ "$MODE" == "prod" ]]; then
    ufw allow 4840/tcp >/dev/null 2>&1 || true
  else
    ufw allow 8080/tcp >/dev/null 2>&1 || true
    ufw allow 5173/tcp >/dev/null 2>&1 || true
    ufw allow 4840/tcp >/dev/null 2>&1 || true
  fi
  if [[ "$ENABLE_TLS" == "true" ]]; then
    ufw allow 443/tcp >/dev/null 2>&1 || true
  fi
  # Enable non-interactively if inactive
  if ufw status | grep -qi inactive; then
    echo "y" | ufw enable >/dev/null 2>&1 || true
  fi
  ok "Firewall-Regeln gesetzt"
}

install_systemd_unit() {
  [[ "$MODE" == "prod" ]] || return 0
  local unit="/etc/systemd/system/anomalymatrix.service"
  cat > "$unit" <<EOF
[Unit]
Description=AnomalyMatrix production stack
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/docker compose -p ${COMPOSE_PROJECT} -f ${APP_DIR}/docker-compose.yml -f ${APP_DIR}/docker-compose.prod.yml --env-file ${APP_DIR}/.env.production up -d
ExecStop=/usr/bin/docker compose -p ${COMPOSE_PROJECT} -f ${APP_DIR}/docker-compose.yml -f ${APP_DIR}/docker-compose.prod.yml --env-file ${APP_DIR}/.env.production stop
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable anomalymatrix.service >/dev/null
  ok "systemd-Unit anomalymatrix.service aktiviert (Autostart)"
}

print_summary() {
  local version scheme="http"
  version="$(read_version)"
  [[ "$ENABLE_TLS" == "true" ]] && scheme="https"

  local compose_hint
  if [[ "$MODE" == "prod" ]]; then
    compose_hint="docker compose -p $COMPOSE_PROJECT -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production"
  else
    compose_hint="docker compose -p $COMPOSE_PROJECT -f docker-compose.yml -f docker-compose.dev.yml --env-file .env"
  fi

  cat <<EOF

================================================================================
 $APP_NAME v${version} — Installation abgeschlossen
================================================================================
 Empfohlenes OS:     Ubuntu Server 24.04 LTS
 Installationspfad:  $APP_DIR
 Modus:              $MODE
 HMI:                ${scheme}://${INSTALL_HOST}/
 API-Health:         http://127.0.0.1:8080/api/v1/health
 Credentials:        $CREDENTIALS_FILE

 Nützliche Befehle:
   cd $APP_DIR
   $compose_hint ps
   $compose_hint logs -f api
   systemctl status anomalymatrix

 Kamera später aktivieren:
   In .env.production: CAMERA_DRIVER=opencv  und  CAMERA_SOURCE=0|/dev/video0|Pfad
   Dann: $compose_hint up -d --build edge-acquisition
================================================================================
EOF

  if [[ -f "$CREDENTIALS_FILE" ]]; then
    echo
    log "Zugangsdaten (auch in $CREDENTIALS_FILE):"
    grep -E '^(HMI|Admin|License|OPC-UA|Service)' "$CREDENTIALS_FILE" || true
  fi
}

main() {
  parse_args "$@"
  require_root
  detect_os
  detect_host
  LOG_FILE="/var/log/anomalymatrix-install.log"
  exec > >(tee -a "$LOG_FILE") 2>&1
  log "Starte Installation (Log: $LOG_FILE)"

  install_base_packages
  install_docker
  resolve_source_tree

  if [[ "$MODE" == "prod" ]]; then
    write_env_prod
  else
    write_env_dev
  fi

  start_stack
  wait_for_health
  sync_opcua_api_key
  activate_license
  smoke_inspection
  configure_firewall
  install_systemd_unit
  print_summary
}

main "$@"
