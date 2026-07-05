from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)

CORS(app)

# DATABASE CONNECTION

db = pymysql.connect(
    host="localhost",
    user="root",
    password="root123",
    database="fuel_distribution"
)

cursor = db.cursor()

db.commit()


def table_has_column(table_name, column_name):

    sql = """
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = %s
    AND COLUMN_NAME = %s
    """

    cursor.execute(sql, (table_name, column_name))
    return cursor.fetchone()[0] > 0


def first_existing_column(table_name, column_names):

    for column_name in column_names:
        if table_has_column(table_name, column_name):
            return column_name

    return None


def sync_distributor_revenue(distributor_id):

    if not table_has_column("distributors", "revenue"):
        return

    total_sql = """
    SELECT COALESCE(SUM(price), 0)
    FROM bookings
    WHERE distributor_id=%s
    AND LOWER(status)='accepted'
    """

    cursor.execute(total_sql, (distributor_id,))
    total_revenue = cursor.fetchone()[0] or 0

    update_sql = """
    UPDATE distributors
    SET revenue=%s
    WHERE id=%s
    """

    cursor.execute(update_sql, (total_revenue, distributor_id))

# REGISTER API

@app.route('/register', methods=['POST'])

def register():

    data = request.get_json()

    name = data['name']
    email = data['email']
    phone = data['phone']
    address = data['address']
    password = data['password']

    sql = """
    INSERT INTO customers(name,email,phone,address,password)
    VALUES(%s,%s,%s,%s,%s)
    """

    values = (name,email,phone,address,password)

    cursor.execute(sql, values)

    db.commit()

    return jsonify({
        "message":"Customer Registered Successfully"
    })


@app.route('/login', methods=['POST'])
def login():

    data = request.get_json()

    login_type = data['login_type']
    email = data['email']
    password = data['password']

    # =====================
    # ADMIN LOGIN
    # =====================
    if login_type == "admin":

        if email == "admin@gmail.com" and password == "admin123":
            return jsonify({
                "status": "success",
                "message": "Admin Login Successful"
            })

        else:
            return jsonify({
                "status": "failed",
                "message": "Invalid Admin Credentials"
            })


    # =====================
    # CUSTOMER LOGIN
    # =====================
    elif login_type == "customer":

        sql = """
        SELECT id, name FROM customers
        WHERE email=%s AND password=%s
        """

        cursor.execute(sql, (email, password))
        customer = cursor.fetchone()

        if customer:
            return jsonify({
                "status": "success",
                "message": "Customer Login Successful",
                "customer_id": customer[0],
                "name": customer[1]
            })

        else:
            return jsonify({
                "status": "failed",
                "message": "Invalid Customer Credentials"
            })


    # =====================
    # DISTRIBUTOR LOGIN
    # =====================
    elif login_type == "distributor":

        sql = """
        SELECT id, name FROM distributors
        WHERE email=%s AND password=%s
        """

        cursor.execute(sql, (email, password))
        distributor = cursor.fetchone()

        if distributor:
            return jsonify({
                "status": "success",
                "message": "Distributor Login Successful",
                "distributor_id": distributor[0],
                "name": distributor[1]
            })

        else:
            return jsonify({
                "status": "failed",
                "message": "Invalid Distributor Credentials"
            })


    # =====================
    # INVALID TYPE
    # =====================
    else:
        return jsonify({
            "status": "failed",
            "message": "Invalid Login Type"
        })
    
# ADD DISTRIBUTOR API

@app.route('/add_distributor', methods=['POST'])

def add_distributor():

    data = request.get_json()

    name = data['name']
    email = data['email']
    phone = data['phone']
    city = data['city']
    pincode = data['pincode']
    address = data['address']
    password = data['password']

    sql = """

    INSERT INTO distributors
    (name,email,phone,city,pincode,address,password)

    VALUES(%s,%s,%s,%s,%s,%s,%s)

    """

    values = (
        name,
        email,
        phone,
        city,
        pincode,
        address,
        password
    )

    cursor.execute(sql, values)

    db.commit()

    return jsonify({

        "message":"Distributor Added Successfully"

    })

# VIEW DISTRIBUTORS API

@app.route('/view_distributors', methods=['GET'])

def view_distributors():

    sql = """

    SELECT id,name,email,phone,city,pincode,address
    FROM distributors

    """

    cursor.execute(sql)

    distributors = cursor.fetchall()

    distributor_list = []

    for distributor in distributors:

        distributor_list.append({

            "id": distributor[0],
            "name": distributor[1],
            "email": distributor[2],
            "phone": distributor[3],
            "city": distributor[4],
            "pincode": distributor[5],
            "address": distributor[6]

        })

    return jsonify(distributor_list)


