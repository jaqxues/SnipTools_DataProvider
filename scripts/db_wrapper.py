from collections import namedtuple
from sqlite3 import Cursor

PackRecord = namedtuple('PackRecord', 'id, name, sc_version, pack_version, pack_v_code, changelog')
KnownBugRecord = namedtuple('KnownBugRecord', 'id, category, description, filed_on')


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
                    'changelog'     TEXT NOT NULL,
                    PRIMARY KEY('id' AUTOINCREMENT)
                );
            ''')

        self.con.execute('''
                CREATE TABLE 'KNOWN_BUGS' (
                    'id'	INTEGER,
                    'category'	TEXT NOT NULL,
                    'description'	TEXT NOT NULL,
                    'filed_on' DATE NOT NULL DEFAULT CURRENT_TIMESTAMP,
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

    def insert_pack(self, name, sc_version, pack_version, pack_v_code, changelog):
        return self.con.execute(
            '''
                    INSERT INTO PACKS (name, sc_version, pack_version, pack_v_code, changelog) 
                    VALUES(?,?,?,?,?);
                    ''',
            (name, sc_version, pack_version, pack_v_code, changelog)
        ).lastrowid

    def insert_bug(self, category, description):
        return self.con.execute(
            'INSERT INTO KNOWN_BUGS (category, description) VALUES(?,?);',
            (category, description)
        ).lastrowid

    def link_bug(self, bug_id, pack_id):
        return self.con.execute(
            'INSERT INTO KNOWN_BUGS_JOIN (pack_id, bug_id) VALUES (?, ?)',
            (pack_id, bug_id)
        ).lastrowid

    def add_sample_data(self):
        self.insert_pack('Pack_v1', '10.48.5.0', '1.2.0', 10, 'Updated for 10.48.5.0')
        self.insert_pack('Pack_v2', '10.48.5.0', '1.2.1', 11, 'Fixed Saving')
        self.insert_pack('Pack_v3', '10.49.5.0', '1.2.3', 12, 'Updated for 10.49')
        self.insert_bug('Saving', 'Currently does not work')
        self.link_bug(1, 1)

    def get_known_bugs(self, pack_id):
        return map(KnownBugRecord._make, self.con.execute(f'''
                                SELECT bug_id, category, description, filed_on
                                FROM KNOWN_BUGS_JOIN 
                                LEFT JOIN KNOWN_BUGS ON KNOWN_BUGS.id=bug_id 
                                WHERE pack_id=?
                                ''', (pack_id,)).fetchall())

    def get_sc_versions(self):
        return (x[0] for x in self.con.execute('SELECT DISTINCT sc_version FROM PACKS'))

    def get_packs_for_sc(self, sc_version):
        return map(PackRecord._make, self.con.execute(f'''
                    SELECT id, name, sc_version, pack_version, pack_v_code, changelog
                    FROM PACKS 
                    WHERE sc_version=?
                ''', (sc_version,)))

    def get_latest_packs(self):
        return map(PackRecord._make, self.con.execute('''
                SELECT
                id, name, sc_version, pack_version, pack_v_code, changelog
                FROM PACKS
                WHERE (sc_version, pack_v_code) IN (SELECT sc_version, MAX(pack_v_code) FROM PACKS GROUP BY sc_version)
            '''))
