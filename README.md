# 🧩 Airline Database Practice (SQL + Flask)

## 1. Project Description
This exercise helps you practice writing SQL queries in a real environment.
You will connect a pre-built SQLite database (`airline.sqlite`) with a simple Flask back-end and a front-end dashboard.
By completing the **five TODO sections** inside `server.py`, you will make the system display real data for:

- Employee list (checkbox selection)
- Flights per aircraft (bar chart)
- Employee salary and certificate summary (table)

You can get the database file on Canvas.
![Database_resource](/src/Database_resource.png)

---

## 2. Environment Setup

Please make sure your environment includes the following packages:

```bash
pip install flask
```

Optional (for debugging SQLite):

```bash
pip install db-browser-for-sqlite
```

Folder structure overview:

```
├── server.py             # Flask server (you will edit only the TODOs)
├── web/                  # Front-end files (HTML, JS, CSS)
│   ├── index.html
│   └── main.js
├── data/
│   └── airline.sqlite    # SQLite database file
└── README.md
```

> 💡 **Do not rename files or folders.**
> The Flask app expects this exact structure.

---

## 3. How to Run

**Step 1.** Start the Flask server  
From your project folder, run:

```bash
python server.py
```

If successful, you should see:

```
* Running on http://127.0.0.1:5175
```

**Step 2.** Open the web dashboard  
In your browser, visit:

```
http://127.0.0.1:5175
```

You should see a page with a bar chart on the left and a table on the right.
(If it shows “Loading…” or is empty, you still need to finish the SQL queries.)

---

## 4. What to Edit

Only modify the **five TODO sections** in `server.py`.
Each TODO includes a detailed description of what the query should return.
Write your SQL code inside the marked block:

```python
rows = query_db("""
    -- WRITE YOUR SQL HERE
""")
```

The five TODOs are:

| TODO ID | Description |
|----------|-------------|
| 01 | Return employee list for the checkbox menu |
| 02 | Count total flights per aircraft |
| 03 | Retrieve one employee’s full name by their ID |
| 04 | Count flights for aircraft an employee is certified to operate |
| 05 | List employees with at least one certificate and their salary |

---

## 5. Submission Format

Each group should submit the following:

1. **A screenshot** of the running dashboard (browser view):  
   - The left chart shows correct flight counts.  
   - The right table shows real employee and certificate data.  
   - Choosing same Employee's name as following screenshot.
   ![Submission_example](/src/Submission_example.png)


2. Please name your screenshot file:  
   ```
   GroupNumbe_Airline_SQL.png
   ```
4. Upload the screenshot to week 8 Teams channel.

---

✅ **Reminder:**
- You do **not** need to change any HTML, CSS, or JavaScript.
- Only edit the five SQL TODOs in `server.py`.
- Make sure the port is `5175` (default).
- If you see “no such column” errors, check your column names using DB Browser.
