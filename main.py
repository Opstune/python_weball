from flask import Flask, render_template, request, redirect, url_for, flash
from connection import connection_database, execute_data, execute_data_insert
import requests



app = Flask(__name__, template_folder="template", static_folder="static")
app.secret_key = 'd4b73684cc5886b0eedb08b4719fb5870a6f93634597cc12'


@app.route("/", methods=["GET", "POST"])
def home():
    result = connection_database()
    
    # ตั้งค่าข้อมูลให้เป็นลิสต์เปล่าก่อน ป้องกัน NoneType
    customer_text = execute_data("SELECT * FROM tbCustomer") or []
    customergroup_text = execute_data("SELECT * FROM tbCustomerGrp") or []
    stock_text = execute_data("SELECT * FROM tbStock") or []
    stockgroup_text = execute_data("SELECT * FROM tbStockGrp") or []
    order_data = execute_data("SELECT * FROM tb_Order") or []

    # Default values
    select_customer_name = ""
    select_tel = ""
    select_customergroup = ""
    select_stock = ""
    select_customer = ""
    order_id = ""
    updated_customer_name = ""
    updated_tel = ""
    updated_customergroup = ""
    updated_stock = ""
    stock_data = ""
    old_customer_data = ""
    new_customer_data = ""

    if request.method == "POST":
        # กรณีกดปุ่มค้นหา
        if "button_search" in request.form:
            select_customer = request.form.get("customer")
            select_customergroup = request.form.get('customergroup')
            select_customer_name = request.form.get('customer')
            select_stock = request.form.get('stock')

            if select_customer:
                for row in customer_text:
                    if row[0] == select_customer:
                        select_tel = row[5]
                        select_customergroup = row[1]
                        select_customer_name = row[2]  # ชื่อลูกค้า
                        break
                    
    if request.method == "POST":
        # กรณีกดปุ่มเพิ่มข้อมูล
        if "button_add" in request.form:
            select_customergroup = request.form.get('customergroup')
            select_customer_name = request.form.get('customer')  # ใช้เป็น CustCode
            select_stock = request.form.get('stock')

            # ตรวจสอบว่ามีข้อมูลซ้ำหรือไม่
            existing_order_check = execute_data(f"""
                SELECT * FROM tb_Order WHERE OrID = '{select_customer_name}' 
                AND OrStockID = '{select_stock}' AND OrGroupID = '{select_customergroup}'
            """) or []

            if not existing_order_check:  # ถ้ายังไม่มีข้อมูลซ้ำ
                if not all([select_customer_name, select_stock, select_customergroup]):
                    flash("กรุณากรอกข้อมูลให้ครบถ้วน")
                    return redirect(url_for("home"))

                # ✅ ดึงข้อมูลลูกค้าจาก tbCustomer
                customer_result = execute_data(f"SELECT * FROM tbCustomer WHERE CustCode = '{select_customer_name}'")
                if customer_result:
                    customer_prefix = customer_result[0][2]  # คำนำหน้าชื่อ
                    customer_name = customer_result[0][3]   # ชื่อ-นามสกุล
                    customer_tel = customer_result[0][5]    # เบอร์โทร
                    customer_group_code = customer_result[0][1]  # รหัสประเภทลูกค้า
                else:
                    customer_prefix = "ไม่พบ"
                    customer_name = "ข้อมูลลูกค้า"
                    customer_tel = "ไม่พบเบอร์โทร"
                    customer_group_code = "ไม่พบรหัสประเภทลูกค้า"

                # ✅ ดึงประเภทลูกค้าจาก tbCustomerGrp
                customer_group_result = execute_data(f"SELECT * FROM tbCustomerGrp WHERE CustGrpCode = '{customer_group_code}'")
                if customer_group_result:
                    customer_group = customer_group_result[0][1]  # ประเภทลูกค้า
                else:
                    customer_group = "ไม่พบประเภทลูกค้า"

                # ✅ ดึงชื่อสินค้า
                stock_result = execute_data(f"SELECT * FROM tbStock WHERE StockCode = '{select_stock}'")
                if stock_result:
                    product_name = stock_result[0][4]  # ✅ ดึงค่าจากคอลัมน์ StockName (row 4)
                else:
                    product_name = "ไม่มีสินค้า"

                # ✅ เพิ่มข้อมูลลงใน tb_Order
                query = f"""
                    INSERT INTO tb_Order (OrID, OrStockID, OrGroupID)
                    VALUES ('{select_customer_name}', '{select_stock}', '{select_customergroup}')
                """
                execute_data_insert(query)

                # ✅ ส่งข้อความไป LINE Notify
                url = "https://notify-api.line.me/api/notify"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    "Authorization": "Bearer 7lVpHVzPrquKZ3M4aucCt7SBuXj5tMfw8oWuQSqQTWx"
                }

                message_text = (
                    " ร้าน เครื่องเขียนนายวิน"
                    f"📢 ข้อมูลการสั่งสินค้าใหม่\n"
                    f"👤 ลูกค้า: {customer_prefix} {customer_name}\n"
                    f"📞 เบอร์โทร: {customer_tel}\n"
                    f"🏷️ ประเภทลูกค้า: {customer_group}\n"
                    f"📦 สินค้า: {product_name}"
                )

                message = {"message": message_text}

                res = requests.post(url=url, headers=headers, data=message)

                print("res", res.status_code)
                print("message", message_text)

                flash("ข้อมูลการสั่งซื้อถูกเพิ่มเรียบร้อยแล้ว")
            else:   
                flash("ข้อมูลการสั่งซื้อนี้มีอยู่แล้วในระบบ")

            return redirect(url_for("home"))


        # กรณีกดเลือกข้อมูลเพื่อแก้ไข
        if request.method == "POST":
            # กรณีกดปุ่มเลือกแก้ไข
            if "select_edit" in request.form:
                order_id = request.form.get("select_edit")
                
                # ดึงข้อมูลของ order ที่เลือกจากฐานข้อมูล
                query = f"SELECT OrID, OrStockID, OrGroupID FROM tb_Order WHERE OrID = '{order_id}'"
                selected_order = execute_data(query) or []

                query_stock = "SELECT StockCode, StockName FROM tbStock"
                stock_data = execute_data(query_stock) or []

                if selected_order:
                    select_customer = selected_order[0][0]  # รหัสลูกค้า
                    select_stock = selected_order[0][1]     # รหัสสินค้า
                    select_customergroup = selected_order[0][2]  # ประเภทลูกค้า

                    # ดึงข้อมูลเบอร์โทรของลูกค้า จาก tb_Customer
                    query_customer = f"SELECT CustTel FROM tbCustomer WHERE CustCode = '{select_customer}'"
                    customer_data = execute_data(query_customer) or []

                    if customer_data:
                        select_tel = customer_data[0][0]  # กำหนดเบอร์โทรให้ select_tel


        if request.method == "POST":
            # กรณีกดปุ่มอัพเดต
            if "button_update" in request.form:
                select_customer = request.form.get('customer')  # รหัสลูกค้าเดิม
                select_tel = request.form.get('tel')  # เบอร์โทรใหม่
                select_customergroup = request.form.get('customergroup')  # ประเภทลูกค้าใหม่
                select_stock = request.form.get('stock')  # สินค้าใหม่
                select_new_customer_code = request.form.get('new_customer_name')  # รหัสลูกค้าใหม่

                # ✅ เช็คให้แน่ใจว่ามีข้อมูลครบ
                if not all([select_customer, select_tel, select_customergroup, select_stock, select_new_customer_code]):
                    flash("กรุณากรอกข้อมูลให้ครบถ้วน")
                    return redirect(url_for("home"))

                # ✅ ดึงข้อมูลลูกค้าเดิม
                old_customer_data = execute_data(f"SELECT CustPreFix, CustName, CustTel, CustGrpCode FROM tbCustomer WHERE CustCode = '{select_customer}'")
                if old_customer_data:
                    old_prefix, old_fullname, old_tel, old_group_code = old_customer_data[0]  # รวมชื่อและนามสกุลไว้ที่ old_fullname
                else:
                    flash("ไม่พบข้อมูลลูกค้าเดิม")
                    return redirect(url_for("home"))

                # ✅ ดึงชื่อประเภทลูกค้าเก่า จากรหัส old_group_code
                old_customer_group_result = execute_data(f"SELECT CustGrpName FROM tbCustomerGrp WHERE CustGrpCode = '{old_group_code}'")
                if old_customer_group_result:
                    old_customer_group_name = old_customer_group_result[0][0]  # เอาชื่อประเภทลูกค้าเก่า
                else:
                    old_customer_group_name = "ไม่พบข้อมูล"

                new_customer_data = execute_data(f"SELECT CustPreFix, CustName, CustTel FROM tbCustomer WHERE CustCode = '{select_new_customer_code}'")
                if new_customer_data:
                    new_prefix, new_fullname, new_tel = new_customer_data[0]  # นำเบอร์โทรจากลูกค้าคนใหม่มาเก็บใน new_tel
                else:
                    flash("ไม่พบข้อมูลลูกค้าใหม่")
                    return redirect(url_for("home"))

                # ✅ ดึงชื่อสินค้าเก่า
                old_stock_result = execute_data(f"SELECT StockName FROM tbStock WHERE StockCode = (SELECT OrStockID FROM tb_Order WHERE OrID = '{select_customer}')")
                if old_stock_result:
                    old_product_name = old_stock_result[0][0]  # ชื่อสินค้าเก่า
                else:
                    old_product_name = "ไม่พบข้อมูลสินค้า"

                # ✅ ดึงชื่อสินค้าใหม่
                stock_result = execute_data(f"SELECT StockName FROM tbStock WHERE StockCode = '{select_stock}'")
                if stock_result:
                    product_name = stock_result[0][0]  # ชื่อสินค้าใหม่
                else:
                    product_name = "ไม่พบข้อมูลสินค้า"

                # ✅ ดึงชื่อประเภทลูกค้าใหม่ จากรหัส select_customergroup
                customer_group_result = execute_data(f"SELECT CustGrpName FROM tbCustomerGrp WHERE CustGrpCode = '{select_customergroup}'")
                if customer_group_result:
                    customer_group_name = customer_group_result[0][0]  # เอาชื่อประเภทลูกค้าใหม่
                else:
                    customer_group_name = "ไม่พบข้อมูล"

                # ✅ ส่งข้อความ LINE Notify ก่อนอัพเดต
                url = "https://notify-api.line.me/api/notify"
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    "Authorization": "Bearer 7lVpHVzPrquKZ3M4aucCt7SBuXj5tMfw8oWuQSqQTWx"
                }

                message_text = (
                    " ร้าน เครื่องเขียนนายวิน"
                    f"🔄 การอัพเดตข้อมูลลูกค้า\n"
                    f"👤 ข้อมูลลูกค้าเก่า: {old_prefix} {old_fullname} (📞 เบอร์: {old_tel} 🏷️ ประเภท: {old_customer_group_name} 📦 สินค้า: {old_product_name})\n\n"
                    f"➡️ เกิดการแก้ไขข้อมูลลูกค้า\n\n"
                    f"👤 ข้อมูลลูกค้าใหม่: {new_prefix} {new_fullname} (📞 เบอร์: {new_tel}) 🏷️ ประเภท: {customer_group_name} 📦 สินค้า: {product_name})\n"
                )

                message = {"message": message_text}

                # ส่งข้อความแจ้งเตือนก่อนการอัพเดต
                res = requests.post(url=url, headers=headers, data=message)
                print("res", res.status_code)
                print("message", message_text)

                # ✅ อัพเดตข้อมูลสินค้าใน tb_Order
                update_order_query = f"""
                    UPDATE tb_Order
                    SET OrStockID = '{select_stock}', OrGroupID = '{select_customergroup}'
                    WHERE OrID = '{select_customer}'
                """
                execute_data_insert(update_order_query)

                flash("ข้อมูลได้รับการอัพเดตเรียบร้อยแล้ว")
                return redirect(url_for("home"))

        if request.method == "POST":
            if "cancel_order" in request.form:  # กรณียกเลิกคำสั่งซื้อ
                order_id_to_cancel = request.form["cancel_order"]
                print("cancel_order", order_id_to_cancel)  # ตรวจสอบค่า order_id

                # ✅ ตรวจสอบว่ามีคำสั่งซื้อนี้อยู่หรือไม่
                order_check_query = f"SELECT OrID, OrStockID, OrGroupID, OrderStatus FROM tb_Order WHERE OrID = '{order_id_to_cancel}'"
                order_check = execute_data(order_check_query)

                if not order_check:
                    flash("ไม่พบคำสั่งซื้อที่ต้องการยกเลิก")
                    return redirect(url_for("home"))
                
                # ✅ ดึงข้อมูลจากคำสั่งซื้อ
                order_status = order_check[0][3]  # สถานะคำสั่งซื้อ
                customer_id = order_check[0][0]  # รหัสลูกค้า
                stock_id = order_check[0][1]  # รหัสสินค้า
                print("customer_id",customer_id)

                if order_status != 'ยกเลิก':  # ตรวจสอบว่ายังไม่ถูกยกเลิก
                    # ✅ อัปเดตสถานะคำสั่งซื้อเป็น "ยกเลิก"
                    cancel_order_query = f"UPDATE tb_Order SET OrderStatus = 'ยกเลิก' WHERE OrID = '{order_id_to_cancel}'"
                    execute_data_insert(cancel_order_query)
                    flash("คำสั่งซื้อถูกยกเลิกเรียบร้อยแล้ว")
                    print(f"Updating Order ID {order_id_to_cancel} to 'ยกเลิก'")  

                    # ✅ ดึงข้อมูลลูกค้า
                    customer_query = f"SELECT CustPreFix, CustName, CustTel, CustGrpCode FROM tbCustomer WHERE CustCode = '{customer_id}'"
                    customer_result = execute_data(customer_query)
                    print("customer_result",customer_result)

                    if customer_result:
                        customer_prefix = customer_result[0][0]  # คำนำหน้าชื่อ
                        customer_name = customer_result[0][1]  # ชื่อ-นามสกุล
                        customer_tel = customer_result[0][2]  # เบอร์โทร
                        customer_group_code = customer_result[0][3]  # รหัสประเภทลูกค้า
                    else:
                        customer_prefix = "ไม่พบ"
                        customer_name = "ไม่พบข้อมูลลูกค้า"
                        customer_tel = "ไม่พบเบอร์โทร"
                        customer_group_code = None
                        print("customer_prefix",customer_prefix)
                        print("customer_name",customer_name)
                        print("customer_tel",customer_tel)
                        print("customer_group_code",customer_group_code)


                    # ดึงประเภทลูกค้า
                    if customer_group_code:
                        customer_group_query = f"SELECT CustGrpName FROM tbCustomerGrp WHERE CustGrpCode = '{customer_group_code}'"
                        customer_group_result = execute_data(customer_group_query)

                        print("Customer Group Query:", customer_group_query)  # 🔎 Debug Query
                        print("Customer Group Result:", customer_group_result)  # 🔎 Debug Result

                        customer_group = customer_group_result[0][0] if customer_group_result else "ไม่พบประเภทลูกค้า"
                    else:
                        customer_group = "ไม่พบประเภทลูกค้า"
                        print("customer_group",customer_group)


                    # ดึงชื่อสินค้า
                    stock_query = f"SELECT StockName FROM tbStock WHERE StockCode = '{stock_id}'"
                    stock_result = execute_data(stock_query)

                    print("Stock Query:", stock_query)  # 🔎 Debug Query
                    print("Stock Result:", stock_result)  # 🔎 Debug Result

                    product_name = stock_result[0][0] if stock_result else "ไม่มีสินค้า"

                    print("product_name",product_name)
                    print("stock_result",stock_result)
                    

                    # ✅ แจ้งเตือนผ่าน LINE Notify
                    url = "https://notify-api.line.me/api/notify"
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Authorization': 'Bearer 7lVpHVzPrquKZ3M4aucCt7SBuXj5tMfw8oWuQSqQTWx'  # เปลี่ยนเป็น Access Token ของคุณ
                    }

                    # ✅ สร้างข้อความที่ส่งไป LINE Notify
                    message_text = (
                        "ร้าน เครื่องเขียนนายวิน\n"
                        f"📢 คำสั่งซื้อถูกยกเลิก\n"
                        f"👤 ลูกค้า: {customer_prefix} {customer_name}\n"
                        f"📞 เบอร์โทร: {customer_tel}\n"
                        f"🏷️ ประเภทลูกค้า: {customer_group}\n"
                        f"📦 สินค้า: {product_name}\n"
                        f"💬 สถานะคำสั่งซื้อ: ยกเลิก"
                    )

                    message = {"message": message_text}

                    # ✅ ส่งข้อความไป LINE Notify
                    res = requests.post(url, headers=headers, data=message)

                    print("res", res.status_code)  # ตรวจสอบสถานะการตอบกลับจาก LINE API
                    print("message", message_text)  # แสดงข้อความที่ส่งไป

                    flash("ข้อมูลการสั่งซื้อถูกยกเลิกและส่งข้อมูลผ่าน LINE Notify เรียบร้อยแล้ว")
                    return redirect(url_for("home"))
                else:
                    flash("คำสั่งซื้อนี้มีอยู่แล้วในระบบ")
                    return redirect(url_for("home"))



            # if request.method == 'POST':

            #     if 'restore_order' in request.form:  # เมื่อฟอร์มถูกส่ง
            #         order_id_to_restore = request.form['restore_order']
            #         print("restore_order", order_id_to_restore)  # ตรวจสอบค่า order_id

            #         # ตรวจสอบคำสั่งซื้อในฐานข้อมูล
            #         order_check_query = f"SELECT OrID, OrStockID, OrGroupID, OrderStatus FROM tb_Order WHERE OrID = '{order_id_to_restore}'"
            #         order_check = execute_data(order_check_query)

            #         if not order_check:
            #             flash("ไม่พบคำสั่งซื้อที่ต้องการคืนค่า")
            #             return redirect(url_for("home"))

            #         # ดึงข้อมูลสถานะคำสั่งซื้อ
            #         order_status = order_check[0][3]  # สถานะคำสั่งซื้อ

            #         if order_status == 'ยกเลิก':  # เฉพาะกรณีที่คำสั่งซื้อถูกยกเลิกแล้ว
            #             # อัปเดตสถานะคำสั่งซื้อให้กลับไปเป็น 'ปกติ'
            #             restore_order_query = f"UPDATE tb_Order SET OrderStatus = 'ปกติ' WHERE OrID = '{order_id_to_restore}'"
            #             execute_data_insert(restore_order_query)
            #             flash("คำสั่งซื้อถูกคืนค่าเรียบร้อยแล้ว")
            #             print(f"Restoring Order ID {order_id_to_restore} to 'ปกติ'")

            #         else:
            #             flash("คำสั่งซื้อนี้ไม่ได้ถูกยกเลิก จึงไม่สามารถคืนค่าได้")

            #     return redirect(url_for('home'))


    return render_template(
        "home/home.html", 
        customer_text=customer_text,  # ส่งข้อมูลลูกค้า
        customergroup_text=customergroup_text,  # ส่งข้อมูลประเภทลูกค้า
        stock_text=stock_text,  # ส่งข้อมูลสินค้า
        select_tel=select_tel,  # ส่งเบอร์โทรศัพท์ที่เลือก
        select_customergroup=select_customergroup,  # ส่งประเภทลูกค้าที่เลือก
        order_data=order_data,  # ส่งข้อมูลการสั่งซื้อ
        select_customer_name=select_customer_name,  # ส่งชื่อของลูกค้าที่เลือก
        select_customer=select_customer,  # ส่งรหัสลูกค้าที่เลือก       
        updated_customergroup=updated_customergroup,  # ส่งประเภทลูกค้าที่อัปเดต
    )



