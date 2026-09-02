# Immverse Room Scan to 3D Gaussian Splat Backend

A FastAPI and PostgreSQL backend service for handling 3D room scan frame chunk uploads from Meta Quest 3 headsets, orchestrating COLMAP sparse reconstructions, and training Gaussian Splat models via AWS GPU instances[cite: 1, 2, 5].

---

## Technical Stack - 

* **Framework:** Python 3.11+ / FastAPI[cite: 1, 5]
* **Database:** PostgreSQL 14+ (running in Docker)[cite: 2, 5]
* **ORM:** SQLAlchemy 2.0[cite: 2]
* **System Engine:** Windows Subsystem for Linux (WSL 2 / Ubuntu)[cite: 1, 5]
* **Containerization:** Docker Desktop[cite: 1, 2]
* **3D Reconstruction Pipeline:** COLMAP & Splatfacto (Nerfstudio)[cite: 1, 2, 5]

---

## Project Structure

```text
metaOS_APK/
│
├── backend/
│   ├── models/             # SQLAlchemy ORM models (Scan, Job, Asset)
│   │   ├── asset.py
│   │   ├── job.py
│   │   └── scan.py
│   ├── routes/             # FastAPI REST endpoints
│   │   ├── scans.py
│   │   └── upload.py
│   ├── workers/            # Reconstruction scripts
│   │   ├── colmap_runner.py
│   │   ├── splatfacto_runner.py
│   │   └── worker.py
│   ├── uploads/            # Temporary local storage for keyframes & depth maps
│   ├── config.py           # Configuration settings
│   ├── database.py         # DB connection & table generation
│   ├── main.py             # FastAPI entry point
│   └── requirements.txt    # Python dependencies
│
├── .env                    # Local environment variables (git-ignored)
├── .gitignore              # Files excluded from version control
└── README.md               # Setup and daily execution guide

```

---

## One-Time Setup Instructions

If setting up on a new machine, follow these steps:

1. **Install Prerequisites:**
* Python 3.11+ (Ensure "Add to PATH" is checked during setup)


* VS Code


* Docker Desktop with WSL 2 backend enabled


* Git




2. **Set Up Python Virtual Environment:**
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary

```


3. **Set Up Environment Variables (`.env`):**
Create a `.env` file in the root folder with:
```env
DATABASE_URL=
SECRET_KEY=dev_secret_key_123

```



---

## Daily Execution Workflow

Follow these steps every day when starting work on the project:

### Step 1: Start Docker Desktop

1. Open **Docker Desktop** from Windows.
2. Wait until the bottom-left status indicator turns green (**"Engine running"**).



### Step 2: Start the PostgreSQL Database Container

Open a terminal (Windows Command Prompt or VS Code Terminal) and run:

```cmd
docker start postgres-db

```

*(If starting for the first time on a new system, run:)*

```cmd
docker run --name postgres-db -e POSTGRES_PASSWORD=dev123 -p 5432:5432 -d postgres

```

Verify that the container is running:

```cmd
docker ps

```

---

### Step 3: Launch the FastAPI Backend Server

1. Open **VS Code** to the `metaOS_APK` project folder.
2. Open the built-in terminal (`Ctrl + ~`).
3. Navigate to the `backend` folder and activate the virtual environment:
```cmd
cd backend
venv\Scripts\activate

```


4. Start the Uvicorn development server:


```cmd
uvicorn main:app --reload

```



The server will start at: `http://127.0.0.1:8000`

---

## Testing API Endpoints

Access the interactive Swagger API documentation in your browser:

* **Interactive Docs:** [http://127.0.0.1:8000/docs](https://www.google.com/search?q=http://127.0.0.1:8000/docs)
* **Alternative OpenAPI Docs:** [http://127.0.0.1:8000/redoc](https://www.google.com/search?q=http://127.0.0.1:8000/redoc)

### Key Endpoints:

1. **`GET /health`** - Check API and DB status


2. **`POST /scans/create`** - Create a new scan session ID


3. **`POST /scans/{scan_id}/upload-chunk`** - Upload frame chunks


4. **`GET /scans/{scan_id}/status`** - Track upload and reconstruction progress



---

## Inspecting Database Records

To view records inside PostgreSQL via Docker Exec:

```cmd
docker exec -it postgres-db psql -U postgres

```

Useful `psql` queries:

```sql
\dt                  -- List all tables (scans, jobs, assets)
SELECT * FROM scans; -- View created scan records
\q                   -- Exit psql

```