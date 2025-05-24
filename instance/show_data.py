from sqlalchemy import create_engine, MetaData, Table, select
import sqlalchemy

# 🔁 عدّل هذا حسب نوع قاعدة البيانات ومسارها
# SQLite مثال:
engine = create_engine('sqlite:///clinickk.db')  # ضع اسم ملف قاعدة البيانات

# PostgreSQL مثال:
# engine = create_engine('postgresql://username:password@localhost/dbname')

metadata = MetaData()
metadata.reflect(bind=engine)
print(metadata.tables.items())
# المرور على كل الجداول وطباعتها
for table_name, table in metadata.tables.items():
    print(f"محتويات جدول: {table_name}")
    with engine.connect() as conn:
        result = conn.execute(select(table))
        for row in result:
            print(dict(row))
    print('-' * 40)
