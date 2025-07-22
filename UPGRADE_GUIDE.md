# PFCAM Upgrade Guide

## Overview
This guide provides step-by-step instructions for safely upgrading your PFCAM server to a new release, including best practices for backup and persistent data management.

---

## 1. Preparation

### 1.1. Review Release Notes
- Read the release notes for the new version on GitHub.
- Check for breaking changes or manual migration steps.

### 1.2. Notify Users
- Inform users of planned downtime (if any).

---

## 2. Backup

### 2.1. Backup Database
```sh
docker compose exec -T postgres pg_dump -U pfcam pfcam > /opt/pfcam/backups/db_$(date +%Y%m%d_%H%M%S).sql
```

### 2.2. Backup Configuration and Persistent Data
```sh
cp .env /opt/pfcam/backups/.env_$(date +%Y%m%d_%H%M%S)
cp -r /opt/pfcam/data /opt/pfcam/backups/data_$(date +%Y%m%d_%H%M%S)
```

- **Tip:** Store backups in a separate directory (e.g., `/opt/pfcam/backups/`) to avoid overwriting during upgrade.

---

## 3. Stop Running Services
```sh
docker compose down
```

---

## 4. Download and Extract the New Release

### 4.1. Download the Deployment Package
```sh
wget https://github.com/alexsimsy/pfcam/releases/download/vX.Y.Z/event-cam-deployment-X.Y.Z.tar.gz
```

### 4.2. Extract the Package
```sh
tar -xzf event-cam-deployment-X.Y.Z.tar.gz
cd event-cam-deployment-X.Y.Z
```

---

## 5. Restore/Preserve Persistent Files

- **Best Practice:**
  - Store your `.env` and persistent data (e.g., `/opt/pfcam/data/`, database volume) outside the deployment directory.
  - After extracting the new release, copy your `.env` and persistent data back into the new deployment directory if needed.
  - This avoids accidental overwrites and makes rollbacks easier.

```sh
cp /opt/pfcam/backups/.env_YYYYMMDD_HHMMSS .env
cp -r /opt/pfcam/backups/data_YYYYMMDD_HHMMSS data
```

---

## 6. Run the Upgrade

### 6.1. Run the Deployment Script (if provided)
```sh
chmod +x hetzner-deploy.sh
./hetzner-deploy.sh
```

### 6.2. Or Start Services Manually
```sh
docker compose up -d --build
```

---

## 7. Post-Upgrade Steps

### 7.1. Verify the Upgrade
- Check the web UI and API endpoints.
- Confirm new features (e.g., camera health polling, reconnect button) are present.
- Check logs for errors:
```sh
docker compose logs -f
```

### 7.2. Clean Up Old Backups (optional)
- Remove backups older than 7 days to save space:
```sh
find /opt/pfcam/backups -type f -mtime +7 -delete
```

---

## FAQ: Should I reload existing files or store them separately?

- **Best Practice:** Store persistent files (e.g., `.env`, data, backups) in a separate directory outside the deployment package.
  - This prevents accidental overwrites during upgrades.
  - Makes rollbacks and disaster recovery easier.
- Only copy files back into the new deployment directory if the new version requires it.
- Always verify your backups before starting the upgrade.

---

## Support
- For issues, check the logs and review the troubleshooting section in the deployment guide.
- Create a GitHub issue if you encounter problems. 