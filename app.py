from flask import Flask, render_template, request, send_from_directory, flash
from delhi_court import scrape_case
import sqlite3
import datetime
import os
import json # To store structured data in DB

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # IMPORTANT: Change this to a strong, random key

# Define the path where downloaded PDFs will be stored (optional, for local serving)
DOWNLOAD_FOLDER = 'downloaded_pdfs'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Define case types and years (consistent with scraper)
CASE_TYPES = sorted([
    "ADMIN.REPORT", "ARB.A.", "ARB. A. (COMM.)", "ARB.P.", "BAIL APPLN.", "CA", "CA (COMM.IPD-CR)",
    "C.A.(COMM.IPD-GI)", "C.A.(COMM.IPD-PAT)", "C.A.(COMM.IPD-PV)", "C.A.(COMM.IPD-TM)", "CAVEAT(CO.)",
    "CC(ARB.)", "CCP(CO.)", "CCP(REF)", "CEAC", "CEAR", "CHAT.A.C.", "CHAT.A.REF", "CMI", "CM(M)",
    "CM(M)-IPD", "C.O.", "CO.APP.", "CO.APPL.(C)", "CO.APPL.(M)", "CO.A(SB)", "C.O.(COMM.IPD-CR)",
    "C.O.(COMM.IPD-GI)", "C.O.(COMM.IPD-PAT)", "C.O. (COMM.IPD-TM)", "CO.EX.", "CONT.APP.(C)",
    "CONT.CAS(C)", "CONT.CAS.(CRL)", "CO.PET.", "C.REF.(O)", "CRL.A.", "CRL.L.P.", "CRL.M.C.",
    "CRL.M.(CO.)", "CRL.M.I.", "CRL.O.", "CRL.O.(CO.)", "CRL.REF.", "CRL.REV.P.", "CRL.REV.P.(MAT.)",
    "CRL.REV.P.(NDPS)", "CRL.REV.P.(NI)", "C.R.P.", "CRP-IPD", "C.RULE", "CS(COMM)", "CS(OS)",
    "CS(OS) GP", "CUSAA", "CUS.A.C.", "CUS.A.R.", "CUSTOM A.", "DEATH SENTENCE REF.", "DEMO", "EDC",
    "EDR", "EFA(COMM)", "EFA(OS)", "EFA(OS)  (COMM)", "EFA(OS)(IPD)", "EL.PET.", "ETR", "EX.F.A.",
    "EX.P.", "EX.S.A.", "FAO", "FAO (COMM)", "FAO-IPD", "FAO(OS)", "FAO(OS) (COMM)", "FAO(OS)(IPD)",
    "GCAC", "GCAR", "GTA", "GTC", "GTR", "I.A.", "I.P.A.", "ITA", "ITC", "ITR", "ITSA", "LA.APP.",
    "LPA", "MAC.APP.", "MAT.", "MAT.APP.", "MAT.APP.(F.C.)", "MAT.CASE", "MAT.REF.",
    "MISC. APPEAL(PMLA)", "OA", "OCJA", "O.M.P.", "O.M.P. (COMM)", "OMP (CONT.)", "O.M.P. (E)",
    "O.M.P. (E) (COMM.)", "O.M.P.(EFA)(COMM.)", "OMP (ENF.) (COMM.)", "O.M.P.(I)", "O.M.P.(I) (COMM.)",
    "O.M.P. (J) (COMM.)", "O.M.P. (MISC.)", "O.M.P.(MISC.)(COMM.)", "O.M.P.(T)", "O.M.P. (T) (COMM.)",
    "O.REF.", "RC.REV.", "RC.S.A.", "RERA APPEAL", "REVIEW PET.", "RFA", "RFA(COMM)", "RFA-IPD",
    "RFA(OS)", "RFA(OS)(COMM)", "RF(OS)(IPD)", "RSA", "SCA", "SDR", "SERTA", "ST.APPL.", "STC",
    "ST.REF.", "SUR.T.REF.", "TEST.CAS.", "TR.P.(C)", "TR.P.(C.)", "TR.P.(CRL.)", "VAT APPEAL",
    "W.P.(C)", "W.P.(C)-IPD", "WP(C)(IPD)", "W.P.(CRL)", "WTA", "WTC", "WTR"
])
YEARS = [str(y) for y in range(datetime.datetime.now().year, 1950, -1)]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        case_type = request.form['case_type']
        case_number = request.form['case_number']
        case_year = request.form['case_year']

        if not case_number.strip():
            flash("Please enter a case number.", 'warning')
            return render_template('index.html', case_types=CASE_TYPES, years=YEARS)

        # Scrape data
        # The scrape_case function now returns a dict and raw HTML
        scraped_data, raw_html = scrape_case(case_type, case_number, case_year)

        # Connect to SQLite database
        conn = sqlite3.connect('db.sqlite3')
        cur = conn.cursor()

        # Create table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_type TEXT,
                case_number TEXT,
                case_year TEXT,
                scraped_data_json TEXT, -- Store structured data as JSON
                raw_html TEXT,
                timestamp DATETIME
            )
        ''')

        # Insert query details into the database
        cur.execute(
            "INSERT INTO queries (case_type, case_number, case_year, scraped_data_json, raw_html, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (case_type, case_number, case_year, json.dumps(scraped_data), raw_html, datetime.datetime.now())
        )
        conn.commit()
        conn.close()

        if "error" in scraped_data:
            flash(scraped_data['error'], 'danger')
            return render_template('index.html', case_types=CASE_TYPES, years=YEARS)
        else:
            return render_template('result.html', data=scraped_data)

    return render_template('index.html', case_types=CASE_TYPES, years=YEARS)

# Route to serve downloaded PDFs (if you implement a download feature)
@app.route('/downloads/<filename>')
def downloaded_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)


if __name__ == '__main__':
    # Initialize the database table when the app starts if it doesn't exist
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_type TEXT,
            case_number TEXT,
            case_year TEXT,
            scraped_data_json TEXT,
            raw_html TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()
    app.run(debug=True) # Run in debug mode for development