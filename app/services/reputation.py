from app import db

async def ensure_user(user):
    await db.execute(
        """INSERT INTO users (user_id, username, first_name, last_name, language_code)
           VALUES ($1,$2,$3,$4,$5)
           ON CONFLICT (user_id) DO UPDATE SET
             username=EXCLUDED.username,
             first_name=EXCLUDED.first_name,
             last_name=EXCLUDED.last_name,
             language_code=EXCLUDED.language_code""",
        user.id, user.username, user.first_name, user.last_name, getattr(user, "language_code", None)
    )
    await db.execute(
        """INSERT INTO reputations (user_id) VALUES ($1)
           ON CONFLICT (user_id) DO NOTHING""",
        user.id
    )

async def accepted_terms(user_id: int):
    return await db.fetchval("SELECT accepted_terms_at FROM users WHERE user_id=$1", user_id) is not None

async def mark_accept_terms(user_id: int, version: str):
    await db.execute("UPDATE users SET accepted_terms_at=now() WHERE user_id=$1", user_id)
    await db.execute(
        """INSERT INTO agreements (user_id, terms_version, accepted_at)
           VALUES ($1, $2, now())
           ON CONFLICT (user_id) DO UPDATE SET terms_version=EXCLUDED.terms_version, accepted_at=EXCLUDED.accepted_at""",
        user_id, version
    )

async def get_rep(user_id: int):
    row = await db.fetchrow(
        "SELECT score, praises_count, reports_count FROM reputations WHERE user_id=$1", user_id
    )
    if not row:
        return {"score": 0, "praises": 0, "reports": 0}
    return {"score": row["score"], "praises": row["praises_count"], "reports": row["reports_count"]}

async def create_case(case_type: str, author_id: int, target_id: int, reason: str, evidence: str | None):
    row = await db.fetchrow(
        """INSERT INTO cases (type, target_user_id, author_user_id, reason, evidence)
           VALUES ($1,$2,$3,$4,$5) RETURNING id""",
        case_type, target_id, author_id, reason, evidence
    )
    return row["id"]

async def next_pending_case():
    return await db.fetchrow(
        """SELECT c.*, u.username as target_username, a.username as author_username
           FROM cases c
           JOIN users u ON u.user_id = c.target_user_id
           JOIN users a ON a.user_id = c.author_user_id
           WHERE c.status='pending'
           ORDER BY c.created_at ASC
           LIMIT 1"""
    )

async def decide_case(case_id: int, moderator_id: int, approve: bool, decision_reason: str | None):
    status = "approved" if approve else "rejected"
    await db.execute(
        """UPDATE cases SET status=$1, moderator_user_id=$2, decision_reason=$3, decided_at=now()
           WHERE id=$4""",
        status, moderator_id, decision_reason, case_id
    )
    if approve:
        case = await db.fetchrow("SELECT type, target_user_id FROM cases WHERE id=$1", case_id)
        if case and case["type"] == "report":
            await db.execute(
                """UPDATE reputations SET score=score-10, reports_count=reports_count+1, updated_at=now()
                   WHERE user_id=$1""",
                case["target_user_id"]
            )
        elif case and case["type"] == "praise":
            await db.execute(
                """UPDATE reputations SET score=score+5, praises_count=praises_count+1, updated_at=now()
                   WHERE user_id=$1""",
                case["target_user_id"]
            )

async def create_appeal(case_id: int, appellant_id: int, message: str):
    row = await db.fetchrow(
        """INSERT INTO appeals (case_id, appellant_user_id, message)
           VALUES ($1,$2,$3) RETURNING id""",
        case_id, appellant_id, message
    )
    return row["id"]

async def next_pending_appeal():
    return await db.fetchrow(
        """SELECT ap.*, c.type as case_type, c.status as case_status
           FROM appeals ap
           JOIN cases c ON c.id = ap.case_id
           WHERE ap.status='pending'
           ORDER BY ap.created_at ASC
           LIMIT 1"""
    )

async def decide_appeal(appeal_id: int, moderator_id: int, approve: bool, decision_reason: str | None):
    status = "approved" if approve else "rejected"
    await db.execute(
        """UPDATE appeals SET status=$1, moderator_user_id=$2, decision_reason=$3, decided_at=now()
           WHERE id=$4""",
        status, moderator_id, decision_reason, appeal_id
    )
