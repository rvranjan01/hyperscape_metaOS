# Immverse Room Scan Project: Beginner Review Guide

**Review level:** Beginner / non-technical reviewer  
**Purpose:** Explain what this project is intended to do, what each important file and function does, and what should be checked during a review.

## 1. What This Project Is

This project is the beginning of a service for turning room scans from a Meta Quest 3s headset into a 3D result.

In simple terms:

1. A headset starts a new room scan.
2. The headset sends the scan data to the backend in smaller files called chunks.
3. The backend saves those files and counts how many have arrived.
4. When all expected files arrive, the scan is marked as ready for processing.
5. Planned processing tools, such as COLMAP and Splatfacto, are intended to create a 3D reconstruction and Gaussian Splat result.

**Important current-state note:** The scan creation, upload, counting, and status functions exist. The automatic 3D processing workers are currently empty, and there are no frontend files in this workspace yet.

## 2. What Is Actually Implemented

| Area                           | Current state                              |
| ------------------------------ | ------------------------------------------ |
| API server                     | Present in `backend/main.py`               |
| Create a scan                  | Implemented                                |
| Upload a scan chunk            | Implemented                                |
| Check scan progress            | Implemented                                |
| Database tables                | Defined and created automatically          |
| PostgreSQL connection          | Implemented with a fixed connection string |
| COLMAP processing              | Placeholder file only                      |
| Splatfacto processing          | Placeholder file only                      |
| Background worker              | Placeholder file only                      |
| Frontend application           | No files currently present                 |
| Authentication / user accounts | Not implemented                            |
| Cloud storage such as AWS S3   | Not implemented in the current code        |

## 3. Simple End-to-End Flow

```text
Headset or client
      |
      | 1. POST /scans/create
      v
Backend creates a Scan record
      |
      | 2. POST /scans/{scan_id}/upload-chunk
      v
Backend saves each file in uploads/{scan_id}/
      |
      | 3. GET /scans/{scan_id}/status
      v
Client sees upload progress
      |
      | When the expected number of files arrives
      v
Scan status changes from "uploading" to "processing"
      |
      | Future work
      v
COLMAP reconstruction -> Splatfacto training -> final 3D assets
```

## 4. Project Folders and Files

### Root folder

- `README.md`: Setup instructions and a high-level description of the project.
- `.env`: Local settings such as the database URL and secret key. The current application does not read these values correctly yet.
- `.gitignore`: Lists local files that should not be committed, including virtual environments, uploads, and environment files.
- `PROJECT_FUNCTIONAL_REVIEW.md`: This beginner-friendly review guide.

### `backend/`

The Python server code lives here.

- `main.py`: Starts the FastAPI application and contains the main scan endpoints.
- `database.py`: Connects to PostgreSQL and defines the database tables.
- `config.py`: Intended for configuration, but currently empty.
- `requirements.txt`: Lists Python packages required by the project.

### `backend/routes/`

Routes are the web addresses that clients can call.

- `upload.py`: Contains the file upload endpoint.
- `scans.py`: Intended for scan-related endpoints, but currently empty.

### `backend/models/`

This folder is intended to contain database model files.

- `scan.py`: Currently empty; the active `Scan` model is defined in `database.py`.
- `job.py`: Currently empty; the active `Job` model is defined in `database.py`.
- `asset.py`: Currently empty; the active `Asset` model is defined in `database.py`.

### `backend/workers/`

These files are intended to run long or heavy 3D processing tasks.

- `worker.py`: Currently empty.
- `colmap_runner.py`: Currently empty. It is intended to run COLMAP reconstruction.
- `splatfacto_runner.py`: Currently empty. It is intended to train a Gaussian Splat model.

### `backend/uploads/`

Temporary local storage for uploaded scan files. Each scan should have its own folder.

## 5. Active Functions Explained

### Functions in `backend/main.py`

#### `root()`

- **Web address:** `GET /`
- **Purpose:** Returns a welcome message.
- **Why it matters:** It confirms that the API server can answer a basic request.
- **Expected result:** A message saying the Immverse Room Scan API is available.

#### `health_check()`

- **Web address:** `GET /health`
- **Purpose:** Reports that the service is online.
- **Why it matters:** Monitoring tools can use it to check whether the server is reachable.
- **Review warning:** It always says the database is connected. It does not actually test the database connection, so it can report a healthy result even when the database is unavailable.

#### `create_scan(request)`

- **Web address:** `POST /scans/create`
- **Purpose:** Creates a new scan session in the database.
- **Input:** A device name and the expected number of frames.
- **What it does:** Opens a database session, creates a `Scan` record, saves it, and returns the new scan ID and status.
- **Why it matters:** The returned scan ID is needed for later uploads and status checks.

#### `get_scan_status(scan_id)`

- **Web address:** `GET /scans/{scan_id}/status`
- **Purpose:** Shows how much of a scan has been uploaded.
- **What it does:** Finds the scan, calculates the percentage uploaded, and returns the counts and current status.
- **Error behavior:** Returns HTTP 404 when the scan ID does not exist.
- **Review warning:** It reads the database correctly for normal use, but the code should also be checked for reliable cleanup if a database error occurs.

