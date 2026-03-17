# gamecom-engine restart-loop root cause

## Root cause
1. `gamecom-engine` exits with code `1` and restarts.
2. Startup fails during DB connection (Alembic/SQLAlchemy), with:
   - `socket.gaierror: [Errno -2] Name or service not known`

This indicates unresolved database host name in container runtime config (wrong DB host in env/network scope).

## What to fix
1. Verify DB host env used by `gamecom-engine` (must match reachable Docker service/container name in same network).
2. Ensure `gamecom-engine` and DB container are attached to the same Docker network.
3. Verify DATABASE_URL/DB_* vars in compose/env file (no typo in host name).
4. Re-deploy `gamecom-engine` after env/network correction and confirm exit code stays `0`.
