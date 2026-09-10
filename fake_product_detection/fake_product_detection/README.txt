FAKE PRODUCT DETECTION - BARCODE-BASED BLOCKCHAIN SYSTEM

LOCAL VS CODE
1. Open this folder in VS Code.
2. Create/activate a virtual environment if desired.
3. Run: pip install -r requirements.txt
4. Run: python app.py
5. Open: http://127.0.0.1:5000
6. Local mode uses SQLite automatically when DATABASE_URL is not set.

RENDER + POSTGRESQL
1. Create a Render PostgreSQL database in the same region as the web service.
2. In the Render Web Service Environment, add DATABASE_URL using the PostgreSQL Internal Database URL.
3. Deploy with:
   Build Command: cd fake_product_detection && pip install -r requirements.txt
   Start Command: cd fake_product_detection && gunicorn app:app
4. PostgreSQL stores users, products, verification history, complaints, and blockchain blocks permanently.
5. QR codes are generated dynamically, so they do not depend on Render's temporary filesystem.

DEFAULT ADMIN
Email: admin@gmail.com
Password: admin123

IMPORTANT
Change SECRET_KEY and the default admin password before using the project for real users.
