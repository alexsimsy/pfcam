# Refresh & Deploy Process for PFCAM Application

Follow these steps to reliably deploy a refreshed application and ensure all code and environment changes are picked up.

---

## 1. Make Your Code and Environment Changes
- Edit your code, `.env`, or configuration files as needed.

---

## 2. Clean Up Old Build Artifacts
- **Delete the local frontend build output (if present):**
  ```sh
  rm -rf frontend/dist
  ```

---

## 3. Build the Docker Image with No Cache
- **Build the frontend image from scratch** to ensure all changes (including `.env`) are picked up:
  ```sh
  docker-compose build --no-cache frontend
  ```

---

## 4. Recreate the Container
- **Recreate the frontend container** to use the new image:
  ```sh
  docker-compose up -d --force-recreate frontend
  ```

---

## 5. (Optional) Restart Backend/Other Services
- If you made backend or config changes, rebuild/recreate those containers as well:
  ```sh
  docker-compose build --no-cache backend
  docker-compose up -d --force-recreate backend
  ```

---

## 6. Hard Refresh Your Browser
- **Force a hard refresh** to clear any cached frontend assets:
  - Mac: `Cmd + Shift + R`
  - Windows: `Ctrl + Shift + R`

---

## 7. Test the Application
- Verify that the frontend and backend are working as expected.
- Check the browser's network tab to ensure API requests use relative paths (e.g., `/api/v1/...`).

---

## 8. Commit and Push to GitHub
- **Stage, commit, and push your changes** to keep your repository up to date:
  ```sh
  git add .
  git commit -m "Describe your changes"
  git push
  ```

---

## 9. Troubleshooting Checklist
- If you see 502 errors: check backend and nginx logs.
- If you see old code: ensure you removed the frontend volumes from `docker-compose.yml` and followed the build steps above.
- If you see CORS or hostname errors: check that all API calls use relative paths.

---

**This process ensures you always deploy a fresh, up-to-date application and avoid stale builds or environment issues.** 