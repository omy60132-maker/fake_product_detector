from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

import sqlite3
import uuid
import qrcode
import os

from database import (
    get_connection,
    create_database
)

from blockchain import Blockchain


# =====================================================
# APP CONFIGURATION
# =====================================================

app = Flask(__name__)

# IMPORTANT:
# Session ke liye fixed secret key
app.secret_key = "fake-product-detection-secret-key-2026"

# Session settings
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Development mein localhost HTTP use kar rahe hain,
# isliye Secure=True nahi karna hai.
app.config["SESSION_COOKIE_SECURE"] = False


# =====================================================
# DATABASE
# =====================================================

create_database()


# =====================================================
# BLOCKCHAIN
# =====================================================

blockchain = Blockchain()


# =====================================================
# QR CODE FOLDER
# =====================================================

QR_FOLDER = os.path.join(
    app.root_path,
    "static",
    "qr"
)

os.makedirs(
    QR_FOLDER,
    exist_ok=True
)


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =====================================================
# ADMIN LOGIN
# =====================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    # Agar already admin login hai
    if "admin" in session:

        return redirect(
            url_for("admin_dashboard")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            return render_template(
                "admin_login.html",
                error="Please enter email and password."
            )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            AND role = 'admin'
        """, (
            email,
            password
        ))

        admin = cursor.fetchone()

        connection.close()

        if admin:

            # FIX: Ab admin login karne par customer
            # session ko delete NAHI karte.
            # Pehle yahan session.pop("customer", None) tha,
            # jiski wajah se doosre tab mein customer session
            # tut jata tha aur baar-baar login page aata tha.

            # Admin session set karo
            session["admin"] = admin["email"]

            session.permanent = True

            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )

        return render_template(
            "admin_login.html",
            error="Invalid admin email or password"
        )

    return render_template(
        "admin_login.html"
    )


# =====================================================
# ADMIN DASHBOARD
# =====================================================

@app.route(
    "/admin/dashboard"
)
def admin_dashboard():

    if "admin" not in session:

        return redirect(
            url_for("admin_login")
        )

    connection = get_connection()
    cursor = connection.cursor()

    # ---------------------------------------------
    # PRODUCTS
    # ---------------------------------------------

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()

    # ---------------------------------------------
    # PRODUCT COUNT
    # ---------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM products
    """)

    product_count = cursor.fetchone()[0]

    # ---------------------------------------------
    # CUSTOMER COUNT
    # ---------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role = 'customer'
    """)

    customer_count = cursor.fetchone()[0]

    # ---------------------------------------------
    # VERIFICATION COUNT
    # ---------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM verification_history
    """)

    verification_count = cursor.fetchone()[0]

    # ---------------------------------------------
    # COMPLAINTS
    # ---------------------------------------------

    cursor.execute("""
        SELECT *
        FROM complaints
        ORDER BY id DESC
    """)

    complaints = cursor.fetchall()

    connection.close()

    return render_template(
        "admin_dashboard.html",

        products=products,

        product_count=product_count,

        customer_count=customer_count,

        verification_count=verification_count,

        complaints=complaints
    )


# =====================================================
# ADD PRODUCT
# =====================================================

