import sqlite3
import sys
import os

def migrate():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kalemera.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}, skipping migration.")
        return

    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Helper to check if column exists
    def column_exists(table, col):
        cur.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cur.fetchall()]
        return col in columns

    # 1. Alter Products Table
    altered_products = False
    if not column_exists("products", "name_en"):
        print("Adding column 'name_en' to 'products' table...")
        cur.execute("ALTER TABLE products ADD COLUMN name_en VARCHAR(255)")
        altered_products = True

    if not column_exists("products", "description_en"):
        print("Adding column 'description_en' to 'products' table...")
        cur.execute("ALTER TABLE products ADD COLUMN description_en VARCHAR(1000)")
        altered_products = True

    # 2. Alter Order Items Table
    altered_order_items = False
    if not column_exists("order_items", "product_name_en_snapshot"):
        print("Adding column 'product_name_en_snapshot' to 'order_items' table...")
        cur.execute("ALTER TABLE order_items ADD COLUMN product_name_en_snapshot VARCHAR(255)")
        altered_order_items = True

    conn.commit()

    # 3. Migrate Products Data
    print("Migrating products data...")
    cur.execute("SELECT id, name, description FROM products")
    products = cur.fetchall()

    for pid, name, desc in products:
        # Parse name: e.g., "Margherita Pizza - مارجريتا" or "Alexandrian Liver Sandwich - كبدة إسكندراني"
        name_ar, name_en = name, name
        if " - " in name:
            parts = name.split(" - ", 1)
            name_en = parts[0].strip()
            name_ar = parts[1].strip()

        # Parse description: e.g., "Arabic / English"
        desc_ar, desc_en = desc, desc
        if desc and " / " in desc:
            parts = desc.split(" / ", 1)
            desc_ar = parts[0].strip()
            desc_en = parts[1].strip()

        cur.execute(
            "UPDATE products SET name = ?, name_en = ?, description = ?, description_en = ? WHERE id = ?",
            (name_ar, name_en, desc_ar, desc_en, pid)
        )

    # 4. Migrate Order Items Data
    print("Migrating order items data...")
    cur.execute("SELECT id, product_name_snapshot FROM order_items")
    items = cur.fetchall()

    for iid, snapshot in items:
        snap_ar, snap_en = snapshot, snapshot
        if " - " in snapshot:
            parts = snapshot.split(" - ", 1)
            snap_en = parts[0].strip()
            snap_ar = parts[1].strip()

        cur.execute(
            "UPDATE order_items SET product_name_snapshot = ?, product_name_en_snapshot = ? WHERE id = ?",
            (snap_ar, snap_en, iid)
        )

    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
