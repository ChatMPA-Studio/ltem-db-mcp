"""Optimize ltem_historical_database for the query patterns tools/*.py uses.

THE PLAN — four phases, run in order, each skipped if already applied
-----------------------------------------------------------------------
Phase 1 — Fix column types. Label, Region, Reef, MPA and Transect are typed
  TEXT (up to 65535 bytes) but hold short categorical values (Region: 14
  distinct values, 14 chars max; Transect: 9 distinct values, 1 char max —
  measured against the live table). MySQL/InnoDB refuses to index a
  TEXT/BLOB column without an explicit prefix length (error 1170), so this
  has to happen before Phase 3, and it's the right fix anyway — VARCHAR is
  smaller on disk and gives a full-value index instead of a truncated
  prefix one.

Phase 2 — Add a PRIMARY KEY. The table has none today (confirmed via
  SHOW INDEX — zero rows), so InnoDB clusters it on a hidden internal key
  instead. Adds a surrogate `id BIGINT AUTO_INCREMENT PRIMARY KEY`.

Phase 3 — Add the missing secondary indexes. Counting every WHERE/GROUP BY
  clause across tools/*.py shows the same few patterns repeated dozens of
  times:
    - WHERE Label = ... [AND Region = ...] [AND Year = ...]   (Label/Region/
      Year are the three most common equality filters, in that order)
    - GROUP BY Year, Region, Reef, Transect                    (the
      "transect identity" almost every tool aggregates to before averaging
      further)
    - WHERE MPA = ...                                          (protection-
      level comparisons in mpa_effectiveness.py / report_generator.py)
  Without a matching index, every one of those queries does a full table
  scan — measured at 3.08s for a single Region+Year filter on 431,692 rows.
  See PROPOSED_INDEXES below for the exact column lists.

Phase 4 — ANALYZE TABLE. Refreshes the optimizer's cardinality statistics
  so it actually chooses the new indexes instead of still costing plans as
  if the table were unindexed.

WHY THIS IS A SEPARATE SCRIPT, NOT AN MCP TOOL
------------------------------------------------
mcp_server/security.py explicitly refuses ALTER/CREATE/MODIFY for any query
that goes through the app (see DENIED_KEYWORDS), and this script does not
weaken that: it never imports mcp_server.db or mcp_server.security, and
never touches the app's .env. It takes its own admin credentials (with
ALTER/INDEX privilege) as an explicit argument, at run time only.

Note this is a real gap today, not a formality: the credential the app
itself uses in production (checked via SHOW GRANTS) is `admin`@`%` with
full `*.*` privileges (DROP, CREATE USER, GRANT OPTION, `rds_superuser_role`)
— there is no separate scoped `mcp_ltem_ro` read-only MySQL user yet. Until
one exists, `mcp_server/security.py`'s SQL whitelist is the *only* thing
stopping a write through the app; it is not backed by a matching DB-level
grant. That's a separate follow-up, not something this script fixes.

USAGE
-----
    # 1. See the full plan across all four phases (default — no changes made)
    python scripts/add_db_indexes.py --database-url mysql://admin:pass@host:3306/ecological_monitoring

    # 2. Actually apply it, phase by phase, in order (asks for confirmation once)
    python scripts/add_db_indexes.py --database-url mysql://admin:pass@host:3306/ecological_monitoring --apply

    # Or export DB_ADMIN_URL instead of passing --database-url every time.

GOTCHA — Docker bridge networking against this RDS instance silently hangs.
Connecting from inside a container on the default `bridge` network stalls
indefinitely partway through the MySQL handshake (TCP connects fine, the
auth exchange never completes) — no error, no timeout, just hangs. Verified
against this exact host. Run with `--network host`, or outside Docker
entirely, if this script seems to hang after "Connecting...".

Phase 3's indexes are created with ALGORITHM=INPLACE, LOCK=NONE (online
DDL, reads and writes both proceed while the index builds). Phases 1 and 2
rebuild the table (column type changes and adding a PRIMARY KEY cannot be
done as pure metadata changes) — writes block for that phase's duration;
reads do not. On this table's current size (431K rows / ~169MB) that
should be low tens of seconds, but run it in a low-traffic window anyway.
Every phase is skipped automatically if already applied — safe to re-run.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import pymysql

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

TABLE = "ltem_historical_database"

# --- Phase 1: column types --------------------------------------------------
# TEXT -> VARCHAR for exactly the columns Phase 3 needs to index (MySQL
# refuses to index TEXT/BLOB without a prefix length). Sizes are the
# measured max length on the live table today, rounded up for headroom —
# not guessed:
#   Label:    2 distinct values,   max  3 chars
#   Region:  14 distinct values,   max 14 chars
#   Reef:   358 distinct values,   max 35 chars
#   MPA:     21 distinct values,   max 74 chars
#   Transect: 9 distinct values,   max  1 char
COLUMN_TYPE_CHANGES: dict[str, str] = {
    "Label": "VARCHAR(10)",
    "Region": "VARCHAR(20)",
    "Reef": "VARCHAR(50)",
    "MPA": "VARCHAR(100)",
    "Transect": "VARCHAR(5)",
}

# --- Phase 3: secondary indexes ---------------------------------------------
# name -> ordered column tuple. Order matters (leftmost-prefix rule).
PROPOSED_INDEXES: dict[str, tuple[str, ...]] = {
    # WHERE Label = %s [AND Region = %s] [AND Year = %s] — by far the most
    # common filter combo (report_generator.py, biomass.py, invertebrates.py,
    # data_access.py all lead with this).
    "idx_ltem_label_region_year": ("Label", "Region", "Year"),
    # GROUP BY Year, Region, Reef, Transect (or a prefix of it) — the
    # transect-identity aggregation every biomass/abundance/richness tool
    # does before averaging further.
    "idx_ltem_year_region_reef_transect": ("Year", "Region", "Reef", "Transect"),
    # Same four columns, Region first. Not redundant with the index above:
    # none of the other indexes lead with Region, so `WHERE Region = %s`
    # without a Label or Year alongside it (biomass.py's regional trend,
    # data_access.py's get_reefs) had no index it could seek on. Measured
    # on a local copy: without this, the optimizer scans the whole
    # Year-leading index to avoid a filesort and ends up 2.3x SLOWER than
    # the plain table scan it did before any of these indexes existed.
    # With it, the same query is 2.5x faster than baseline instead.
    "idx_ltem_region_year_reef_transect": ("Region", "Year", "Reef", "Transect"),
    # WHERE MPA = %s [AND Year = %s] — protection-level comparisons.
    "idx_ltem_mpa_year": ("MPA", "Year"),
    # WHERE Reef = %s used on its own (get_reefs, get_observations) without
    # Region/Year as a leftmost prefix.
    "idx_ltem_reef": ("Reef",),
}


def _parse_db_url(url: str) -> dict:
    parsed = urlparse(url)
    if not parsed.hostname or not parsed.username:
        raise ValueError(
            "--database-url must look like mysql://user:pass@host:port/dbname"
        )
    return dict(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password or "",
        database=parsed.path.lstrip("/") or "ecological_monitoring",
    )


# --- Phase 1: column types ---------------------------------------------


def get_column_types(conn, table: str) -> dict[str, str]:
    """Return {column_name: DATA_TYPE} (e.g. 'text', 'varchar', 'double')."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
            (table,),
        )
        return dict(cur.fetchall())


