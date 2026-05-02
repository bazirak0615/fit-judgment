import json
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "app.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS weight_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                weights_json TEXT NOT NULL,
                hard_gates_json TEXT,
                created_at TEXT NOT NULL,
                used_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jd_title TEXT,
                candidate_label TEXT,
                jd_structured_json TEXT NOT NULL,
                candidate_structured_json TEXT NOT NULL,
                weights_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                overall_score REAL,
                recommendation TEXT,
                created_at TEXT NOT NULL
            );
            """
        )


def save_preset(name: str, weights_json: dict, hard_gates_json: dict) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO weight_presets (name, weights_json, hard_gates_json, created_at) VALUES (?, ?, ?, ?)",
            (
                name,
                json.dumps(weights_json, ensure_ascii=False),
                json.dumps(hard_gates_json, ensure_ascii=False),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        return cur.lastrowid


def list_presets() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, weights_json, hard_gates_json, created_at, used_count FROM weight_presets ORDER BY created_at DESC"
        ).fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "name": r["name"],
                "weights": json.loads(r["weights_json"]),
                "hard_gates": json.loads(r["hard_gates_json"] or "{}"),
                "created_at": r["created_at"],
                "used_count": r["used_count"],
            }
        )
    return out


def delete_preset(preset_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM weight_presets WHERE id = ?", (preset_id,))


def bump_preset_usage(preset_id: int) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE weight_presets SET used_count = used_count + 1 WHERE id = ?",
            (preset_id,),
        )


def save_evaluation(
    jd_title: str,
    candidate_label: str,
    jd_structured: dict,
    candidate_structured: dict,
    weights: dict,
    result: dict,
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO evaluations
               (jd_title, candidate_label, jd_structured_json, candidate_structured_json,
                weights_json, result_json, overall_score, recommendation, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                jd_title,
                candidate_label,
                json.dumps(jd_structured, ensure_ascii=False),
                json.dumps(candidate_structured, ensure_ascii=False),
                json.dumps(weights, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                result.get("overall_score"),
                result.get("recommendation"),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        return cur.lastrowid


def list_evaluations(limit: int = 50) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, jd_title, candidate_label, overall_score, recommendation, created_at FROM evaluations ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_evaluation_detail(eval_id: int) -> dict | None:
    """단일 평가의 전체 상세 (jd/후보자/result/weights JSON 포함)."""
    with _connect() as conn:
        row = conn.execute(
            """SELECT id, jd_title, candidate_label, jd_structured_json, candidate_structured_json,
                      weights_json, result_json, overall_score, recommendation, created_at
               FROM evaluations WHERE id = ?""",
            (eval_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "jd_title": row["jd_title"],
        "candidate_label": row["candidate_label"],
        "jd_structured": json.loads(row["jd_structured_json"]),
        "candidate_structured": json.loads(row["candidate_structured_json"]),
        "weights": json.loads(row["weights_json"]),
        "result": json.loads(row["result_json"]),
        "overall_score": row["overall_score"],
        "recommendation": row["recommendation"],
        "created_at": row["created_at"],
    }


def list_evaluations_grouped(limit: int = 200) -> dict[str, list[dict]]:
    """JD 타이틀별로 그룹핑된 평가 이력. {jd_title: [eval_dict, ...]}"""
    with _connect() as conn:
        rows = conn.execute(
            """SELECT id, jd_title, candidate_label, overall_score, recommendation, created_at
               FROM evaluations ORDER BY jd_title, created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    grouped: dict[str, list[dict]] = {}
    for r in rows:
        title = r["jd_title"] or "(타이틀 없음)"
        grouped.setdefault(title, []).append(dict(r))
    return grouped


def delete_evaluation(eval_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM evaluations WHERE id = ?", (eval_id,))