### Function in `backend/routes/upload.py`

#### `upload_chunk(scan_id, chunk)`

- **Web address:** `POST /scans/{scan_id}/upload-chunk`
- **Purpose:** Receives one uploaded scan file.
- **What it does:**
  1. Looks up the scan ID.
  2. Creates a folder for that scan.
  3. Saves the uploaded file using its filename.
  4. Increases the uploaded frame count by one.
  5. Changes the scan status to `processing` when the expected count is reached.
  6. Saves the updated count in the database.
- **Success result:** Returns the filename, uploaded count, expected count, and scan status.
- **Error behavior:** Returns HTTP 404 when the scan ID does not exist.
- **Important review warnings:** The endpoint does not validate file type or file size, does not prevent duplicate uploads from being counted twice, and uses the client-provided filename directly. These should be addressed before exposing the endpoint to untrusted users.

## 6. How a Beginner Can Test the Working Flow

The easiest way to test the current project is through the automatic API page at `http://127.0.0.1:8000/docs` after the server has been started.

### Test 1: Check that the server is running

Open `GET /health` and select **Try it out**, then **Execute**.

Expected result:

```json
{
  "status": "online",
  "database": "connected"
}
```

Remember that this response does not truly test the database connection yet. It only proves that the API process answered.

### Test 2: Create a scan

Open `POST /scans/create`, select **Try it out**, and enter an example such as:

```json
{
  "device_name": "Test Quest 3",
  "total_frames": 2
}
```

Expected result:

- A unique `scan_id` is returned.
- The status is `uploading`.
- The device name matches the submitted value.

Keep the returned `scan_id`. It is needed for the next tests.

### Test 3: Upload a file

Open `POST /scans/{scan_id}/upload-chunk`.

1. Replace `{scan_id}` with the ID from Test 2.
2. Select **Try it out**.
3. Choose a small test file.
4. Select **Execute**.

Expected result:

- The response says `received`.
- `uploaded_frames` increases to `1`.
- A matching file appears inside `backend/uploads/{scan_id}/`.

Upload another test file. Because the scan expected two frames, the status should then become `processing`.

### Test 4: Check progress

Open `GET /scans/{scan_id}/status` using the same scan ID.

Expected result after two uploads:

```json
{
  "uploaded_frames": 2,
  "total_frames": 2,
  "progress_percentage": 100.0,
  "status": "processing"
}
```

The exact scan ID will be different for every test.

### Test 5: Check an invalid scan ID

Use a made-up ID with either the upload or status endpoint.

Expected result: HTTP 404 with a message that the scan ID was not found.

## 7. What Counts as a Successful Review

For the currently implemented part of the project, a successful review should confirm all of these points:

1. The API starts and responds.
2. A scan can be created in the database.
3. A scan file can be saved in the correct folder.
4. The upload count increases correctly.
5. The status changes to `processing` at the expected point.
6. An unknown scan ID is rejected.
7. Unsafe or unexpected files are rejected or handled safely.

The first five points describe current intended behavior. The sixth point is already implemented. The seventh point is a known improvement area and should be treated as a release requirement before real users upload files.

## 8. Database Terms and Records

`database.py` uses SQLAlchemy. SQLAlchemy is a Python tool that lets the application work with database tables using Python classes.

### `Scan` table

Represents one room scanning session.

| Field             | Meaning                                                    |
| ----------------- | ---------------------------------------------------------- |
| `id`              | Unique identifier for the scan, generated as a UUID string |
| `device_name`     | Name of the headset or device                              |
| `created_at`      | Time the scan was created                                  |
| `status`          | Current stage, initially `uploading`                       |
| `total_frames`    | Number of files expected                                   |
| `uploaded_frames` | Number of files received so far                            |

### `Job` table

Represents a future processing task.

| Field        | Meaning                                                        |
| ------------ | -------------------------------------------------------------- |
| `id`         | Unique job identifier                                          |
| `scan_id`    | Scan that the job belongs to                                   |
| `stage`      | Planned stage such as `colmap` or `splat_training`             |
| `status`     | Planned state such as `queued`, `running`, `done`, or `failed` |
| `created_at` | Time the job was created                                       |

**Current state:** The table is defined, but the current code does not create or process jobs.

### `Asset` table

Represents a generated file related to a scan, such as a thumbnail, point cloud, or splat file.

| Field        | Meaning                                   |
| ------------ | ----------------------------------------- |
| `id`         | Unique asset identifier                   |
| `scan_id`    | Scan that produced the asset              |
| `file_type`  | Type of generated file                    |
| `s3_key`     | Planned location of the file in Amazon S3 |
| `created_at` | Time the asset was recorded               |

**Current state:** The table is defined, but the current code does not create asset records or upload files to S3.

### Database setup behavior

`Base.metadata.create_all(bind=engine)` creates the tables when `database.py` is imported. This is convenient for early development, but production systems normally use controlled database migrations so that changes can be reviewed and safely applied.

