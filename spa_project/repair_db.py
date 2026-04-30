import sqlite3

try:
    # Thử dump database ra file mới
    conn = sqlite3.connect('db.sqlite3')
    dump_conn = sqlite3.connect('db_repaired.sqlite3')

    # Dump data
    for line in conn.iterdump():
        dump_conn.execute(line)

    dump_conn.commit()
    dump_conn.close()
    conn.close()

    print("✅ Database repaired successfully!")
    print("File mới: db_repaired.sqlite3")
    print("Hãy thay db.sqlite3 bằng db_repaired.sqlite3")

except Exception as e:
    print(f"❌ Error: {e}")
    print("Database bị hỏng nặng, cần restore từ backup")
