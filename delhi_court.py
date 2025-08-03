import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PIL import Image
import pytesseract
import base64 # To return image as base64 for display in web app

# Set path to tesseract.exe
# IMPORTANT: Adjust this path if tesseract is installed elsewhere on your system
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def solve_captcha(driver, wait, retries=3):
    """
    Attempts to solve the CAPTCHA using Tesseract.
    Returns the solved CAPTCHA text or None if unsuccessful after retries.
    """
    captcha_img_path = "captcha.png"
    for attempt in range(retries):
        try:
            captcha_img_element = wait.until(EC.presence_of_element_located((By.XPATH, "//img[contains(@src,'captcha')]")))
            captcha_img_element.screenshot(captcha_img_path)

            captcha_text = pytesseract.image_to_string(Image.open(captcha_img_path)).strip()
            captcha_text = ''.join(filter(str.isalnum, captcha_text)) # Remove non-alphanumeric
            print(f"CAPTCHA Attempt {attempt + 1}: Solved as '{captcha_text}'")

            # Clean up the screenshot
            if os.path.exists(captcha_img_path):
                os.remove(captcha_img_path)

            if captcha_text: # Ensure captcha_text is not empty
                return captcha_text
        except Exception as e:
            print(f"Error during CAPTCHA solving attempt {attempt + 1}: {e}")
            if os.path.exists(captcha_img_path):
                os.remove(captcha_img_path)
            time.sleep(1) # Wait a bit before retrying

    return None # CAPTCHA could not be solved after retries

