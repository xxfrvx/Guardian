from app import db
import logging
import asyncio
import time
import os
import random
from typing import Any, Awaitable, Callable, Optional

log = logging.getLogger(__name__)

# Таймаут клиента для каждого запроса (сек). ВНИМАНИЕ:
# низкие значения могут приводить к отменам и "connection reset by peer" на стороне сервера.
# Можно отключить клиентский таймаут, установив DB_TIMEOUT=0.
DB_TIMEOUT = float(os.getenv("DB_TIMEOUT", "5.0"))

# Кол-во попыток при временных ошибках сети/соединения
DB_RETRIES = int(os.getenv("DB_RETRIES", "3"))

# Максимальная задержка между ретраями
DB_BACKOFF_MAX = float(os.getenv("DB_BACKOFF_MAX", "4.0"))

# Таймаут пинга (короче основного)
DB_PING_TIMEOUT = min(DB_TIMEOUT if DB_TIMEOUT > 0 else 1.0, 2.0)


# ========== ВСПОМОГАТЕЛЬНЫЕ УТИЛИТЫ ==========

async def _await_with_timing(awaitable: Awaitable[Any], label: str) -> Any:
    """
    Оборачивает awaitable таймером и (опционально) клиентским таймаутом.
    Чтобы исключить жёсткие отмены (и "reset by peer"), выставь DB_TIMEOUT=0.
    """
    start = time.perf_counter()
    try:
        if DB_TIMEOUT and DB_TIMEOUT > 0:
            result = await asyncio.wait_for(awaitable, timeout=DB_TIMEOUT)
        else:
            result = await awaitable
        elapsed = (time.perf_counter() - start) * 1000
        log.info("%s OK (%.1f ms)", label, elapsed)
        return result
    except asyncio.TimeoutError:
        elapsed = (time.perf_counter() - start) * 1000
        log.error("%s TIMEOUT after %.1f ms", label, elapsed)
        raise
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        log.exception("%s FAILED after %.1f ms", label, elapsed)
        raise


async def _ping_db_once() -> None:
    """Быстрый пинг соединения: раннее выявление обрыва перед основной операцией."""
    try:
        if DB_PING_TIMEOUT and DB_PING_TIMEOUT > 0:
            await asyncio.wait_for(db.fetchval("SELECT 1"), timeout=DB_PING_TIMEOUT)
        else:
            await db.fetchval("SELECT 1")
        log.debug("DB ping OK")
    except Exception as e:
        # Пинг не фатален: основная операция всё равно попробует выполниться (и при необходимости уйдёт в ретрай).
        log.warning("DB ping FAILED: %s: %s", type(e).__name__, e)


TransientErrors = (OSError, ConnectionError, asyncio.TimeoutError)


async def _db_call_with_retry(label: str, op_factory: Callable[[], Awaitable[Any]], *, retries: int = DB_RETRIES) -> Any:
    """
    Универсальный ретрай-раннер для DB-операций.
    - Пинг перед попыткой
    - Экспоненциальный бэкофф с джиттером на временных ошибках сети/таймаутах
    """
    attempt = 0
    last_err: Optional[BaseException] = None

    while attempt < retries:
        attempt += 1
        await _ping_db_once()
        try:
            return await _await_with_timing(op_factory(), f"{label} (attempt {attempt}/{retries})")
        except TransientErrors as e:
            last_err = e
            backoff = min((2 ** (attempt - 1)), DB_BACKOFF_MAX) + random.uniform(0, 0.3)
            log.warning("%s transient error: %s: %s -> retry in %.2fs", label, type(e).__name__, e, backoff)
            await asyncio.sleep(backoff)
            continue
        except Exception as e:
            # Нефатальные бизнес-ошибки лучше не ретраить, но мы не различаем тут типы —
            # если это не сеть/таймаут, сразу пробрасываем.
            raise

    # Все попытки исчерпаны
    if last_err:
        log.error("%s exhausted after %d attempts: %s: %s", label, retries, type(last_err).__name__, last_err)
        raise last_err
    raise RuntimeError(f"{label} exhausted without specific error")


