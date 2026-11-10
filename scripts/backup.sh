#!/usr/bin/env bash
set -euo pipefail
backup_root="/var/backups/infrafoundry"
mkdir -p "$backup_root"
archive="$backup_root/app-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
tar --create --gzip --file "$archive" /var/www/html
sha256sum "$archive" > "$archive.sha256"
find "$backup_root" -type f -mtime +14 -delete
