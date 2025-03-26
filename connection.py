import pyodbc

# เชื่อมต่อกับฐานข้อมูล SQL Server
connect = pyodbc.connect("Driver={SQL Server};Server=LAPTOP-HDF2DSJG;Database=iStockCoop")

# ฟังก์ชันเชื่อมต่อกับฐานข้อมูล
def connection_database():
    try:
        if connect:
            print("✅ Connection Successful")
            return True
        else:
            print("❌ Connection Failed")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

# ฟังก์ชันดึงข้อมูลจากฐานข้อมูล (ลบ params ออก)
def execute_data(query):
    try:
        cursor = connect.cursor()
        cursor.execute(query)  # ลบ params ออก
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print("❌ Error executing query:", e)
        return None
    finally:
        cursor.close()  # ปิด cursor

# ฟังก์ชันเพิ่มข้อมูลลงฐานข้อมูล
def execute_data_insert(query):
    try:
        cursor = connect.cursor()
        cursor.execute(query)  # สั่งให้ query ทำงาน
        connect.commit()  # คอมมิตข้อมูล
        return 1  # ส่งกลับผลลัพธ์สำเร็จ
    except Exception as e:
        connect.rollback()  # หากเกิดข้อผิดพลาด, ยกเลิกการเปลี่ยนแปลงทั้งหมด
        print("❌ Error executing insert query:", e)
        return 0  # ส่งกลับผลลัพธ์ที่ล้มเหลว
    finally:
        cursor.close()  # ปิด cursor

# ฟังก์ชันอัปเดตข้อมูลในฐานข้อมูล
def execute_data_update(query):
    try:
        cursor = connect.cursor()
        cursor.execute(query)  # สั่งให้ query ทำงาน
        connect.commit()  # คอมมิตการอัปเดต
        return 1  # ส่งกลับผลลัพธ์สำเร็จ
    except Exception as e:
        connect.rollback()  # หากเกิดข้อผิดพลาด, ยกเลิกการเปลี่ยนแปลงทั้งหมด
        print("❌ Error executing update query:", e)
        return 0  # ส่งกลับผลลัพธ์ที่ล้มเหลว
    finally:
        cursor.close()  # ปิด cursor

# ฟังก์ชันลบข้อมูลจากฐานข้อมูล
def execute_data_delete(query):
    try:
        cursor = connect.cursor()
        cursor.execute(query)  # สั่งให้ query ทำงาน
        connect.commit()  # คอมมิตการลบ
        return 1  # ส่งกลับผลลัพธ์สำเร็จ
    except Exception as e:
        connect.rollback()  # หากเกิดข้อผิดพลาด, ยกเลิกการเปลี่ยนแปลงทั้งหมด
        print("❌ Error executing delete query:", e)
        return 0  # ส่งกลับผลลัพธ์ที่ล้มเหลว
    finally:
        cursor.close()  # ปิด cursor

# ฟังก์ชันเพื่อดึงข้อมูล, หากไม่มีผลลัพธ์จะส่งกลับเป็นลิสต์ว่าง
def get_data(query):
    result = execute_data(query)
    return result if result else []

# ฟังก์ชันเช็คข้อมูลในฐานข้อมูล
def check_data_exists(query):
    result = execute_data(query)
    return True if result else False


