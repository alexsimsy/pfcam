# PFCAM Project Context Guide

## Architecture Overview
- **Frontend**: React/Vite application (port 3000)
- **Backend**: FastAPI Python application (port 8000)
- **Database**: PostgreSQL (port 5432)
- **Cache**: Redis (port 6379)
- **Video Streaming**: MediaMTX (ports 8554/8888)
- **Reverse Proxy**: Nginx (ports 80/443)

## Key Configuration Files
- `docker-compose.yml` - Main orchestration
- `nginx/nginx.conf` - Routing and reverse proxy
- `backend/Dockerfile` - Backend container setup
- `frontend/Dockerfile` - Frontend container setup
- `backend/app/main.py` - FastAPI application entry
- `frontend/vite.config.ts` - Vite configuration

## Service Dependencies
```
nginx → frontend:3000 (UI)
nginx → backend:8000 (API)
backend → postgres:5432 (Database)
backend → redis:6379 (Cache)
```

## Common Issues & Solutions
1. **Frontend restarting**: Usually serve command format issues
2. **API routing**: Check nginx.conf proxy_pass settings
3. **Database connection**: Verify postgres health check
4. **Build failures**: Check Dockerfile dependencies

## Development Workflow
1. Always check `docker-compose ps` before changes
2. Use `docker-compose logs [service]` for debugging
3. Rebuild with `docker-compose build --no-cache` if needed
4. Test via http://localhost after changes

## Frontend Deployment Process (CRITICAL)
**Reference: `docs/REFRESH_DEPLOYMENT_PROCESS.md`**

For frontend changes, always follow this process:
1. **Clean build artifacts**: `rm -rf frontend/dist`
2. **Build with no cache**: `docker-compose build --no-cache frontend`
3. **Force recreate container**: `docker-compose up -d --force-recreate frontend`
4. **Hard refresh browser**: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
5. **Test API calls**: Ensure they use relative paths (`/api/v1/...`)

**Common Issues:**
- 502 errors: Check backend and nginx logs
- Old code showing: Remove frontend volumes, follow build steps
- CORS errors: Verify API calls use relative paths

## Critical Paths
- Frontend API calls: `/api/v1/*`
- WebSocket connections: `/ws/*`
- Health checks: `/health`
- Static files: Served by nginx from frontend

## Environment Variables
- Backend: DATABASE_URL, SECRET_KEY, etc.
- Frontend: VITE_WS_URL for WebSocket connections
- Database: POSTGRES_* credentials

## Last Known Good State
- Commit: 98b76ea (HEAD -> main, origin/main)
- All services running without restart loops
- Clean rebuild successful 