def scrape_case(case_type, case_number, year):
    """
    Scrapes case data from Delhi High Court.
    Returns a dictionary of parsed data and the raw HTML.
    """
    driver = None # Initialize driver to None
    try:
        url = "https://delhihighcourt.nic.in/app/get-case-type-status"
        # IMPORTANT: Adjust this path to your chromedriver.exe location
        driver_path = r"D:\chromedriver-win64\chromedriver-win64\chromedriver.exe"
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080") # Set a larger window size for headless
        options.add_argument("--log-level=3") # Suppress console logs
        options.add_experimental_option('excludeSwitches', ['enable-logging']) # Exclude logging

        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        wait = WebDriverWait(driver, 15) # Increased wait time

        # Select Case Type
        case_type_dropdown = wait.until(EC.presence_of_element_located((By.NAME, "case_type")))
        Select(case_type_dropdown).select_by_visible_text(case_type)

        # Enter Case Number
        driver.find_element(By.NAME, "case_number").send_keys(case_number)

        # Select Year
        year_dropdown = wait.until(EC.presence_of_element_located((By.NAME, "cyear")))
        Select(year_dropdown).select_by_visible_text(str(year))

        # Solve CAPTCHA and submit
        max_attempts = 5
        for attempt in range(max_attempts):
            captcha_text = solve_captcha(driver, wait)
            if not captcha_text:
                raise Exception("Failed to solve CAPTCHA after multiple attempts.")

            captcha_input = driver.find_element(By.NAME, "captchaInput")
            captcha_input.clear() # Clear previous CAPTCHA if any
            captcha_input.send_keys(captcha_text)

            submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")))
            submit_btn.click()

            time.sleep(3) # Give time for the page to process submission

            # Check if CAPTCHA was incorrect or if we've moved to the results page
            try:
                # Look for an error message or the results table
                error_message = driver.find_elements(By.XPATH, "//*[contains(text(), 'Invalid Captcha Code')]")
                if error_message:
                    print(f"Attempt {attempt + 1}: Invalid Captcha Code. Retrying...")
                    # Refresh CAPTCHA by interacting with a new element or re-loading
                    # A simple way might be to clear the input and try solving again from the current page
                    # Or, if that doesn't work, re-load the page for a new captcha.
                    # For simplicity, we assume the captcha image will refresh if input is wrong.
                    continue # Try again with a new CAPTCHA
                else:
                    # If no error and we are not on the initial form, assume success
                    if driver.current_url != url: # Check if URL has changed or content loaded
                        break # CAPTCHA was correct, proceed
                    # Also check for presence of results table directly
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table-responsive")))
                    break # CAPTCHA was correct, proceed
            except Exception as e:
                # If no error message and no results table yet, might still be loading or another issue
                print(f"Attempt {attempt + 1}: No explicit CAPTCHA error, checking for results... ({e})")
                try:
                     wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table-responsive")))
                     break # Found results, break from captcha loop
                except:
                    print("Results table not found yet, retrying CAPTCHA...")
                    # If results table not found, it implies captcha failed or no data.
                    # We might need to refresh the page to get a new captcha.
                    driver.get(url) # Reload to get new captcha
                    wait = WebDriverWait(driver, 15) # Re-initialize wait after reload
                    # Re-fill the initial form fields
                    case_type_dropdown = wait.until(EC.presence_of_element_located((By.NAME, "case_type")))
                    Select(case_type_dropdown).select_by_visible_text(case_type)
                    driver.find_element(By.NAME, "case_number").send_keys(case_number)
                    year_dropdown = wait.until(EC.presence_of_element_located((By.NAME, "cyear")))
                    Select(year_dropdown).select_by_visible_text(str(year))


        else:
            raise Exception(f"Failed to bypass CAPTCHA after {max_attempts} attempts.")


        raw_html = driver.page_source
        data = {}

        try:
            # Parties' names
            petitioner_name_elem = driver.find_element(By.ID, "pet_name")
            respondent_name_elem = driver.find_element(By.ID, "res_name")
            data['parties'] = f"{petitioner_name_elem.text.strip()} VS {respondent_name_elem.text.strip()}"
        except:
            data['parties'] = "Not Found"

        # Filing & next-hearing dates
        try:
            filing_date_elem = driver.find_element(By.XPATH, "//strong[text()='Filing Date : ']/following-sibling::span[1]")
            data['filing_date'] = filing_date_elem.text.strip()
        except:
            data['filing_date'] = "Not Found"

        try:
            next_hearing_date_elem = driver.find_element(By.XPATH, "//strong[text()='Next Date of Listing : ']/following-sibling::span[1]")
            data['next_hearing_date'] = next_hearing_date_elem.text.strip()
        except:
            data['next_hearing_date'] = "Not Found"

        # Order/judgment PDF links
        order_links = []
        try:
            # Find the 'Order/Judgment' section, usually within a table or div
            # This XPath might need adjustment based on the actual HTML structure
            order_table_rows = driver.find_elements(By.XPATH, "//table[contains(@class, 'table')]//tr")
            for row in order_table_rows:
                try:
                    # Look for links that point to PDF files
                    pdf_link_elem = row.find_element(By.XPATH, ".//a[contains(@href, '.pdf')]")
                    pdf_url = pdf_link_elem.get_attribute('href')
                    pdf_text = pdf_link_elem.text.strip()
                    if pdf_url:
                        order_links.append({"text": pdf_text, "url": pdf_url})
                except:
                    continue # No PDF link in this row

        except Exception as e:
            print(f"Error finding order links: {e}")
        finally:
            # Limit to most recent 5 for display, or all if fewer
            data['order_links'] = order_links[:5] # Example: show up to 5 recent links

        # Check for "No data found"
        if "No Case Data Found" in raw_html or "No record found" in raw_html:
            data = {"error": "No case data found for the provided details. Please check the inputs."}

        return data, raw_html

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return {"error": f"An error occurred: {str(e)}"}, ""
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    # Example usage for testing the scraper directly
    print("Testing scraper...")
    # Replace with actual data for testing
    test_case_type = "W.P.(C)"
    test_case_number = "1"
    test_year = "2024" # Use a valid year with test data

    scraped_data, raw_html_output = scrape_case(test_case_type, test_case_number, test_year)

    if "error" in scraped_data:
        print(f"Scraping Error: {scraped_data['error']}")
    else:
        print("\n--- Scraped Data ---")
        for key, value in scraped_data.items():
            if key == 'order_links':
                print(f"{key}:")
                for link in value:
                    print(f"  - {link['text']}: {link['url']}")
            else:
                print(f"{key}: {value}")
        # Optionally, save raw_html_output to a file for inspection
        # with open("raw_output.html", "w", encoding="utf-8") as f:
        #     f.write(raw_html_output)
        # print("\nRaw HTML saved to raw_output.html")