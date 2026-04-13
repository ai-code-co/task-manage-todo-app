# Django Task Manager API

A small Django + Django REST Framework project for creating, listing, updating, completing, searching, and soft-deleting tasks.

## What This Project Includes

- A basic frontend page at `/` for creating and managing tasks
- A REST API at `/api/`
- Task fields for title, description, status, and priority
- Search by `title` and `description`
- Filter by `status` and `priority`
- Soft delete support with `is_deleted` and `deleted_at`

## Tech Stack

- Python
- Django 5.2.13
- Django REST Framework 3.17.1
- django-filter 25.2
- django-cors-headers 4.9.0
- python-decouple 3.8
- psycopg 3.3.3
- PostgreSQL

## Project Structure

```text
task-manager-api/
|-- README.md
|-- venv/
|-- backend/
|   |-- manage.py
|   |-- .env
|   |-- db.sqlite3
|   |-- templates/
|   |   `-- index.html
|   |-- tasks/
|   |   |-- models.py
|   |   |-- serializers.py
|   |   |-- tests.py
|   |   |-- urls.py
|   |   `-- views.py
|   `-- config/
|       |-- settings.py
|       `-- urls.py
`-- frontend/
    |-- index.html
    |-- tester.css
    `-- tester.js
```

## API Routes

- `GET /api/` List all non-deleted tasks
- `POST /api/` Create a task
- `GET /api/<id>/` Get one task
- `PATCH /api/<id>/` Update part of a task
- `PUT /api/<id>/` Replace a task
- `DELETE /api/<id>/` Soft delete a task

## Search And Filter Examples

- `GET /api/?status=pending`
- `GET /api/?priority=high`
- `GET /api/?search=meeting`

## Environment Variables

Create a `.env` file in `backend/.env` with:

```env
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=5432
```

## Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install the required packages.
4. Add your `.env` file.
5. Run migrations.
6. Start the server.

Example on Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install Django==5.2.13 djangorestframework==3.17.1 django-filter==25.2 django-cors-headers==4.9.0 python-decouple==3.8 psycopg==3.3.3
python .\backend\manage.py migrate
python .\backend\manage.py runserver
```

## How To Use

- Open `http://127.0.0.1:8000/` for the basic backend-rendered page
- Open `http://127.0.0.1:8000/api/` for the DRF API view
- Create a task from the frontend form
- Use the buttons to complete or delete tasks

## Query Param Tester On Port 5500

To test filtering, sorting, pagination, and `page_size` without landing on the DRF page, use the standalone tester in `frontend/`:

- File: `frontend/index.html`
- API used by the tester: `http://127.0.0.1:8000/api/tasks/`

From the repository root, run:

```powershell
Set-Location .\frontend
..\venv\Scripts\python.exe -m http.server 5500
```

Then open:

- `http://127.0.0.1:5500/`

Example query-param URL:

- `http://127.0.0.1:5500/?status=pending&priority=high&ordering=-created_at&page=1&page_size=5`

This tester keeps the frontend state in the browser URL so you can verify:

- `search`
- `status`
- `priority`
- `ordering`
- `page`
- `page_size`

## Testing

Run:

```powershell
python .\backend\manage.py test
```

## Important Note About Delete

Deleting a task does not remove it permanently from the database.
The project uses soft delete:

- `is_deleted=True`
- `deleted_at` is set
- hidden tasks no longer appear in the normal task list

## Current Behavior

- Frontend route: `/`
- API route: `/api/`
- Deleted tasks are hidden from list results
