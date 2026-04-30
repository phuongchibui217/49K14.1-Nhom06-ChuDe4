import sqlite3

try:
    # Connect và checkpoint WAL
    conn = sqlite3.connect('db.sqlite3')
    conn.execute('PRAGMA wal_checkpoint(FULL)')
    conn.close()

    print("✅ WAL checkpoint completed!")

    # Thử integrity check
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('PRAGMA integrity_check')
    result = cursor.fetchone()
    conn.close()

    if result and result[0] == 'ok':
        print("✅ Database is OK!")
    else:
        print(f"❌ Integrity check: {result}")

except Exception as e:
    print(f"❌ Error: {e}")