# DELETE DISTRIBUTOR API

@app.route('/delete_distributor/<int:id>', methods=['DELETE'])

def delete_distributor(id):

    sql = "DELETE FROM distributors WHERE id=%s"

    cursor.execute(sql, (id))

    db.commit()

    return jsonify({

        "message":"Distributor Deleted Successfully"

    })

# ADD FUEL PRICE API

@app.route('/add_fuel_price', methods=['POST'])

def add_fuel_price():

    data = request.get_json()

    fuel_type = data['fuel_type']
    price = data['price']

    # CHECK IF FUEL ALREADY EXISTS

    check_sql = """

    SELECT * FROM fuel_prices

    WHERE fuel_type=%s

    """

    cursor.execute(check_sql, (fuel_type))

    fuel = cursor.fetchone()

    # IF EXISTS

    if fuel:

        return jsonify({

            "status":"failed",
            "message":"Fuel Already Exists"

        })

    # INSERT NEW FUEL

    sql = """

    INSERT INTO fuel_prices(fuel_type,price)

    VALUES(%s,%s)

    """

    cursor.execute(sql, (fuel_type, price))

    db.commit()

    return jsonify({

        "status":"success",
        "message":"Fuel Price Added Successfully"

    })


# VIEW FUEL PRICE API

@app.route('/view_fuel_prices', methods=['GET'])

def view_fuel_prices():

    cursor.execute("SELECT * FROM fuel_prices")

    fuels = cursor.fetchall()

    fuel_list = []

    for fuel in fuels:

        fuel_list.append({

            "id": fuel[0],
            "fuel_type": fuel[1],
            "price": fuel[2]

        })

    return jsonify(fuel_list)


# UPDATE FUEL PRICE API

@app.route('/update_fuel_price/<int:id>', methods=['PUT'])

def update_fuel_price(id):

    data = request.get_json()

    fuel_type = data['fuel_type']
    price = data['price']

    sql = """

    UPDATE fuel_prices

    SET fuel_type=%s, price=%s

    WHERE id=%s

    """

    cursor.execute(sql, (fuel_type, price, id))

    db.commit()

    return jsonify({

        "message":"Fuel Price Updated Successfully"

    })


# GET SINGLE FUEL PRICE

@app.route('/get_fuel_price/<int:id>', methods=['GET'])

def get_fuel_price(id):

    sql = "SELECT * FROM fuel_prices WHERE id=%s"

    cursor.execute(sql, (id))

    fuel = cursor.fetchone()

    return jsonify({

        "id": fuel[0],
        "fuel_type": fuel[1],
        "price": fuel[2]

    })

# BOOKING API

@app.route('/create_booking', methods=['POST'])
def create_booking():

    data = request.get_json()

    columns = [
        "customer_id",
        "distributor_id",
        "fuel_type",
        "liters",
        "price",
        "pincode",
        "address",
        "payment_mode",
        "status"
    ]

    values = [
        data['customer_id'],
        data['distributor_id'],
        data['fuel_type'],
        data['liters'],
        data['price'],
        data['pincode'],
        data['address'],
        data['payment_mode'],
        "pending"
    ]

    if data.get("date") and table_has_column("bookings", "date"):
        columns.append("date")
        values.append(data["date"])

    placeholders = ",".join(["%s"] * len(columns))
    column_list = ",".join(columns)

    sql = f"""
    INSERT INTO bookings
    ({column_list})
    VALUES ({placeholders})
    """

    cursor.execute(sql, values)
    db.commit()

    return jsonify({"status":"success","message":"Booking created"})

# BOOKINGS API

@app.route('/view_bookings/<int:customer_id>')
def view_bookings(customer_id):

    sql = """
    SELECT 
        b.id,
        b.fuel_type,
        b.liters,
        b.price,
        b.pincode,
        b.address,
        b.payment_mode,
        b.status,
        d.name,
        d.email,
        d.phone,
        d.address
    FROM bookings b
    JOIN distributors d ON b.distributor_id = d.id
    WHERE b.customer_id=%s
    """

    cursor.execute(sql, (customer_id,))
    data = cursor.fetchall()

    result = []

    for i in data:
        result.append({
            "id": i[0],
            "fuel_type": i[1],
            "liters": i[2],
            "price": i[3],
            "pincode": i[4],
            "address": i[5],
            "payment_mode": i[6],
            "status": i[7],
            "d_name": i[8],
            "d_email": i[9],
            "d_phone": i[10],
            "d_address": i[11]
        })

    return jsonify(result)