@app.route(
    "/admin/add-product",
    methods=["GET", "POST"]
)
def add_product():

    if "admin" not in session:

        return redirect(
            url_for("admin_login")
        )

    if request.method == "POST":

        # ---------------------------------------------
        # PRODUCT ID
        # ---------------------------------------------

        product_id = (
            "PROD-" +
            uuid.uuid4().hex[:8].upper()
        )

        # ---------------------------------------------
        # FORM DATA
        # ---------------------------------------------

        product_name = request.form.get(
            "product_name",
            ""
        ).strip()

        manufacturer = request.form.get(
            "manufacturer",
            ""
        ).strip()

        batch_number = request.form.get(
            "batch_number",
            ""
        ).strip()

        manufacturing_date = request.form.get(
            "manufacturing_date",
            ""
        )

        expiry_date = request.form.get(
            "expiry_date",
            ""
        )

        price = request.form.get(
            "price",
            ""
        )

        # ---------------------------------------------
        # VALIDATION
        # ---------------------------------------------

        if not product_name:

            return render_template(
                "add_product.html",
                error="Product name is required."
            )

        if not manufacturer:

            return render_template(
                "add_product.html",
                error="Manufacturer is required."
            )

        if not batch_number:

            return render_template(
                "add_product.html",
                error="Batch number is required."
            )

        # =================================================
        # QR CODE
        # =================================================

        qr_filename = (
            product_id +
            ".png"
        )

        qr_path = os.path.join(
            QR_FOLDER,
            qr_filename
        )

        # QR ke andar Product ID store hoga
        qr = qrcode.make(
            product_id
        )

        qr.save(
            qr_path
        )

        # =================================================
        # BLOCKCHAIN
        # =================================================

        product_data = {

            "product_id":
                product_id,

            "product_name":
                product_name,

            "manufacturer":
                manufacturer,

            "batch_number":
                batch_number
        }

        block = blockchain.add_product(
            product_data
        )

        # =================================================
        # SAVE PRODUCT IN SQLITE
        # =================================================

        connection = get_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO products
                (
                    product_id,
                    product_name,
                    manufacturer,
                    batch_number,
                    manufacturing_date,
                    expiry_date,
                    price,
                    barcode,
                    blockchain_hash
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (

                product_id,

                product_name,

                manufacturer,

                batch_number,

                manufacturing_date,

                expiry_date,

                price,

                qr_filename,

                block["hash"]
            ))

            connection.commit()

        except Exception as e:

            connection.rollback()
            connection.close()

            # Agar database save fail ho gaya
            # to QR remove kar do
            if os.path.exists(qr_path):

                os.remove(qr_path)

            return render_template(
                "add_product.html",
                error="Product could not be registered."
            )

        connection.close()

        # =================================================
        # SUCCESS
        # =================================================

        return render_template(
            "add_product.html",

            success=True,

            product_id=product_id,

            qr_filename=qr_filename
        )

    return render_template(
        "add_product.html"
    )


# =====================================================
# CUSTOMER REGISTER
# =====================================================

@app.route(
    "/customer/register",
    methods=["GET", "POST"]
)
def customer_register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not name or not email or not password:

            return render_template(
                "customer_register.html",
                error="All fields are required."
            )

        connection = get_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    role
                )

                VALUES (?, ?, ?, 'customer')
            """, (
                name,
                email,
                password
            ))

            connection.commit()
            connection.close()

            return redirect(
                url_for(
                    "customer_login"
                )
            )

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "customer_register.html",
                error="Email already registered."
            )

        except Exception:

            connection.close()

            return render_template(
                "customer_register.html",
                error="Registration failed."
            )

    return render_template(
        "customer_register.html"
    )


# =====================================================
# CUSTOMER LOGIN
# =====================================================

@app.route(
    "/customer/login",
    methods=["GET", "POST"]
)
def customer_login():

    # Already logged in
    if "customer" in session:

        return redirect(
            url_for(
                "customer_dashboard"
            )
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            return render_template(
                "customer_login.html",
                error="Please enter email and password."
            )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            AND role = 'customer'
        """, (
            email,
            password
        ))

        customer = cursor.fetchone()

        connection.close()

        if customer:

            # FIX: Ab customer login karne par admin
            # session ko delete NAHI karte.
            # Pehle yahan session.pop("admin", None) tha,
            # jiski wajah se doosre tab mein admin session
            # tut jata tha aur baar-baar login page aata tha.

            # Customer session
            session["customer"] = \
                customer["email"]

            session.permanent = True

            return redirect(
                url_for(
                    "customer_dashboard"
                )
            )

        return render_template(
            "customer_login.html",
            error="Invalid email or password"
        )

    return render_template(
        "customer_login.html"
    )


# =====================================================
# CUSTOMER DASHBOARD
# =====================================================

@app.route(
    "/customer/dashboard"
)
def customer_dashboard():

    if "customer" not in session:

        return redirect(
            url_for(
                "customer_login"
            )
        )

    return render_template(
        "customer_dashboard.html",

        email=session["customer"]
    )


# =====================================================
# VERIFY PRODUCT
# =====================================================

