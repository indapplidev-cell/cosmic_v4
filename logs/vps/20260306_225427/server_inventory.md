# Server Inventory (VPS 185.216.87.26)

Report timestamp: 20260306_225427

## Scope
- Read-only diagnostics only.
- All remote commands were executed via `bash tools/vps.sh ...`.

## OS and resources
- User: `root` (`uid=0 gid=0`) [source: `logs/vps/20260306_225337/cmd.out.txt`]
- OS: Ubuntu 22.04.5 LTS (Jammy), kernel `5.15.0-164-generic` [source: `logs/vps/20260306_225359/cmd.out.txt`]
- Uptime: ~59 days [source: `logs/vps/20260306_225401/cmd.out.txt`]
- Memory: 1.9 GiB total, ~361 MiB used, ~120 MiB free, swap in use (~62 MiB) [source: `logs/vps/20260306_225401/cmd.out.txt`]
- Disk: `/dev/sda1` 40G total, 15G used, 24G free (~39%) [source: `logs/vps/20260306_225401/cmd.out.txt`]

## Network and listening ports
- Hostname: `p638409.kvmvps`
- Public IP: `185.216.87.26/24`
- Default route: via `185.216.87.1`
- DNS servers: `46.254.22.138`, `46.254.23.138`
[source: `logs/vps/20260306_225402/cmd.out.txt`]

Listening ports (key):
- `22/tcp` -> `sshd`
- `443/tcp` -> `xray`
- no `80/tcp` listener in captured output
[source: `logs/vps/20260306_225403/cmd.out.txt`, `logs/vps/20260306_225423/cmd.out.txt`]

## Docker inventory
- Docker: `28.5.1`
- Docker Compose: `v2.40.3`
[source: `logs/vps/20260306_225404/cmd.out.txt`]

Networks:
- `gamecom_net`, `infra_default`, default bridge/host/none
[source: `logs/vps/20260306_225407/cmd.out.txt`]

Volumes:
- `infra_postgres_data`
[source: `logs/vps/20260306_225408/cmd.out.txt`]

Containers (`docker ps -a`):
- `gamecom-db` (postgres:15-alpine): Up (healthy)
- `gamecom-engine` (infra-engine): Restarting (1)
- `infra-postgres-1` (postgres:16): Up (healthy)
- `infra-api-1` (cosmic-api:local): Up (healthy)
- `infra-cloudflared-1` (cloudflare/cloudflared): Restarting
[source: `logs/vps/20260306_225425/cmd.out.txt`, `logs/vps/20260306_225406/docker_ps.txt`]

## System services
- Running: `docker.service`, `ssh.service`, `xray.service` (among others)
[source: `logs/vps/20260306_225414/cmd.out.txt`]

- `docker.service`: active (running)
- `ssh.service`: active (running)
- `ufw.service`: active (exited)
[sources: `logs/vps/20260306_225415/cmd.out.txt`, `logs/vps/20260306_225417/cmd.out.txt`, `logs/vps/20260306_225418/cmd.out.txt`]

## Firewall / security observations
- `ufw status`: `inactive`
[source: `logs/vps/20260306_225420/cmd.out.txt`]

- `iptables` has Docker chains and default policies (`INPUT ACCEPT`, `FORWARD DROP`, `OUTPUT ACCEPT`)
[source: `logs/vps/20260306_225421/cmd.out.txt`]

- SSH journal shows repeated invalid-user/password attempts from external IPs (ongoing brute-force noise), alongside valid key logins.
[source: `logs/vps/20260306_225422/cmd.out.txt`]

## 443 ownership
- Port `443` is owned by `xray` process.
[source: `logs/vps/20260306_225423/cmd.out.txt`]

## Restart-loop focus (gamecom-engine)
- `gamecom-engine` is restarting with non-zero exit.
- Last logs show DB hostname resolution failure during Alembic/SQLAlchemy startup:
  - `socket.gaierror: [Errno -2] Name or service not known`
[source: `logs/vps/20260306_225427/engine_logs_tail300.txt`]

## Top 3 risks
1. `ufw` is inactive while SSH is internet-exposed on port 22 (elevated attack surface).
2. Active brute-force SSH attempts in journal; hardening/rate-limiting is advisable.
3. Two containers in restart-loop (`gamecom-engine`, `infra-cloudflared`) indicate service instability and possible configuration drift.

## Raw artifacts (this run)
- `logs/vps/20260306_225337/cmd.out.txt`
- `logs/vps/20260306_225359/cmd.out.txt`
- `logs/vps/20260306_225401/cmd.out.txt`
- `logs/vps/20260306_225402/cmd.out.txt`
- `logs/vps/20260306_225403/cmd.out.txt`
- `logs/vps/20260306_225404/cmd.out.txt`
- `logs/vps/20260306_225406/docker_ps.txt`
- `logs/vps/20260306_225407/cmd.out.txt`
- `logs/vps/20260306_225408/cmd.out.txt`
- `logs/vps/20260306_225409/cmd.out.txt`
- `logs/vps/20260306_225410/cmd.out.txt`
- `logs/vps/20260306_225414/cmd.out.txt`
- `logs/vps/20260306_225415/cmd.out.txt`
- `logs/vps/20260306_225417/cmd.out.txt`
- `logs/vps/20260306_225418/cmd.out.txt`
- `logs/vps/20260306_225420/cmd.out.txt`
- `logs/vps/20260306_225421/cmd.out.txt`
- `logs/vps/20260306_225422/cmd.out.txt`
- `logs/vps/20260306_225423/cmd.out.txt`
- `logs/vps/20260306_225425/cmd.out.txt`
- `logs/vps/20260306_225427/*`
