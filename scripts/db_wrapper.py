from collections import namedtuple
from sqlite3 import Cursor
from datetime import datetime

PackRecord = namedtuple('PackRecord',
                        'id, name, sc_version, pack_version, pack_v_code, min_apk_v_code, changelog, created_at')
KnownBugRecord = namedtuple('KnownBugRecord', 'id, category, description, filed_on, fixed_on')


class DbWrapper:
    def __init__(self, con):
        con: Cursor
        self.con = con

    def create_db(self):
        self.con.execute('''
                CREATE TABLE PACKS (
                    'id'	INTEGER,
                    'name'	TEXT NOT NULL UNIQUE,
                    'sc_version'	TEXT NOT NULL,
                    'pack_version'	TEXT NOT NULL,
                    'pack_v_code'	INTEGER NOT NULL,
                    'min_apk_v_code' INTEGER NOT NULL,
                    'changelog'     TEXT NOT NULL,
                    'created_at' DATE NOT NULL,
                    PRIMARY KEY('id' AUTOINCREMENT)
                );
            ''')

        self.con.execute('''
                CREATE TABLE 'KNOWN_BUGS' (
                    'id'	INTEGER,
                    'category'	TEXT NOT NULL,
                    'description'	TEXT NOT NULL,
                    'filed_on' DATE NOT NULL,
                    'fixed_on' DATE,
                    PRIMARY KEY('id' AUTOINCREMENT)
                );
            ''')

        self.con.execute('''
                CREATE TABLE 'KNOWN_BUGS_JOIN' (
                    'pack_id'	INTEGER,
                    'bug_id'	INTEGER,
                    FOREIGN KEY('bug_id') REFERENCES 'KNOWN_BUGS'('id') ON DELETE CASCADE,
                    FOREIGN KEY('pack_id') REFERENCES 'PACKS'('id') ON DELETE CASCADE
                );
        ''')

    def insert_pack(self, name, sc_version, pack_version, pack_v_code, min_apk_v_code, changelog):
        return self.con.execute(
            '''
                    INSERT INTO PACKS 
                    (name, sc_version, pack_version, pack_v_code, min_apk_v_code, changelog, created_at) 
                    VALUES(?,?,?,?,?,?, ?);
                    ''',
            (name, sc_version, pack_version, pack_v_code, min_apk_v_code, changelog, datetime.now())
        ).lastrowid

    def inherit_bugs_from(self, previous_pack_id, current_pack_id):
        self.con.execute(
            f'''
                    INSERT INTO KNOWN_BUGS_JOIN (pack_id, bug_id)
                    SELECT ?, bug_id FROM KNOWN_BUGS_JOIN WHERE pack_id=?;
            ''', (current_pack_id, previous_pack_id)
        )

    def insert_bug(self, category, description):
        return self.con.execute(
            'INSERT INTO KNOWN_BUGS (category, description, filed_on) VALUES(?,?,?);',
            (category, description, datetime.now())
        ).lastrowid

    def fix_bug_for(self, bug_id, pack_id):
        return self.con.execute(
            'DELETE FROM KNOWN_BUGS_JOIN WHERE pack_id=? AND bug_id=?;', (pack_id, bug_id)
        )

    def mark_bug_as_fixed(self, bug_id, delete_links=False):
        if delete_links:
            self.con.execute('DELETE FROM KNOWN_BUGS_JOIN WHERE bug_id=?', (bug_id,))
        self.con.execute('UPDATE KNOWN_BUGS SET fixed_on=? WHERE id=?', (datetime.now(), bug_id))

    def link_bug(self, bug_id, pack_id):
        return self.con.execute(
            'INSERT INTO KNOWN_BUGS_JOIN (pack_id, bug_id) VALUES (?, ?)',
            (pack_id, bug_id)
        ).lastrowid

    def get_known_bugs(self, pack_id):
        return map(KnownBugRecord._make, self.con.execute(f'''
                                SELECT bug_id, category, description, 
                                        filed_on AS "[timestamp]", fixed_on AS "[timestamp]"
                                FROM KNOWN_BUGS_JOIN 
                                LEFT JOIN KNOWN_BUGS ON KNOWN_BUGS.id=bug_id 
                                WHERE pack_id=?
                                ''', (pack_id,)).fetchall())

    def get_sc_versions(self):
        return (x[0] for x in self.con.execute('SELECT DISTINCT sc_version FROM PACKS'))

    def get_packs_for_sc(self, sc_version):
        return map(PackRecord._make, self.con.execute(f'''
                    SELECT id, name, sc_version, pack_version, pack_v_code, 
                            min_apk_v_code, changelog, created_at AS "[timestamp]"
                    FROM PACKS 
                    WHERE sc_version=?
                ''', (sc_version,)))

    def get_latest_packs(self):
        return map(PackRecord._make, self.con.execute('''
                SELECT id, name, sc_version, pack_version, pack_v_code, 
                        min_apk_v_code, changelog, created_at AS "[timestamp]"
                FROM PACKS
                WHERE (sc_version, pack_v_code) IN 
                    (SELECT sc_version, MAX(pack_v_code) FROM PACKS GROUP BY sc_version)
            '''))