## 9. API Terms in Plain Language

- **API:** A set of web addresses that another program can call.
- **Endpoint / route:** One API address, such as `/health`.
- **GET:** A request used to read information.
- **POST:** A request used to create or send information.
- **Request:** Data sent to the server.
- **Response:** Data returned by the server.
- **HTTP 404:** The requested item was not found.
- **JSON:** A simple text format used to send structured data.
- **FastAPI:** The Python framework used to build the API.
- **Uvicorn:** The program that runs the FastAPI server.
- **Swagger / OpenAPI docs:** A browser page that lists and lets a person test the API endpoints.

## 10. Technical Terms in Plain Language

- **Backend:** The server-side part of an application.
- **Frontend:** The user-facing screen or application. No frontend code is currently present here.
- **Database:** A structured place for storing information.
- **PostgreSQL:** The database software used by this project.
- **Table:** A database structure containing related records.
- **Record / row:** One saved item in a table.
- **ORM:** A tool that lets code work with database records as objects. SQLAlchemy is the ORM here.
- **UUID:** A long, practically unique identifier used for scans, jobs, and assets.
- **File upload chunk:** One file or piece of scan data sent to the server.
- **Frame:** One captured image or scan unit from the headset. The current code assumes one uploaded file equals one frame.
- **Worker:** A separate process that performs a time-consuming task without blocking normal API requests.
- **COLMAP:** A computer-vision tool that can estimate camera positions and create a sparse 3D reconstruction from images.
- **Gaussian Splat / Splatfacto:** A method and tool for representing a 3D scene using many soft, colored points.
- **S3:** Amazon's cloud file storage service. It is referenced by the design but is not connected in the current implementation.
- **Environment variable:** A setting supplied outside the code, often used for passwords and connection details.
- **Docker:** A tool for running software such as PostgreSQL in a separate container.
- **Virtual environment:** An isolated Python installation for this project.

## 11. Beginner Review Checklist

### Basic behavior

- [ ] The server starts without errors.
- [ ] `GET /` returns a welcome response.
- [ ] `GET /health` works.
- [ ] Creating a scan returns a unique scan ID.
- [ ] Creating a scan with a missing or invalid value gives a clear error.
- [ ] Uploading a file for a valid scan saves the file.
- [ ] Uploading to an unknown scan ID returns HTTP 404.
- [ ] The status endpoint reports the correct upload count.
- [ ] The scan changes to `processing` only after the expected number of uploads.
- [ ] The database contains the expected scan record.

### Data and security

- [ ] Database passwords are not hard-coded in source code.
- [ ] The `.env` file is not committed to source control.
- [ ] Upload filenames are cleaned or replaced with server-generated names.
- [ ] File size and allowed file types are limited.
- [ ] Duplicate files cannot incorrectly increase the frame count.
- [ ] Users cannot access another user's scans without permission.
- [ ] Authentication and authorization requirements are defined.
- [ ] Error messages do not reveal passwords, internal paths, or private data.

### Reliability

- [ ] Database sessions close even when an error occurs.
- [ ] Partial uploads can be retried safely.
- [ ] The server does not lose track of uploads after a restart.
- [ ] Large files do not exhaust disk space or memory.
- [ ] Failed processing jobs are recorded and can be retried.
- [ ] Logs exist for uploads, failures, and processing progress.
- [ ] Health checking confirms the real database connection.

### 3D processing

- [ ] A completed scan creates a processing job.
- [ ] The COLMAP step actually runs and reports success or failure.
- [ ] The Splatfacto step actually runs and reports success or failure.
- [ ] Generated files are stored in a durable location.
- [ ] Generated files are recorded in the `assets` table.
- [ ] The client can retrieve or download the final result.

## 12. Main Findings From This Review

1. **The upload workflow is the main implemented feature.** Scan creation, chunk saving, counting, and status reporting are present.
2. **The 3D processing pipeline is not implemented yet.** The worker, COLMAP, and Splatfacto files are empty.
3. **The frontend is not implemented in this workspace.** The `frontend` folder contains no source files.
4. **Configuration is incomplete.** The project has a `.env` file and an empty `config.py`, but `database.py` uses a hard-coded database URL instead of reading the environment setting.
5. **The health endpoint is optimistic.** It reports the database as connected without performing a database check.
6. **Upload validation needs attention.** File type, size, duplicate handling, filename safety, and access control are not implemented.
7. **The database model files are placeholders.** The active models are in `database.py`, which can make future maintenance confusing.
8. **The requirements file should be reviewed.** It contains many packages, while the visible application currently uses only a smaller subset. The team should confirm which dependencies are intentional.

## 13. Short Reviewer Conclusion

This project is a working early backend prototype for receiving room-scan files and tracking their upload progress. It is not yet a complete room-to-3D product because the background processing pipeline, generated asset management, frontend, authentication, and production safeguards are still missing.

For a beginner review, the most important question is:

> Can a scan be created, uploaded safely and completely, processed successfully, and then retrieved by the correct user?

At the current stage, only the first part of that journey, up to marking a scan as `processing`, is implemented.