def plan_column_type_changes(column_types: dict[str, str]) -> dict[str, str]:
    """COLUMN_TYPE_CHANGES entries whose column is still TEXT today."""
    return {
        col: new_type
        for col, new_type in COLUMN_TYPE_CHANGES.items()
        if column_types.get(col) == "text"
    }


def apply_column_type_changes(conn, table: str, changes: dict[str, str]) -> None:
    """One ALTER TABLE with every MODIFY — one table rebuild, not five.

    Changing a column's type is a real data rewrite (every row's value for
    that column gets re-encoded), so unlike Phase 3's indexes this cannot
    run as ALGORITHM=INPLACE, LOCK=NONE — MySQL rejects that combination
    for a type change. It still runs online in the sense that matters here:
    LOCK=SHARED lets reads continue against the table while it rebuilds;
    writes queue until it finishes.
    """
    modify_list = ", ".join(
        f"MODIFY `{col}` {new_type}" for col, new_type in changes.items()
    )
    sql = f"ALTER TABLE `{table}` {modify_list}, ALGORITHM=COPY, LOCK=SHARED"
    print(f"\n-> {sql}")
    started = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"   done in {time.perf_counter() - started:.1f}s")


# --- Phase 2: primary key ------------------------------------------------


def has_primary_key(conn, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s "
            "AND INDEX_NAME = 'PRIMARY' LIMIT 1",
            (table,),
        )
        return cur.fetchone() is not None


def apply_primary_key(conn, table: str) -> None:
    """Adding a PRIMARY KEY rebuilds the table's clustered index. This runs
    INPLACE (no full table copy), but not lock-free: MySQL assigns the
    auto-increment values itself and rejects LOCK=NONE for that outright
    ("Adding an auto-increment column requires a lock", error 1846), so
    LOCK=SHARED it is — reads proceed, writes block for the duration."""
    sql = (
        f"ALTER TABLE `{table}` ADD COLUMN id BIGINT AUTO_INCREMENT PRIMARY KEY FIRST, "
        "ALGORITHM=INPLACE, LOCK=SHARED"
    )
    print(f"\n-> {sql}")
    started = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"   done in {time.perf_counter() - started:.1f}s")


# --- Phase 3: secondary indexes ------------------------------------------


def get_existing_indexes(conn, table: str) -> dict[str, tuple[str, ...]]:
    """Return {index_name: (col1, col2, ...)} ordered by position in the index."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX "
            "FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s "
            "ORDER BY INDEX_NAME, SEQ_IN_INDEX",
            (table,),
        )
        rows = cur.fetchall()

    by_name: dict[str, list[str]] = {}
    for name, column, _seq in rows:
        by_name.setdefault(name, []).append(column)
    return {name: tuple(cols) for name, cols in by_name.items()}


def plan_missing_indexes(
    existing: dict[str, tuple[str, ...]]
) -> dict[str, tuple[str, ...]]:
    """Proposed indexes not already served by an existing index's leftmost prefix."""
    existing_column_tuples = list(existing.values())
    missing = {}
    for name, cols in PROPOSED_INDEXES.items():
        already_covered = any(
            existing_cols[: len(cols)] == cols for existing_cols in existing_column_tuples
        )
        if not already_covered:
            missing[name] = cols
    return missing


