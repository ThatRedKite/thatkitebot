import sqlite3

conn = sqlite3.connect("test.db")
c = conn.cursor()
c.execute("""select * from fuck order by name;""")
conn.commit()
conn.close()