# ADD BOOKING API
@app.route('/add_booking', methods=['POST'])
def add_booking():

    data = request.get_json()

    sql = """
    INSERT INTO bookings
    (date,fuel_type,liters,price,total,pincode,address,payment)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        data['date'],
        data['fuel'],
        data['liters'],
        data['price'],
        data['total'],
        data['pincode'],
        data['address'],
        data['payment']
    )

    cursor.execute(sql, values)
    db.commit()

    return jsonify({"message":"Booking successful"})

# VIEW BOOKING API

@app.route('/view_distributor_bookings/<int:distributor_id>')
def view_distributor_bookings(distributor_id):

    sql = """
    SELECT 
        b.id,
        b.fuel_type,
        b.liters,
        b.price,
        b.pincode,
        b.address,
        b.payment_mode,
        b.status,

        c.name,
        c.email,
        c.phone

    FROM bookings b
    JOIN customers c ON b.customer_id = c.id
    WHERE b.distributor_id=%s
    """

    cursor.execute(sql, (distributor_id,))
    data = cursor.fetchall()

    result = []

    for i in data:
        result.append({
            "id": i[0],
            "fuel_type": i[1],
            "liters": i[2],
            "price": i[3],
            "pincode": i[4],
            "address": i[5],
            "payment_mode": i[6],
            "status": i[7],

            "c_name": i[8],
            "c_email": i[9],
            "c_phone": i[10]
        })

    return jsonify(result)

# UPDATE BOOKING STATUS

@app.route('/update_booking_status/<int:id>', methods=['PUT'])
def update_booking_status(id):

    data = request.get_json()

    status = data['status']

    booking_sql = """
    SELECT distributor_id, status
    FROM bookings
    WHERE id=%s
    """

    cursor.execute(booking_sql, (id,))
    booking = cursor.fetchone()

    if not booking:
        return jsonify({
            "message": "Booking not found"
        }), 404

    # UPDATE BOOKING STATUS

    update_sql = """
    UPDATE bookings
    SET status=%s
    WHERE id=%s
    """

    cursor.execute(update_sql, (status, id))

    sync_distributor_revenue(booking[0])

    db.commit()

    return jsonify({
        "message": f"Booking {status} successfully"
    })

# VIEW revenue API

@app.route('/view_revenue/<int:distributor_id>')
def view_revenue(distributor_id):

    date_column = first_existing_column("bookings", ["created_at", "date"])
    date_expression = f"DATE({date_column})" if date_column else "CURDATE()"

    sql = f"""

    SELECT
        {date_expression} as booking_date,
        fuel_type,
        COALESCE(SUM(liters), 0) as total_quantity,
        COALESCE(SUM(price), 0) as total_price

    FROM bookings

    WHERE distributor_id=%s
    AND LOWER(status)='accepted'

    GROUP BY {date_expression}, fuel_type

    ORDER BY booking_date DESC

    """

    cursor.execute(sql, (distributor_id,))

    data = cursor.fetchall()

    result = []

    for i in data:

        result.append({

            "date": str(i[0]),
            "fuel_type": i[1],
            "total_quantity": float(i[2]),
            "total_price": float(i[3])

        })

    return jsonify(result)

# ADD FEEDBACK API

@app.route('/add_feedback', methods=['POST'])
def add_feedback():

    data = request.get_json()

    customer_id = data['customer_id']
    rating = data['rating']
    comment = data['comment']

    sql = """
    INSERT INTO feedback(customer_id, rating, comment)
    VALUES(%s,%s,%s)
    """

    cursor.execute(sql, (customer_id, rating, comment))

    db.commit()

    return jsonify({

        "message":"Feedback Submitted Successfully"

    })


# VIEW FEEDBACK API

@app.route('/view_feedback', methods=['GET'])
def view_feedback():

    sql = """

    SELECT
    c.name,
    c.email,
    f.rating,
    f.comment

    FROM feedback f

    JOIN customers c
    ON f.customer_id = c.id

    ORDER BY f.id DESC

    """

    cursor.execute(sql)

    data = cursor.fetchall()

    feedback_list = []

    for i in data:

        feedback_list.append({

            "name": i[0],
            "email": i[1],
            "rating": i[2],
            "comment": i[3]

        })

    return jsonify(feedback_list)

# VIEW CUSTOMERS
@app.route("/view_customers")
def view_customers():

    sql = """
    SELECT id, name, email, phone, address
    FROM customers
    """

    cursor.execute(sql)

    data = cursor.fetchall()

    result = []

    for i in data:
        result.append({
            "id": i[0],
            "name": i[1],
            "email": i[2],
            "phone": i[3],
            "address": i[4]
        })

    return jsonify(result)

if __name__ == '__main__':

    app.run(debug=True, port=7000)
