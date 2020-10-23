import json
import sqlite3 as sl
from collections import namedtuple
from os import path
from pathlib import Path

db_name = 'packs.db'

PackRecord = namedtuple('PackRecord', 'id, name, sc_version, pack_version, pack_v_code, changelog')
KnownBugRecord = namedtuple('KnownBugRecord', 'id, category, description')


def create_db():
    con.execute("""
            CREATE TABLE PACKS (
                "id"	INTEGER,
                "name"	TEXT NOT NULL UNIQUE,
                "sc_version"	TEXT NOT NULL,
                "pack_version"	TEXT NOT NULL,
                "pack_v_code"	INTEGER NOT NULL,
                "changelog"     TEXT NOT NULL,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
        """)

    con.execute("""
            CREATE TABLE "KNOWN_BUGS" (
                "id"	INTEGER,
                "category"	TEXT NOT NULL,
                "description"	TEXT NOT NULL,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
        """)

    con.execute("""
            CREATE TABLE "KNOWN_BUGS_JOIN" (
                "pack_id"	INTEGER,
                "bug_id"	INTEGER,
                FOREIGN KEY("bug_id") REFERENCES "KNOWN_BUGS"("id") ON DELETE CASCADE,
                FOREIGN KEY("pack_id") REFERENCES "PACKS"("id") ON DELETE CASCADE
            );
    """)


def add_sample_data():
    con.execute("""
        INSERT INTO PACKS (name, sc_version, pack_version, pack_v_code, changelog) 
        VALUES("Pack_v1", "10.48.5.0", "1.2.0", 10, "Updated for 10.48.5.0")
    """)
    con.execute("""
        INSERT INTO PACKS (name, sc_version, pack_version, pack_v_code, changelog) 
        VALUES("Pack_v2", "10.48.5.0", "1.2.1", 11, "Fixed Saving")
    """)
    con.execute("""
        INSERT INTO PACKS (name, sc_version, pack_version, pack_v_code, changelog) 
        VALUES("Pack_v3", "10.49.5.0", "1.2.3", 12, "Updated for 10.49")
    """)
    con.execute("""
        INSERT INTO KNOWN_BUGS (category, description) VALUES("Saving", "Currently does not work")
    """)
    con.execute(f"""
        INSERT INTO KNOWN_BUGS_JOIN (pack_id, bug_id) VALUES (1, 1)
    """)


def _get_pack_info_dir(dir, file_name):
    t = path.join("Packs/Info/", dir)
    Path(t).mkdir(parents=True, exist_ok=True)
    return path.join(t, file_name)


def gen_latest_pack(pack):
    with open(_get_pack_info_dir("PackUpdates", f'LatestPack_Sc_v{pack.sc_version}.json'), 'w+') as f:
        values = {
            "pack_version": pack.pack_version,
            "pack_v_code": pack.pack_v_code
        }
        f.write(json.dumps(values))


should_create = not path.isfile(db_name)

with sl.connect(db_name) as con:
    if should_create:
        create_db()
        add_sample_data()

    latest_packs = dict(con.execute("SELECT sc_version, MAX(pack_v_code) FROM PACKS GROUP BY sc_version").fetchall())

    for pack in map(PackRecord._make, con.execute("""
        SELECT id, name, sc_version, pack_version, pack_v_code, changelog 
        FROM PACKS
    """)):
        pack: PackRecord

        if pack.pack_v_code == latest_packs[pack.sc_version]:
            gen_latest_pack(pack)

        known_bugs = tuple(map(KnownBugRecord._make, con.execute(f"""
            SELECT bug_id, category, description 
            FROM KNOWN_BUGS_JOIN 
            LEFT JOIN KNOWN_BUGS ON KNOWN_BUGS.id=bug_id 
            WHERE pack_id={pack.id}
            """).fetchall()))
