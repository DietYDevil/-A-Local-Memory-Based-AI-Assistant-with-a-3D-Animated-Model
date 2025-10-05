# Backend/MemoryManager.py
import sqlite3
import time
import json
from typing import List, Dict, Optional
import cohere  # pip install cohere
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
CohereAPIKey = env_vars.get("CohereAPIKey")
CohereModel  = env_vars.get("CohereModel")

class MemoryManager:
    def __init__(self, db_path="genni_memory.db", cohere_api_key: Optional[str] = None):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
        self.cohere = cohere.Client(cohere_api_key) if cohere_api_key else None

    def _init_db(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                ts REAL,
                compressed INTEGER DEFAULT 0
            )
        """)
        # FTS table for fast keyword match (FTS5)
        c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(content, content='messages', content_rowid='id')")
        c.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT,
                source_ids TEXT,
                ts REAL
            )
        """)
        self.conn.commit()

    def add_message(self, role: str, content: str) -> int:
        ts = time.time()
        c = self.conn.cursor()
        c.execute("INSERT INTO messages (role, content, ts) VALUES (?, ?, ?)", (role, content, ts))
        rowid = c.lastrowid
        c.execute("INSERT INTO messages_fts(rowid, content) VALUES (?, ?)", (rowid, content))
        self.conn.commit()
        return rowid

    def get_recent(self, n: int = 12) -> List[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT role, content, ts FROM messages WHERE compressed=0 ORDER BY ts DESC LIMIT ?", (n,))
        rows = c.fetchall()
        # return in chronological order (oldest first)
        return [{"role": r[0], "content": r[1], "ts": r[2]} for r in rows[::-1]]

    def search(self, query: str, k: int = 5) -> List[Dict]:
        # Basic FTS match — not semantic, but fast and dependency-free.
        c = self.conn.cursor()
        # match phrase; use quotes for phrase-match if necessary
        c.execute("SELECT rowid, content FROM messages_fts WHERE messages_fts MATCH ? LIMIT ?", (query, k))
        rows = c.fetchall()
        return [{"id": r[0], "content": r[1]} for r in rows]

    def list_uncompressed_ids(self, limit=200) -> List[int]:
        c = self.conn.cursor()
        c.execute("SELECT id FROM messages WHERE compressed=0 ORDER BY ts ASC LIMIT ?", (limit,))
        return [r[0] for r in c.fetchall()]

    def mark_compressed(self, ids: List[int]):
        if not ids:
            return
        c = self.conn.cursor()
        placeholders = ",".join("?" for _ in ids)
        c.execute(f"UPDATE messages SET compressed=1 WHERE id IN ({placeholders})", ids)
        self.conn.commit()

    def store_summary(self, summary_text: str, source_ids: List[int]):
        c = self.conn.cursor()
        c.execute("INSERT INTO summaries (summary, source_ids, ts) VALUES (?, ?, ?)",
                  (summary_text, json.dumps(source_ids), time.time()))
        self.conn.commit()

    # ------------ Cohere-based summarization --------------
    def summarize_messages_into_memory(self, ids: List[int]) -> Optional[str]:
        """
        Given a list of message ids, ask the model to summarize them into short memory facts and persona hints.
        Returns the summary text saved.
        """
        if not ids or not self.cohere:
            return None

        c = self.conn.cursor()
        placeholders = ",".join("?" for _ in ids)
        c.execute(f"SELECT role, content FROM messages WHERE id IN ({placeholders}) ORDER BY ts", ids)
        rows = c.fetchall()
        conv_text = "\n".join([f"{r[0]}: {r[1]}" for r in rows])

        prompt = (
            "You are a memory-compression assistant. "
            "Summarize the following conversation into:\n"
            "1) a short list of 6-10 facts (1 sentence each) that would be useful to remember about the user or context;\n"
            "2) a 1-2 sentence persona update describing how Genni should behave (tone, do/don't)\n\n"
            f"Conversation:\n{conv_text}\n\n"
            "Output JSON with keys: facts (list), persona (string)."
        )

        resp = self.cohere.chat.create(
            model=CohereModel,
            messages=[
                {"role": "system", "content": "You compress conversation into memory facts and persona rules."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        out_text = resp.choices[0].message["content"]
        # store the raw model output as summary (you can parse JSON if model returned JSON)
        self.store_summary(out_text, ids)
        # mark originals as compressed
        self.mark_compressed(ids)
        return out_text

    # Helper: get recent summary strings (for including in prompts)
    def get_recent_summaries_text(self, limit=5) -> str:
        c = self.conn.cursor()
        c.execute("SELECT summary, ts FROM summaries ORDER BY ts DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        return "\n".join([r[0] for r in rows])

    # Example high-level operation used by a periodic task
    def compress_old_if_needed(self, min_messages=30, batch_size=200):
        ids = self.list_uncompressed_ids(limit=batch_size)
        if len(ids) >= min_messages:
            return self.summarize_messages_into_memory(ids)
        return None
