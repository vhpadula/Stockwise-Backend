# 📦 Stockwise-Backend

Stockwise is a **lot-based inventory management system** for **Food & Beverage CPG brands**, tracking products, purchase orders, sales, and profits.
It uses **Django + PostgreSQL + DRF** and supports **FIFO stock management**.

---

## 📝 Features

- Register products with units: kg, g, L, mL, unit
- Manage stocks via purchase orders or manual additions
- Record sales orders
- Track financials: revenue, costs, profit, profit margins
- FIFO stock consumption and COGS calculation
- Role-based authentication and authorization (admin/manager/staff)

---

## 📂 Project Structure

```
stockwise-backend/
│
├── config/               # Django settings
├── inventory/            # Product & Stock models
├── purchases/            # Purchase Orders
├── sales/                # Sales Orders
├── users/                # Custom user model
│
├── Dockerfile
├── docker-compose.yml
├── Pipfile
├── Pipfile.lock
├── .env
├── manage.py
├── README.md
```

---

## ⚙️ Requirements

- Python 3.11+
- Pipenv
- Docker & Docker Compose (optional but recommended)

---

## 🏃 Running Locally (Pipenv)

1. **Clone the repo**:

```bash
git clone https://github.com/vhpadula/Stockwise-Backend.git
cd Stockwise-Backend
```

2. **Install dependencies**:

```bash
pipenv install --dev
pipenv shell
```

3. **Configure environment variables**:

Create a `.env` file in the root:

```env
DEBUG=True
SECRET_KEY=super-secret-key

DATABASE_NAME=stockwise
DATABASE_USER=postgres
DATABASE_PASSWORD=defaultpwd
DATABASE_HOST=localhost
DATABASE_PORT=5432

APP_INTERNAL_PORT=8000
APP_EXTERNAL_PORT=8000
DB_EXTERNAL_PORT=5432
```

4. **Run migrations** (note: you'll need a DB running at the specified port on the .env):

```bash
python manage.py makemigrations
python manage.py migrate
```

I've also included a SQL Dump with examples for two separate users

Alice

- email: alice@example.com
- password: secret

and Bob

- email: bob@example.com
- password: secret

5. **Create superuser**:

```bash
python manage.py createsuperuser
```

6. **Start server**:

```bash
python manage.py runserver 0.0.0.0:8000
```

Open in browser:

```
http://localhost:8000
```

---

## 🐳 Running with Docker Compose

1. **Ensure Docker and Docker Compose are installed**

2. **Build and start containers**:

```bash
docker compose up --build
```

This will start:

- **PostgreSQL** on port defined by `DB_EXTERNAL_PORT` in `.env`
- **Django API (Gunicorn)** on port defined by `APP_EXTERNAL_PORT` in `.env`

3. **Access the API**:

```
http://localhost:8000
```

4. **Stop containers**:

```bash
docker compose down
```

---

## ⚡ Environment Variables

| Variable            | Description                                            |
| ------------------- | ------------------------------------------------------ |
| `DEBUG`             | Django debug mode                                      |
| `SECRET_KEY`        | Django secret key                                      |
| `DATABASE_NAME`     | Postgres database name                                 |
| `DATABASE_USER`     | Postgres user                                          |
| `DATABASE_PASSWORD` | Postgres password                                      |
| `DATABASE_HOST`     | Postgres host (`db` for Docker, `localhost` for local) |
| `DATABASE_PORT`     | Postgres port                                          |
| `DB_EXTERNAL_PORT`  | Port mapped on host for Postgres                       |
| `APP_INTERNAL_PORT` | Port Gunicorn listens to inside container              |
| `APP_EXTERNAL_PORT` | Port exposed on host for Django API                    |

---

## 🔒 Authentication & Authorization

- Uses **custom user model** (`users.User`)
- JWT-based authentication via DRF
- Object-level permissions ensure users only access **their own inventory, purchase and sales orders**

---

## 💡 Notes

- All quantities are stored in **base units** (`g`, `kg`, `ml`, `L`, `unit`)
- Inventory is **lot-based**
- Profit is calculated from **StockMovement (COGS)**
- FIFO strategy is applied when selling products
