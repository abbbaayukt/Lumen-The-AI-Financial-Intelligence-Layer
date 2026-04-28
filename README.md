# Lumen — The AI Financial Intelligence Layer

Lumen is a full-stack intelligent finance system designed to automate expense tracking, bill management, document extraction, and real-time financial insights using AI.

This project includes:

* A modern React + TypeScript frontend
* A secure Flask backend with JWT authentication
* File uploads (images/PDFs), bill extraction, and verification
* Automatic transaction creation & categorisation
* AI-powered document analysis

---

# Screenshots

## Analysis Dashbord
<img width="1897" height="866" alt="image" src="https://github.com/user-attachments/assets/bdf4498c-33f8-47ee-8f82-76433d8b6616" />
<img width="1897" height="872" alt="image" src="https://github.com/user-attachments/assets/c6647644-6144-4aba-8f32-d6466690be77" />

## Past Transactions
<img width="1898" height="872" alt="image" src="https://github.com/user-attachments/assets/8f3ca2e2-aaf8-48d6-bf0b-bd82ac7f8044" />
<img width="1898" height="867" alt="image" src="https://github.com/user-attachments/assets/251138b4-5219-44b9-81cf-1396cc0a9092" />

## Add Bills
<img width="1897" height="862" alt="image" src="https://github.com/user-attachments/assets/7858c866-4713-4c8f-bdc7-860c2e6fb5b4" />

## Add Transactions
<img width="1898" height="871" alt="image" src="https://github.com/user-attachments/assets/a80c3748-0557-48d4-aebd-25dd0c0c217c" />

## GST Checker
<img width="1898" height="863" alt="image" src="https://github.com/user-attachments/assets/c673a39c-38cc-4167-903c-456b673494d6" />

## File ITR
<img width="1897" height="868" alt="image" src="https://github.com/user-attachments/assets/b33f82c4-6bbd-471a-a182-0688e628ab85" />

---

## 🚀 Features

### **1. Smart Transaction Management**

* Add, edit, and view transactions
* Category filtering
* Sorting by date (ASC/DESC)
* Pagination
* Bill preview (images) and bill download

### **2. AI-Powered Bill Extraction**

* Upload receipts or invoices
* Automated extraction of vendor, amount, date, and payment info
* Verification status (pending, verified, rejected)

### **3. User Authentication**

* JWT-based login/signup
* Protected routes on both frontend and backend

### **4. Full Document Pipeline**

* Every bill upload automatically:

  * Creates a Transaction
  * Creates a Document entry
  * Links the two together

### **5. Clean Financial Dashboard**

* Summary cards: Verified, Pending, Suspicious
* Table view with actions

### **6. ITR Form Filling**

* Automatically fills your ITR File based on your transaction
* Allows to directly download the PDF.

### **7. GST & Legitimacy Verification**

* Automatically verifies GSTIN from uploaded bills
* AI-powered "Legitimacy Report" for every transaction
* Fraud detection indicators (Verified vs Suspicious)

---

## 🏗️ Tech Stack

### **Frontend**

* React + TypeScript
* TailwindCSS
* ShadCN UI
* Axios API wrapper
* React Router

### **Backend**

* Flask (Python)
* Flask-JWT-Extended
* SQLAlchemy ORM
* SQLite / PostgreSQL
* File uploads + static file serving

---

## 🔧 Setup Instructions

### **Backend Setup**

```bash
cd backend
pip install -r requirements.txt
flask run
```

create .env file with gemini api and gst checker api
Backend runs at: `http://localhost:5000`

### **Frontend Setup**

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

## 🔑 Environment Variables (.env)

Create a `.env` file in the `backend/` directory with the following keys:

| Variable | Description |
| :--- | :--- |
| `JWT_SECRET_KEY` | Secret key for signing authentication tokens |
| `GEMINI_API_KEY_x` | Gemini AI keys for bill data extraction (Supports up to 3) |
| `API_1` to `API_10` | KnowYourGST keys for verifying merchant GST numbers |
| `TESSERACT_PATH` | Full path to the `tesseract.exe` binary (Local OCR) |
| `POPPLER_PATH` | Full path to the poppler `bin` directory (PDF processing) |

---

# 📡 Lumen API Endpoints

# 🔐 Authentication

## **POST /auth/signup**
Create a new user.

**Body:**
```json
{
  "first_name": "",
  "last_name": "",
  "email": "",
  "phone_number": "",
  "password": "",
  "organization": "",
  "aadhar_number": "",
  "pan_number": "",
  "date_of_birth": "",
  "employment_type": "",
  "annual_salary": "",
  "address": ""
}
````

---

## **POST /auth/login**

Authenticate user.

**Body:**

```json
{ "email": "", "password": "" }
```

**Response:**

```json
{
  "access": "<JWT_ACCESS>",
  "refresh": "<JWT_REFRESH>"
}
```

> [!NOTE]
> The JWT token includes the following additional claims in its payload:
> * `email`: The registered email of the user
> * `name`: The full name (First + Last) of the user

---

## **GET /auth/me** *(JWT Required)*

Returns the authenticated user's profile.

---

## **PUT /auth/update-profile** *(JWT Required)*

Update profile fields.

Accepts any subset of:

```
first_name, last_name, phone_number, organization,
aadhar_number, pan_number, date_of_birth, employment_type,
annual_salary, address, email
```

---

# 💸 Transactions

## **GET /transactions/all** *(JWT Required)*

Fetch paginated, optionally filtered, optionally sorted transactions.

**Query Params:**

```
page=1
per_page=20
category=food
sort=asc | desc | created_asc | created_desc
```

**Response:**

```json
{
  "transactions": [...],
  "page": 1,
  "total_pages": 3,
  "total": 60,
  "category_filter": null,
  "sort": "desc"
}
```

---

## **GET /transactions/<id>** *(JWT Required)*

Fetch a single transaction + linked document metadata.

---

## **POST /transactions/add** *(JWT Required)*

Create a manual transaction (non-bill).

**Body:**

```json
{
  "item_name": "",
  "amount": "",
  "category": "",
  "payment_mode": "",
  "transaction_date": "YYYY-MM-DD",
  "vendor": "",
  "description": "",
  "tags": ""
}
```

---

# 📄 Document + Bill Extraction

## **GET /document/** *(JWT Required)*

Fetch paginated documents.

**Query Params:**

```
page=1
limit=20
```

---

## **POST /document/add** *(JWT Required)*

Upload bill → OCR → LLM extraction → GST lookup → auto-create Transaction & Document.

**Form-Data:**

```
file: <file>
vendor: optional
category: optional
notes: optional
```

**Response:**

```json
{
  "transaction_id": 12,
  "document_id": 9,
  "status": "verified",
  "llm": { ...extracted_fields },
  "gst_details": { ... },
  "file_url": "/documents/<file>"
}
```

---

## **GET /documents/<filename>**

Downloads a stored bill file.

---

# 🧾 GST Lookup

## **POST /gst/check_public** *(JWT Required)*

Lookup GSTIN using rotating API keys.

**Body:**

```json
{ "gstin": "22AAAAA0000A1Z5" }
```

---

# 🧮 ITR Generation

## **POST /itr/generate** *(JWT Required)*

Generate a filled ITR PDF using user profile + transactions.

**Body:**

```json
{
  "form_data": { ... }
}
```

**Response:** A downloadable PDF.