# เส้นทางสำหรับหน้าข้อมูลลูกค้า
@app.route('/customer')
def customer():
    result_customer = execute_data(query="SELECT * FROM tbCustomer")
    return render_template('Customer/customer.html', customer_text=result_customer)


# เส้นทางสำหรับข้อมูลการสั่งซื้อ
@app.route("/orders")
def orders():
    order_data = execute_data(query="SELECT * FROM tb_Order")
    return render_template('Orders/orders.html', order_data=order_data)


# เส้นทางสำหรับกลุ่มลูกค้า
@app.route('/customergroup')
def customergroup():
    result_customer = execute_data(query="SELECT * FROM tbCustomerGrp")
    return render_template('Customergroup/customergroup.html', customer_text=result_customer)


# เส้นทางสำหรับข้อมูลสินค้า (Stock)
@app.route('/stock')
def stock():
    result_customer = execute_data(query="SELECT * FROM tbStock")
    return render_template('stock/stock.html', customer_text=result_customer)


# เส้นทางสำหรับกลุ่มสินค้า
@app.route('/stockgroup')
def stockgroup():
    result_customer = execute_data(query="SELECT * FROM tbStockGrp")
    return render_template('stockgroup/stockgroup.html', customer_text=result_customer)


# เส้นทางสำหรับประเภทการขาย (Sale Type)
@app.route('/saletype')
def saletype():
    result_customer = execute_data(query="SELECT * FROM tbSaleType")
    return render_template('saletype/saletype.html', customer_text=result_customer)


# เส้นทางสำหรับข้อมูลสถานที่ (Location)
@app.route('/location')
def location():
    result_customer = execute_data(query="SELECT * FROM tbLocation")
    return render_template('location/location.html', customer_text=result_customer)


if __name__ == '__main__':
    app.run(debug=True)
