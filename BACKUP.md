# Inventory AI — Backup & restore (local Postgres)

Docker Postgres volume: `inventory_ai_pgdata` (see `docker-compose.yml`). Host port **5435**.

## Dump

```bash
docker compose exec -T db pg_dump -U inventory -d inventory_ai --format=custom -f /tmp/inventory_ai.dump
docker compose cp db:/tmp/inventory_ai.dump ./backups/inventory_ai-$(date +%Y%m%d).dump
```

Plain SQL alternative:

```bash
docker compose exec -T db pg_dump -U inventory -d inventory_ai > backups/inventory_ai.sql
```

## Restore

```bash
docker compose exec -T db pg_restore -U inventory -d inventory_ai --clean --if-exists /tmp/inventory_ai.dump
# or after copying the dump into the container
```

For plain SQL:

```bash
docker compose exec -T db psql -U inventory -d inventory_ai < backups/inventory_ai.sql
```

## After restore

```bash
cd backend
alembic upgrade head
# Re-seed only if the dump is empty / you want demo data again:
# python seed.py
```

## Notes

- Keep dumps off git; add `backups/` to local ignore if needed
- Demo JWT secret and connector token are env-only — rotate in `.env` after restore if sharing dumps
- This is portfolio ops guidance, not a managed HA backup plan
