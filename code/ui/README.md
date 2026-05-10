# HospitalDB UI

Small raw-SQL Streamlit interface for demonstrating the HospitalDB schema, views,
stored procedures, triggers, and assignment queries.

## Run

Install dependencies:

```bash
python3 -m pip install --user -r code/ui/requirements.txt
```

Start the app:

```bash
python3 -m streamlit run code/ui/app.py
```

The sidebar reads these optional defaults:

```bash
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=HospitalDB
MYSQL_USER=root
MYSQL_PASSWORD=
```

The implementation deliberately uses `mysql-connector-python` and raw SQL. It
does not use an ORM.
