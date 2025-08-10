from app import db

async def report_coin(name: str, symbol: str | None, chain: str | None, contract: str | None, reasons: list[str], added_by: int):
    row = await db.fetchrow(
        """INSERT INTO coins (name, symbol, chain, contract_address, reasons, added_by)
           VALUES ($1,$2,$3,$4,$5,$6) RETURNING id""",
        name, symbol, chain, contract, reasons, added_by
    )
    return row["id"]

async def next_pending_coin():
    return await db.fetchrow("""SELECT * FROM coins WHERE status='pending' ORDER BY created_at ASC LIMIT 1""")

async def decide_coin(coin_id: int, moderator_id: int, approve: bool):
    status = "listed" if approve else "rejected"
    await db.execute(
        "UPDATE coins SET status=$1, decided_by=$2, decided_at=now() WHERE id=$3",
        status, moderator_id, coin_id
    )

async def find_coin(query: str):
    # Поиск по контракту или символу/имени
    row = await db.fetchrow(
        """SELECT * FROM coins
           WHERE contract_address = $1
              OR lower(symbol) = lower($1)
              OR lower(name) = lower($1)
           ORDER BY status='listed' DESC, created_at DESC
           LIMIT 1""",
        query
    )
    return row