def create_index(conn, table: str, name: str, columns: tuple[str, ...]) -> None:
    col_list = ", ".join(f"`{c}`" for c in columns)
    sql = f"ALTER TABLE `{table}` ADD INDEX `{name}` ({col_list}), ALGORITHM=INPLACE, LOCK=NONE"
    print(f"\n-> {sql}")
    started = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"   done in {time.perf_counter() - started:.1f}s")


# --- Phase 4: refresh optimizer statistics --------------------------------


def analyze_table(conn, table: str) -> None:
    """New indexes are invisible to the optimizer's cost estimates until
    this runs — it still has the pre-index cardinality stats otherwise."""
    sql = f"ANALYZE TABLE `{table}`"
    print(f"\n-> {sql}")
    with conn.cursor() as cur:
        cur.execute(sql)
        for row in cur.fetchall():
            print(f"   {row}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Optimize ltem_historical_database (column types, primary key, "
            "indexes, stats) — see module docstring for the four-phase plan."
        )
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DB_ADMIN_URL"),
        help=(
            "mysql://user:pass@host:port/dbname for a user with ALTER/INDEX "
            "privilege. Falls back to the DB_ADMIN_URL env var. Do not reuse "
            "this for the app's own runtime credential afterwards — this one "
            "should stay a separate, more privileged, short-lived credential."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply the plan. Without this flag, only prints it (dry run).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt when --apply is used.",
    )
    args = parser.parse_args()

    if not args.database_url:
        parser.error("--database-url is required (or set the DB_ADMIN_URL env var)")

    print("Connecting...")  # first thing printed — see the Docker networking
    # gotcha in the module docstring if this is the last line you see.
    conn = pymysql.connect(**_parse_db_url(args.database_url), connect_timeout=10)
    try:
        column_types = get_column_types(conn, TABLE)
        type_changes = plan_column_type_changes(column_types)

        pk_exists = has_primary_key(conn, TABLE)

        existing_indexes = get_existing_indexes(conn, TABLE)
        missing_indexes = plan_missing_indexes(existing_indexes)

        print(f"\nPlan for `{TABLE}`:")
        print(
            f"  Phase 1 (column types): "
            + (
                "nothing to do"
                if not type_changes
                else f"{len(type_changes)} column(s) — "
                + ", ".join(f"{c} TEXT -> {t}" for c, t in type_changes.items())
            )
        )
        print(
            "  Phase 2 (primary key): "
            + ("already exists" if pk_exists else "add `id BIGINT AUTO_INCREMENT PRIMARY KEY`")
        )
        print(
            f"  Phase 3 (indexes): "
            + (
                "nothing to do"
                if not missing_indexes
                else f"{len(missing_indexes)} index(es) — "
                + ", ".join(
                    f"{name} ({', '.join(cols)})" for name, cols in missing_indexes.items()
                )
            )
        )

        anything_to_do = bool(type_changes) or not pk_exists or bool(missing_indexes)
        print(f"  Phase 4 (ANALYZE TABLE): {'will run' if anything_to_do else 'skipped'}")

        if not anything_to_do:
            print("\nNothing to do — the table already matches the plan.")
            return

        if not args.apply:
            print("\nDry run only — re-run with --apply to actually apply this plan.")
            return

        if not args.yes:
            answer = input(
                "\nThis runs the four phases above against a live database, in "
                "order. Phases 1-2 briefly block writes (not reads) while the "
                "table rebuilds; Phase 3's indexes don't block anything. "
                "Continue? [y/N] "
            )
            if answer.strip().lower() != "y":
                print("Aborted.")
                return

        if type_changes:
            print("\n=== Phase 1: column types ===")
            try:
                apply_column_type_changes(conn, TABLE, type_changes)
            except Exception as exc:
                print(f"   FAILED: {exc}")
                print("\nAborting — Phase 3's indexes need Phase 1 to have succeeded.")
                sys.exit(1)

        if not pk_exists:
            print("\n=== Phase 2: primary key ===")
            try:
                apply_primary_key(conn, TABLE)
            except Exception as exc:
                print(f"   FAILED: {exc}")
                sys.exit(1)

        failures = []
        if missing_indexes:
            print("\n=== Phase 3: indexes ===")
            for name, cols in missing_indexes.items():
                try:
                    create_index(conn, TABLE, name, cols)
                except Exception as exc:
                    print(f"   FAILED: {exc}")
                    failures.append(name)

        print("\n=== Phase 4: refresh statistics ===")
        analyze_table(conn, TABLE)

        if failures:
            print(f"\n{len(failures)} index(es) failed: {', '.join(failures)}")
            sys.exit(1)
        print("\nPlan applied successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
