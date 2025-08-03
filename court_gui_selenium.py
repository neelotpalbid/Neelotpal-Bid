import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ----------- Function to Fetch Case Data Using Selenium -----------
def fetch_case_with_selenium(case_type, case_number, year):
    try:
        url = "https://delhihighcourt.nic.in/app/get-case-type-status"

        # ✅ ChromeDriver setup (REQUIRED: ChromeDriver must be at this path)
        driver_path = r"D:\chromedriver\chromedriver.exe"
        options = Options()
        options.add_argument("--headless")        # You can comment this to see browser
        options.add_argument("--disable-gpu")
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # Fill the form
        Select(wait.until(EC.presence_of_element_located((By.NAME, "case_type")))).select_by_visible_text(case_type)
        driver.find_element(By.NAME, "case_number").send_keys(case_number)
        Select(wait.until(EC.presence_of_element_located((By.NAME, "cyear")))).select_by_visible_text(str(year))
        captcha = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "captcha-code"))).text.strip()
        driver.find_element(By.NAME, "captchaInput").send_keys(captcha)

        # Submit the form
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")))
        submit_btn.click()

        # Fetch Result
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table-responsive")))
            pet_name = driver.find_element(By.ID, "pet_name").text.strip()
            table_text = driver.find_element(By.CLASS_NAME, "table-responsive").text.strip()
            result = f"{pet_name}\n\n{table_text}"
        except:
            result = "[!] No case data found or captcha failed."

        driver.quit()
        return result

    except Exception as e:
        return f"[Error] {str(e)}"

# ----------- GUI Submit Logic -----------
def on_submit():
    case_type = case_type_var.get()
    case_number = case_number_entry.get()
    year = year_var.get()

    if not case_number.strip():
        messagebox.showwarning("Missing Input", "Please enter a case number.")
        return

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "Fetching data, please wait...\n")
    root.update_idletasks()

    result = fetch_case_with_selenium(case_type, case_number, year)
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, result)

# ----------- GUI Setup -----------
root = tk.Tk()
root.title("Delhi High Court Case Data Fetcher")
root.geometry("800x600")

# --- Case Types Dropdown (Full List) ---
case_types = sorted([
    "ADMIN.REPORT", "ARB.A.", "ARB. A. (COMM.)", "ARB.P.", "BAIL APPLN.", "CA", "CA (COMM.IPD-CR)",
    "C.A.(COMM.IPD-GI)", "C.A.(COMM.IPD-PAT)", "C.A.(COMM.IPD-PV)", "C.A.(COMM.IPD-TM)", "CAVEAT(CO.)",
    "CC(ARB.)", "CCP(CO.)", "CCP(REF)", "CEAC", "CEAR", "CHAT.A.C.", "CHAT.A.REF", "CMI", "CM(M)",
    "CM(M)-IPD", "C.O.", "CO.APP.", "CO.APPL.(C)", "CO.APPL.(M)", "CO.A(SB)", "C.O.(COMM.IPD-CR)",
    "C.O.(COMM.IPD-GI)", "C.O.(COMM.IPD-PAT)", "C.O. (COMM.IPD-TM)", "CO.EX.", "CONT.APP.(C)",
    "CONT.CAS(C)", "CONT.CAS.(CRL)", "CO.PET.", "C.REF.(O)", "CRL.A.", "CRL.L.P.", "CRL.M.C.",
    "CRL.M.(CO.)", "CRL.M.I.", "CRL.O.", "CRL.O.(CO.)", "CRL.REF.", "CRL.REV.P.", "CRL.REV.P.(MAT.)",
    "CRL.REV.P.(NDPS)", "CRL.REV.P.(NI)", "C.R.P.", "CRP-IPD", "C.RULE", "CS(COMM)", "CS(OS)",
    "CS(OS) GP", "CUSAA", "CUS.A.C.", "CUS.A.R.", "CUSTOM A.", "DEATH SENTENCE REF.", "DEMO", "EDC",
    "EDR", "EFA(COMM)", "EFA(OS)", "EFA(OS)  (COMM)", "EFA(OS)(IPD)", "EL.PET.", "ETR", "EX.F.A.",
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

tk.Label(root, text="Case Type:").pack(anchor="w", padx=10, pady=(10, 0))
case_type_var = tk.StringVar()
case_type_dropdown = ttk.Combobox(root, textvariable=case_type_var, values=case_types, width=65)
case_type_dropdown.current(0)
case_type_dropdown.pack(padx=10)

tk.Label(root, text="Case Number:").pack(anchor="w", padx=10, pady=(10, 0))
case_number_entry = tk.Entry(root, width=20)
case_number_entry.pack(padx=10)

tk.Label(root, text="Year:").pack(anchor="w", padx=10, pady=(10, 0))
year_var = tk.StringVar()
year_list = [str(y) for y in range(2025, 1950, -1)]
year_dropdown = ttk.Combobox(root, textvariable=year_var, values=year_list, width=10)
year_dropdown.current(0)
year_dropdown.pack(padx=10)

submit_btn = tk.Button(root, text="Fetch Case Details", command=on_submit, bg="#0275d8", fg="white")
submit_btn.pack(pady=15)

output_text = tk.Text(root, wrap="word", height=20, width=95)
output_text.pack(padx=10, pady=10)

# --- Start GUI ---
root.mainloop()