# ========== ПУБЛИЧНЫЕ ФУНКЦИИ ДЛЯ БОТА ==========

async def ensure_user(user):
    """
    Обновляет/создаёт пользователя и гарантирует запись в reputations.
    Идемпотентно.
    """
    log.info("ensure_user user_id=%s username=%s", user.id, user.username)

    await _db_call_with_retry(
        "SQL users UPSERT",
        lambda: db.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, language_code)
            VALUES ($1,$2,$3,$4,$5)
            ON CONFLICT (user_id) DO UPDATE SET
              username=EXCLUDED.username,
              first_name=EXCLUDED.first_name,
              last_name=EXCLUDED.last_name,
              language_code=EXCLUDED.language_code
            """,
            user.id, user.username, user.first_name, user.last_name, getattr(user, "language_code", None)
        )
    )

    await _db_call_with_retry(
        "SQL reputations ENSURE",
        lambda: db.execute(
            """
            INSERT INTO reputations (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user.id
        )
    )


async def accepted_terms(user_id: int) -> bool:
    """
    Проверяет, принимал ли пользователь условия (по полю accepted_terms_at в users).
    """
    log.info("accepted_terms? user_id=%s", user_id)
    val = await _db_call_with_retry(
        "SQL users SELECT accepted_terms_at",
        lambda: db.fetchval("SELECT accepted_terms_at FROM users WHERE user_id=$1", user_id)
    )
    return val is not None


async def mark_accept_terms(user_id: int, version: str) -> None:
    """
    Помечает согласие с условиями:
    - Апдейтит users.accepted_terms_at
    - UPSERT в agreements (user_id уникален), чтобы хранить актуальную версию.
    Операции идемпотентны и безопасны для повторного выполнения в случае ретрая.
    """
    log.info("mark_accept_terms user_id=%s version=%s", user_id, version)

    # Выполним обе операции в одном ретрай-блоке: они идемпотентны.
    async def _op():
        # 1) Обновить users.accepted_terms_at
        await db.execute(
            "UPDATE users SET accepted_terms_at=now() WHERE user_id=$1",
            user_id
        )
        # 2) Зафиксировать/обновить версию в agreements
        await db.execute(
            """
            INSERT INTO agreements (user_id, terms_version, accepted_at)
            VALUES ($1, $2, now())
            ON CONFLICT (user_id) DO UPDATE
              SET terms_version=EXCLUDED.terms_version,
                  accepted_at=EXCLUDED.accepted_at
            """,
            user_id, version
        )

    await _db_call_with_retry("SQL accept terms (users+agreements)", _op)


async def get_rep(user_id: int) -> dict:
    """
    Возвращает текущую репутацию пользователя.
    Если записи нет — безопасно возвращает нули.
    """
    row = await _db_call_with_retry(
        "SQL reputations SELECT",
        lambda: db.fetchrow(
            "SELECT score, praises_count, reports_count FROM reputations WHERE user_id=$1",
            user_id
        )
    )
    if not row:
        return {"score": 0, "praises": 0, "reports": 0}
    return {"score": row["score"], "praises": row["praises_count"], "reports": row["reports_count"]}


async def create_case(case_type: str, author_id: int, target_id: int, reason: str, evidence: Optional[str]):
    """
    Создаёт кейс (жалоба/похвала) и возвращает id.
    """
    row = await _db_call_with_retry(
        "SQL cases INSERT",
        lambda: db.fetchrow(
            """
            INSERT INTO cases (type, target_user_id, author_user_id, reason, evidence)
            VALUES ($1,$2,$3,$4,$5)
            RETURNING id
            """,
            case_type, target_id, author_id, reason, evidence
        )
    )
    return row["id"]