@app.route(
    "/verify"
)
def verify():

    if "customer" not in session:

        return redirect(
            url_for(
                "customer_login"
            )
        )

    product_id = request.args.get(
        "product_id",
        ""
    ).strip()

    # Product ID nahi diya
    if not product_id:

        return render_template(
            "verify.html"
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        WHERE product_id = ?
    """, (
        product_id,
    ))

    product = cursor.fetchone()

    # =================================================
    # FAKE
    # =================================================

    if product is None:

        status = \
            "FAKE / NOT REGISTERED"

    # =================================================
    # BLOCKCHAIN VERIFICATION
    # =================================================

    elif blockchain.verify_product(

        product_id,

        product["blockchain_hash"]

    ):

        status = \
            "GENUINE PRODUCT"

    # =================================================
    # SUSPICIOUS
    # =================================================

    else:

        status = \
            "SUSPICIOUS PRODUCT"

    # =================================================
    # SAVE VERIFICATION HISTORY
    # =================================================

    cursor.execute("""
        INSERT INTO verification_history
        (
            product_id,
            customer_email,
            verification_status
        )

        VALUES (?, ?, ?)
    """, (

        product_id,

        session["customer"],

        status
    ))

    connection.commit()
    connection.close()

    return render_template(
        "result.html",

        product=product,

        status=status
    )


# =====================================================
# COMPLAINT
# =====================================================

@app.route(
    "/complaint",
    methods=["GET", "POST"]
)
def complaint():

    if "customer" not in session:

        return redirect(
            url_for(
                "customer_login"
            )
        )

    # GET se Product ID
    product_id = request.args.get(
        "product_id",
        ""
    ).strip()

    if request.method == "POST":

        product_id = request.form.get(
            "product_id",
            ""
        ).strip()

        complaint_text = request.form.get(
            "complaint",
            ""
        ).strip()

        if not complaint_text:

            return render_template(
                "complaint.html",

                product_id=product_id,

                error="Please enter your complaint."
            )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO complaints
            (
                product_id,
                customer_email,
                complaint,
                status
            )

            VALUES (?, ?, ?, 'Pending')
        """, (

            product_id,

            session["customer"],

            complaint_text
        ))

        connection.commit()
        connection.close()

        return redirect(
            url_for(
                "complaint_history"
            )
        )

    return render_template(
        "complaint.html",

        product_id=product_id
    )


# =====================================================
# CUSTOMER COMPLAINT HISTORY
# =====================================================

@app.route(
    "/customer/complaints"
)
def complaint_history():

    if "customer" not in session:

        return redirect(
            url_for(
                "customer_login"
            )
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM complaints
        WHERE customer_email = ?
        ORDER BY id DESC
    """, (
        session["customer"],
    ))

    complaints = cursor.fetchall()

    connection.close()

    return render_template(
        "complaint_history.html",

        complaints=complaints
    )


# =====================================================
# CUSTOMER VERIFICATION HISTORY
# =====================================================

@app.route(
    "/customer/history"
)
def customer_history():

    if "customer" not in session:

        return redirect(
            url_for(
                "customer_login"
            )
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM verification_history
        WHERE customer_email = ?
        ORDER BY id DESC
    """, (
        session["customer"],
    ))

    history = cursor.fetchall()

    connection.close()

    return render_template(
        "history.html",

        history=history
    )


# =====================================================
# ADMIN UPDATE COMPLAINT STATUS
# =====================================================

@app.route(
    "/admin/complaint/<int:complaint_id>/status",
    methods=["POST"]
)
def update_complaint_status(
    complaint_id
):

    if "admin" not in session:

        return redirect(
            url_for(
                "admin_login"
            )
        )

    status = request.form.get(
        "status",
        "Pending"
    )

    allowed_status = [

        "Pending",

        "Investigating",

        "Resolved",

        "Rejected"
    ]

    if status not in allowed_status:

        status = "Pending"

    connection = get_connection()
    cursor = connection.cursor()

    # Pehle check karo complaint exist karti hai
    cursor.execute("""
        SELECT id
        FROM complaints
        WHERE id = ?
    """, (
        complaint_id,
    ))

    complaint_exists = cursor.fetchone()

    if complaint_exists:

        # updated_at column available hai
        cursor.execute("""
            UPDATE complaints

            SET
                status = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
        """, (
            status,
            complaint_id
        ))

    connection.commit()
    connection.close()

    return redirect(
        url_for(
            "admin_dashboard"
        )
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route(
    "/logout"
)
def logout():

    # Proper logout
    session.clear()

    return redirect(
        url_for(
            "home"
        )
    )


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )