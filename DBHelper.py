import sqlite3
import logging

logger = logging.getLogger()
FORMAT = "[%(asctime)s][%(filename)s:%(lineno)3s - %(funcName)20s()] %(message)s"
logger.setLevel(logging.DEBUG)

DB_NAME = "write_board_macro.db"

CURRENT_VERSION = "0.1"

TABLE_BAND = "band"
BAND_ID = "_id"
BAND_NAME = "name"
BAND_URL = "url"
BAND_CHECKED = "checked"
BAND_COLUMNS = [BAND_ID, BAND_NAME, BAND_URL, BAND_CHECKED]

TABLE_PREFERENCE = "preference"
PREFERENCE_KEY = "preference_key"
PREFERENCE_STRING = "preference_string"
PREFERENCE_INTEGER = "preference_integer"
PREFERENCE_REAL = "preference_real"

"""
PREFERENCE KEY
"""
KEY_ID = "key_id"
KEY_PW = "key_pw"
KEY_IP = "key_ip"
KEY_ACCOUNT_VALIDATION = "key_account_validation"
KEY_CONTENT = "key_content"
KEY_RSRV_DATETIME = "key_rsrv_date"
KEY_RSRV_INTERVAL = "key_rsrv_interval"
KEY_DELAY = "key_delay"

def connect():
    global con
    global cursor
    con = sqlite3.connect(f"./{DB_NAME}") 
    cursor = con.cursor()
    
    SCHEMA_BAND = f"({BAND_ID} integer, {BAND_NAME} text, {BAND_URL} text, {BAND_CHECKED} integer default 0, primary key({BAND_ID}))"
    SCHEMA_PREFERENCE = f"({PREFERENCE_KEY} text primary key, {PREFERENCE_STRING} text, {PREFERENCE_INTEGER} integer, {PREFERENCE_REAL} real)"

    CREATE_BAND = f"CREATE TABLE IF NOT EXISTS \"{TABLE_BAND}\""+SCHEMA_BAND
    CREATE_PREFERENCE = f"CREATE TABLE IF NOT EXISTS \"{TABLE_PREFERENCE}\""+SCHEMA_PREFERENCE

    cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='schema_versions'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(f'CREATE TABLE schema_versions(version text)')
        cursor.execute(f'INSERT INTO schema_versions(version) VALUES({CURRENT_VERSION})')
        con.commit()

    cursor.execute(CREATE_BAND)
    cursor.execute(CREATE_PREFERENCE)

    # 버전별 변경 사항 적용해줌 컬럼 -> 속성(PK ...)
    if getDatabaseVersion() == "0.1":
        pass
    

def getDatabaseVersion():
    cursor.execute(f"select max(version) from schema_versions")
    return cursor.fetchone()[0]

def checkSchema(table_name, table_schema, table_columns):
    cursor.execute(f"select * from sqlite_master where type='table' and name='{table_name}';")
    result = cursor.fetchall()[0][4]
    if result[result.index('('):].lower() != table_schema.lower():
        print(table_name)
        cursor.execute("PRAGMA foreign_keys=0")
        cursor.execute("begin")
        try:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS new_{table_name}"+table_schema)
            cursor.execute(f"INSERT INTO new_{table_name}({','.join(table_columns)}) SELECT * FROM {table_name}")
            cursor.execute(f"DROP TABLE {table_name}")
            cursor.execute(f"ALTER TABLE new_{table_name} RENAME TO {table_name}")
            con.commit()
        except:
            logging.exception("")
            con.rollback()
        finally:
            cursor.execute("PRAGMA foreign_keys=1")

def close():
    cursor.close()
    con.close()

def putStringExtra(key, extra):
    cursor.execute(f"INSERT OR REPLACE INTO {TABLE_PREFERENCE}({PREFERENCE_KEY}, {PREFERENCE_STRING}) VALUES ('{key}', '{extra}')")
    con.commit()

def getStringExtra(key, empty):
    cursor.execute(f"SELECT {PREFERENCE_STRING} FROM {TABLE_PREFERENCE} WHERE {PREFERENCE_KEY} = '{key}'")
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return empty

def putIntegerExtra(key, extra):
    cursor.execute(f"INSERT OR REPLACE INTO {TABLE_PREFERENCE}({PREFERENCE_KEY}, {PREFERENCE_INTEGER}) VALUES ('{key}', '{extra}')")
    con.commit()

def getIntegerExtra(key, empty):
    cursor.execute(f"SELECT {PREFERENCE_INTEGER} FROM {TABLE_PREFERENCE} WHERE {PREFERENCE_KEY} = '{key}'")
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return empty

def addBand(band_id, name, url):
    cursor.execute(f"INSERT INTO {TABLE_BAND} ({BAND_ID}, {BAND_NAME}, {BAND_URL}) VALUES('{band_id}', ?, '{url}')", (name,))
    con.commit()

def updateBandChecked(band_id, checked):
    cursor.execute(f"UPDATE {TABLE_BAND} SET {BAND_CHECKED} = {checked} WHERE {BAND_ID} = {band_id};")
    con.commit()

def getBands():
    cursor.execute(f"SELECT * FROM {TABLE_BAND}")
    return cursor.fetchall()

def getBand(band_id):
    cursor.execute(f"SELECT * FROM {TABLE_BAND} WHERE {BAND_ID} = '{band_id}'")
    return cursor.fetchall()[0]

def clearBands():
    cursor.execute(f"DELETE FROM {TABLE_BAND}")
    con.commit()

def clearReferences():
    cursor.execute(f"DELETE FROM {TABLE_PREFERENCE}")
    con.commit()