async def next_pending_case():
    """
    Возвращает следующий кейс в статусе pending (с присоединёнными именами).
    """
    return await _db_call_with_retry(
        "SQL cases NEXT PENDING",
        lambda: db.fetchrow(
            """
            SELECT c.*, u.username as target_username, a.username as author_username
            FROM cases c
            JOIN users u ON u.user_id = c.target_user_id
            JOIN users a ON a.user_id = c.author_user_id
            WHERE c.status='pending'
            ORDER BY c.created_at ASC
            LIMIT 1
            """
        )
    )


async def decide_case(case_id: int, moderator_id: int, approve: bool, decision_reason: Optional[str]):
    """
    Решает кейс.
    - reject: просто помечаем кейс отклонённым, без изменений репутации.
    - approve: атомарно обновляем статус и модифицируем репутацию только если кейс был pending.
      Сделано одним SQL через CTE, чтобы избежать двойных инкрементов при повторах.
    """
    if not approve:
        await _db_call_with_retry(
            "SQL cases REJECT",
            lambda: db.execute(
                """
                UPDATE cases
                   SET status='rejected',
                       moderator_user_id=$2,
                       decision_reason=$3,
                       decided_at=now()
                 WHERE id=$1
                """,
                case_id, moderator_id, decision_reason
            )
        )
        return

    # Approve + репутация — одним SQL.
    await _db_call_with_retry(
        "SQL cases APPROVE + reputations UPDATE",
        lambda: db.execute(
            """
            WITH updated AS (
                UPDATE cases
                   SET status='approved',
                       moderator_user_id=$2,
                       decision_reason=$3,
                       decided_at=now()
                 WHERE id=$1 AND status='pending'
                 RETURNING type, target_user_id
            )
            UPDATE reputations r
               SET score = r.score
                        + CASE
                            WHEN u.type = 'report' THEN -10
                            WHEN u.type = 'praise' THEN  5
                            ELSE 0
                          END,
                   reports_count = r.reports_count + CASE WHEN u.type='report' THEN 1 ELSE 0 END,
                   praises_count = r.praises_count + CASE WHEN u.type='praise' THEN 1 ELSE 0 END,
                   updated_at = now()
              FROM updated u
             WHERE r.user_id = u.target_user_id
            """,
            case_id, moderator_id, decision_reason
        )
    )


async def create_appeal(case_id: int, appellant_id: int, message: str):
    """
    Создаёт апелляцию и возвращает id.
    """
    row = await _db_call_with_retry(
        "SQL appeals INSERT",
        lambda: db.fetchrow(
            """
            INSERT INTO appeals (case_id, appellant_user_id, message)
            VALUES ($1,$2,$3)
            RETURNING id
            """,
            case_id, appellant_id, message
        )
    )
    return row["id"]


async def next_pending_appeal():
    """
    Возвращает следующую апелляцию в статусе pending.
    """
    return await _db_call_with_retry(
        "SQL appeals NEXT PENDING",
        lambda: db.fetchrow(
            """
            SELECT ap.*, c.type as case_type, c.status as case_status
              FROM appeals ap
              JOIN cases c ON c.id = ap.case_id
             WHERE ap.status='pending'
             ORDER BY ap.created_at ASC
             LIMIT 1
            """
        )
    )


async def decide_appeal(appeal_id: int, moderator_id: int, approve: bool, decision_reason: Optional[str]):
    """
    Решает апелляцию (только статус, без влияния на репутацию).
    """
    status = "approved" if approve else "rejected"
    await _db_call_with_retry(
        "SQL appeals DECIDE",
        lambda: db.execute(
            """
            UPDATE appeals
               SET status=$1,
                   moderator_user_id=$2,
                   decision_reason=$3,
                   decided_at=now()
             WHERE id=$4
            """,
            status, moderator_id, decision_reason, appeal_id
        )
    )
