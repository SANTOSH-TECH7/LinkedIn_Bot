import random
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import traceback
from datetime import datetime

# =================== CONFIG ===================
LINKEDIN_USERNAME = 'santosh88386r@gmail.com'
LINKEDIN_PASSWORD = 'sanrs@1804'
SEARCH_KEYWORD = 'ml Engineer'
NUM_PAGES = 30  # Increased to find more potential connections
MAX_REQUESTS = 100  # Limiting to 100 connections
MAX_REQUESTS_PER_PAGE = 10  # Limit requests per page to avoid detection
MESSAGE = "Hi {name}, I'm exploring opportunities and would love to connect with professionals in ML Engineering. Looking forward to learning from your insights!"
HEADLESS = False  # Set to True for headless operation, False to see the browser
DAILY_REQUEST_LIMIT = 100  # LinkedIn's recommended limit is around 80-100 per day
DEBUG_MODE = False  # Set to True to enable debug screenshots and verbose logging

# Create a debug folder if it doesn't exist
if DEBUG_MODE:
    os.makedirs("debug_screenshots", exist_ok=True)

# ========== DEBUG FUNCTIONS ==========
def take_debug_screenshot(driver, name="debug"):
    if not DEBUG_MODE:
        return
        
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debug_screenshots/debug_{name}_{timestamp}.png"
        driver.save_screenshot(filename)
        print(f"[DEBUG] Screenshot saved as {filename}")
    except Exception as e:
        print(f"[DEBUG] Failed to take screenshot: {e}")

def print_debug(message):
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

# ========== GOOGLE SHEETS SETUP ==========
def setup_gsheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open("LinkedIn_Connections_Log").sheet1
        return sheet
    except Exception as e:
        print(f"[!] Google Sheets setup error: {e}")
        print("[!] Continuing without logging to Google Sheets...")
        return None

def log_to_sheet(sheet, name, profile_url, status="Pending", notes=""):
    if sheet:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([timestamp, name, profile_url, status, notes])
            print(f"[✓] Logged {status} connection with {name} to Google Sheet")
        except Exception as e:
            print(f"[!] Failed to log to sheet: {e}")

# ============ SELENIUM SETUP ============
def setup_driver():
    options = Options()
    
    if not HEADLESS:
        options.add_argument("--start-maximized")
    else:
        options.add_argument("--headless=new")  # Updated headless mode syntax
        options.add_argument("--window-size=1920,1080")
    
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    
    # Disable logging
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--log-level=3")
    
    # Handle common Selenium issues
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Add user agent to appear more like a real browser
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"[!] Driver setup error: {e}")
        print("[*] Try installing webdriver-manager: pip install webdriver-manager")
        exit(1)

# ============ LOGIN TO LINKEDIN ============
def login(driver):
    try:
        driver.get("https://www.linkedin.com/login")
        sleep(random.uniform(2, 4))
        
        # Check if we're already logged in
        if "feed" in driver.current_url:
            print("[✓] Already logged in!")
            return
        
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_field.send_keys(LINKEDIN_USERNAME)
        
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(LINKEDIN_PASSWORD)
        
        # Add a small delay like a human would
        sleep(random.uniform(0.5, 1.5))
        
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Wait for login to complete
        WebDriverWait(driver, 15).until(
            lambda driver: "feed" in driver.current_url or "checkpoint" in driver.current_url
        )
        
        # Check if login was successful
        if "feed" in driver.current_url or "checkpoint" in driver.current_url:
            print("[✓] Login successful!")
            
            # Handle security check if it appears
            if "checkpoint" in driver.current_url:
                print("[!] Security checkpoint detected. Please solve it manually within 30 seconds...")
                sleep(30)
                
            # Add a longer wait after login to ensure full page load
            print("[*] Waiting for page to fully load...")
            sleep(5)
        else:
            print("[!] Login might have failed. Current URL:", driver.current_url)
            take_debug_screenshot(driver, "login_failed")
            
    except Exception as e:
        print(f"[!] Login error: {e}")
        traceback.print_exc()
        take_debug_screenshot(driver, "login_error")
        exit(1)

# ========== SEARCH PROFILES ==========
def search_profiles(driver):
    try:
        # Use different search URLs to maximize results
        search_urls = [
            f"https://www.linkedin.com/search/results/people/?keywords={SEARCH_KEYWORD}&origin=GLOBAL_SEARCH_HEADER",
            f"https://www.linkedin.com/search/results/people/?keywords={SEARCH_KEYWORD}%20hiring&origin=GLOBAL_SEARCH_HEADER",
            f"https://www.linkedin.com/search/results/people/?keywords={SEARCH_KEYWORD}%20recruiter&origin=GLOBAL_SEARCH_HEADER",
            f"https://www.linkedin.com/search/results/people/?keywords={SEARCH_KEYWORD}%20talent&origin=GLOBAL_SEARCH_HEADER",
            f"https://www.linkedin.com/search/results/people/?keywords={SEARCH_KEYWORD}%20open%20to%20work&origin=GLOBAL_SEARCH_HEADER"
        ]
        
        # Start with the first search URL
        driver.get(search_urls[0])
        sleep(random.uniform(4, 6))
        print(f"[✓] Searching for '{SEARCH_KEYWORD}' profiles...")
        take_debug_screenshot(driver, "search_page")
        
        return search_urls
        
    except Exception as e:
        print(f"[!] Search error: {e}")
        traceback.print_exc()
        take_debug_screenshot(driver, "search_error")
        return [f"https://www.linkedin.com/search/results/people/?keywords={SEARCH_KEYWORD}&origin=GLOBAL_SEARCH_HEADER"]

# ========== IMPROVED PROFILE ELEMENTS IDENTIFICATION ========== 
def get_profile_elements(driver):
    """Try multiple selector patterns to find profile elements"""
    # First make sure we're on a search results page
    if not any(x in driver.current_url for x in ['/search/results/people', '/search/results/']):
        print_debug("Not on a search results page, cannot find profiles")
        return []
    
    # More specific and accurate selectors for LinkedIn profiles
    selectors = [
        "//ul[contains(@class, 'reusable-search__entity-result-list')]/li[contains(@class, 'reusable-search__result-container')]",
        "//li[contains(@class, 'reusable-search__result-container') and .//span[contains(@class, 'entity-result__title-text')]]",
        "//li[contains(@class, 'entity-result') and not(contains(@class, 'artdeco-pagination'))]",
        "//div[contains(@class, 'search-results-container')]//li[not(contains(@class, 'artdeco-pagination__indicator'))]",
        # Fall back to general list items in the main content area
        "//main//div[contains(@class, 'search-results-container')]//li"
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                # Filter out pagination elements and anything that looks like it's not a profile
                valid_elements = []
                for el in elements:
                    try:
                        # Check if this is a pagination element
                        is_pagination = False
                        
                        # Check for pagination classes
                        class_attr = el.get_attribute("class") or ""
                        if any(x in class_attr.lower() for x in ["pagination", "page", "pager"]):
                            is_pagination = True
                        
                        # Check for profile-like content
                        has_profile_content = False
                        try:
                            # Look for name elements or connection buttons
                            if (el.find_elements(By.XPATH, ".//span[contains(@class, 'entity-result__title-text')]") or
                                el.find_elements(By.XPATH, ".//button[contains(., 'Connect')]") or
                                el.find_elements(By.XPATH, ".//a[contains(@href, '/in/')]")):
                                has_profile_content = True
                        except:
                            pass
                        
                        if not is_pagination and has_profile_content:
                            valid_elements.append(el)
                    except:
                        # If we can't determine, include it by default
                        valid_elements.append(el)
                
                if valid_elements:
                    print_debug(f"Found {len(valid_elements)} valid profiles using selector: {selector}")
                    return valid_elements
        except Exception as e:
            print_debug(f"Selector {selector} failed: {e}")
    
    # Last resort: try to find individual profile cards
    try:
        print_debug("Trying last resort selectors for profiles")
        # Look for elements with profile links
        elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/in/')]")
        if elements:
            # Try to get the parent li elements
            parent_elements = []
            for el in elements:
                try:
                    # Go up max 5 levels to find container
                    current = el
                    for _ in range(5):
                        try:
                            current = current.find_element(By.XPATH, "..")
                            if current.tag_name.lower() == 'li':
                                parent_elements.append(current)
                                break
                        except:
                            continue
                except:
                    continue
            
            if parent_elements:
                print_debug(f"Found {len(parent_elements)} profiles using link-based approach")
                return list(set(parent_elements))  # Remove duplicates
    except:
        pass
        
    # If all selectors fail, take screenshot and return empty list
    print("[!] Failed to find any profile elements with known selectors")
    take_debug_screenshot(driver, "no_profiles_found")
    
    # Try to print some part of the page structure
    try:
        print_debug("Page structure excerpt:")
        body = driver.find_element(By.TAG_NAME, "body")
        print_debug(body.get_attribute("innerHTML")[:500] + "...")
    except:
        pass
        
    return []

# ========== IMPROVED CONNECT BUTTON IDENTIFICATION ==========
def find_connect_button(driver, person):
    """Find the connect button using multiple strategies"""
    connect_button = None
    
    try:
        # Make sure the element is in view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", person)
        sleep(random.uniform(0.5, 1.0))
        
        # Take screenshot of the profile we're analyzing
        if DEBUG_MODE:
            try:
                driver.execute_script("arguments[0].style.border='2px solid red'", person)
                sleep(0.5)
                take_debug_screenshot(driver, f"profile_element_analysis")
                driver.execute_script("arguments[0].style.border=''", person)
            except:
                pass
        
        # 1. First try specific connect button selectors
        connect_button_selectors = [
            ".//button[contains(., 'Connect')]",
            ".//button[contains(@aria-label, 'Invite')]",
            ".//button[contains(@aria-label, 'Connect')]",
            ".//span[text()='Connect']/parent::button",
            ".//span[contains(text(), 'Connect')]/ancestor::button",
            ".//div[contains(@class, 'entity-result__actions')]/button",
            ".//div[contains(@class, 'search-result__actions')]/button",
            ".//div[contains(@class, 'pvs-profile-actions')]/button"
        ]
        
        for selector in connect_button_selectors:
            try:
                buttons = person.find_elements(By.XPATH, selector)
                if buttons:
                    for btn in buttons:
                        try:
                            if btn.is_displayed() and btn.is_enabled():
                                btn_text = btn.text.strip().lower()
                                print_debug(f"Found potential connect button with text: '{btn_text}'")
                                
                                # Skip "Message" or "Follow" buttons
                                if btn_text and ("message" in btn_text or "follow" in btn_text):
                                    continue
                                    
                                return btn
                        except:
                            continue
            except Exception as e:
                print_debug(f"Error with selector {selector}: {e}")
                continue
        
        # 2. Try finding any button in the action area
        action_area_selectors = [
            ".//div[contains(@class, 'entity-result__actions')]",
            ".//div[contains(@class, 'search-result__actions')]",
            ".//div[contains(@class, 'pvs-profile-actions')]",
            ".//div[contains(@class, 'artdeco-card__actions')]"
        ]
        
        for selector in action_area_selectors:
            try:
                action_areas = person.find_elements(By.XPATH, selector)
                for action_area in action_areas:
                    buttons = action_area.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        try:
                            btn_text = btn.text.strip().lower()
                            if btn.is_displayed() and btn.is_enabled():
                                print_debug(f"Found button in action area: '{btn_text}'")
                                
                                # Skip obvious non-connect buttons
                                if btn_text and ("message" in btn_text or "follow" in btn_text or 
                                                "more" in btn_text or "..." in btn_text):
                                    continue
                                    
                                # Prefer buttons that have "connect" in the text
                                if not btn_text or "connect" in btn_text:
                                    return btn
                        except:
                            continue
            except:
                continue
        
        # 3. Try to find elements with "Connect" text and navigate to parent button
        try:
            connect_texts = person.find_elements(By.XPATH, ".//*[contains(text(), 'Connect') or contains(text(), 'connect')]")
            for text_el in connect_texts:
                try:
                    # Try moving up the DOM to find parent button
                    current = text_el
                    for _ in range(5):  # Try up to 5 levels up
                        try:
                            parent = current.find_element(By.XPATH, "..")
                            if parent.tag_name.lower() == 'button':
                                if parent.is_displayed() and parent.is_enabled():
                                    return parent
                            current = parent
                        except:
                            break
                except:
                    continue
        except:
            pass
        
        # 4. Last resort: find all buttons and look for connect-like ones
        try:
            all_buttons = person.find_elements(By.TAG_NAME, "button")
            for btn in all_buttons:
                try:
                    if not btn.is_displayed() or not btn.is_enabled():
                        continue
                        
                    btn_text = btn.text.strip().lower()
                    
                    # Skip obvious non-connect buttons
                    if btn_text and ("message" in btn_text or "follow" in btn_text or 
                                    "more" in btn_text or "..." in btn_text):
                        continue
                    
                    # Get button aria-label if available
                    aria_label = btn.get_attribute("aria-label") or ""
                    
                    # If it has connect-like text or aria-label, use it
                    if ("connect" in btn_text or "invite" in btn_text or 
                        "connect" in aria_label.lower() or "invite" in aria_label.lower()):
                        return btn
                except:
                    continue
        except:
            pass
        
    except Exception as e:
        print_debug(f"Error finding connect button: {e}")
    
    return None

# ========== HANDLE CONNECTION DIALOG ==========
def handle_connection_dialog(driver, name):
    """Handle the connection dialog after clicking connect button"""
    try:
        # Wait for connection dialog to appear
        dialog = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
        )
        print_debug("Connection dialog appeared")
        
        # Try to find the "Add a note" button
        try:
            add_note_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(., 'Add a note') or contains(@aria-label, 'Add a note')]"))
            )
            add_note_button.click()
            print_debug("Clicked 'Add a note' button")
            sleep(random.uniform(1, 1.5))
            
            # Find and fill the message textarea
            try:
                message_box = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//textarea[@name='message' or contains(@id, 'custom-message')]"))
                )
                
                # Clear any existing text
                message_box.clear()
                
                # Prepare personalized message
                first_name = name.split(' ')[0] if ' ' in name else name
                personalized_message = MESSAGE.format(name=first_name)
                
                # Type message character by character like a human
                for char in personalized_message:
                    message_box.send_keys(char)
                    sleep(random.uniform(0.01, 0.03))
                    
                print_debug("Added personalized note")
                sleep(random.uniform(1, 2))
            except TimeoutException:
                print_debug("Could not find message textarea")
        except TimeoutException:
            print_debug("No 'Add a note' button found, will send without note")
        
        # Find and click the Send/Connect/Done button
        send_button_selectors = [
            "//button[contains(., 'Send') or contains(@aria-label, 'Send')]",
            "//button[contains(., 'Connect') and @type='submit']",
            "//button[contains(., 'Done')]",
            "//button[@type='submit']"
        ]
        
        for selector in send_button_selectors:
            try:
                send_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                send_button.click()
                print_debug(f"Clicked send button using selector: {selector}")
                sleep(random.uniform(1, 2))
                return True
            except:
                continue
        
        # If we got here, we didn't find a send button
        print_debug("Could not find send/connect button in dialog")
        
        # Try to close the dialog to continue
        try:
            close_button = driver.find_element(By.XPATH, "//button[@aria-label='Dismiss' or @aria-label='Close']")
            close_button.click()
            sleep(1)
            print_debug("Closed dialog using close button")
        except:
            # Try ESC key to close modal
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            sleep(1)
            print_debug("Attempted to close dialog using ESC key")
        
        return False
        
    except TimeoutException:
        print_debug("No connection dialog appeared")
        return True  # Assume it worked if no dialog appeared
    except Exception as e:
        print_debug(f"Error handling connection dialog: {e}")
        # Try to close any open dialog
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            sleep(1)
        except:
            pass
        return False

# ========== SEND CONNECTION REQUESTS ==========
def send_connection_requests(driver, search_urls, sheet, previous_sent):
    total_sent = previous_sent
    
    for url_index, search_url in enumerate(search_urls):
        if total_sent >= MAX_REQUESTS:
            print(f"[!] Reached maximum requests limit ({MAX_REQUESTS})")
            break
            
        # Navigate to search URL
        print(f"[*] Processing search URL {url_index + 1}/{len(search_urls)}")
        driver.get(search_url)
        sleep(random.uniform(3, 5))
        
        # Process multiple pages of search results
        for page in range(1, NUM_PAGES + 1):
            if total_sent >= MAX_REQUESTS:
                break
                
            print(f"[*] Processing page {page}/{NUM_PAGES}")
            requests_on_page = 0
            
            # More extensive scrolling to load all elements
            for _ in range(5):
                driver.execute_script("window.scrollBy(0, 500)")
                sleep(0.5)
            
            # Final scroll to bottom then back to top
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            sleep(1)
            driver.execute_script("window.scrollTo(0, 0)")
            sleep(2)
            
            # Take screenshot of the search results page
            take_debug_screenshot(driver, f"page_{page}_before_processing")
            
            # Print current URL for debugging
            print_debug(f"Current URL: {driver.current_url}")
            
            # Find all people elements using our specialized function
            people_elements = get_profile_elements(driver)
            
            if not people_elements:
                print(f"[!] No profiles found on page {page}, trying next page or search URL")
                
                # Try to find the next page button anyway
                try:
                    next_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next' or contains(@aria-label, 'next') or contains(., 'Next')]"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    sleep(1)
                    next_button.click()
                    print(f"[*] Navigated to page {page + 1}")
                    sleep(random.uniform(3, 5))
                    continue
                except:
                    break  # If no next button, break out of page loop
            
            print(f"[*] Found {len(people_elements)} profiles on this page")
            
            for idx, person in enumerate(people_elements):
                if total_sent >= MAX_REQUESTS or requests_on_page >= MAX_REQUESTS_PER_PAGE:
                    break
                    
                try:
                    # Scroll element into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", person)
                    sleep(random.uniform(0.5, 1.0))
                    
                    # Take screenshot of the current profile element
                    take_debug_screenshot(driver, f"profile_{idx}_on_page_{page}")
                    
                    # Get name using more reliable approaches
                    name = None
                    name_selectors = [
                        ".//span[contains(@class, 'entity-result__title-text')]//span[@aria-hidden='true']",
                        ".//span[contains(@class, 'entity-result__title-text')]",
                        ".//span[contains(@class, 'actor-name')]",
                        ".//span[contains(@class, 'name')]",
                        ".//a[contains(@class, 'app-aware-link')]//span",
                        ".//a[contains(@href, '/in/')]" # Get from profile link if all else fails
                    ]
                    
                    for selector in name_selectors:
                        try:
                            name_elements = person.find_elements(By.XPATH, selector)
                            for element in name_elements:
                                potential_name = element.text.strip()
                                if potential_name and len(potential_name) > 2:
                                    name = potential_name
                                    break
                            if name:
                                break
                        except:
                            continue
                    
                    if not name or name == "":
                        # Try to get name from link text or title attribute
                        try:
                            profile_link = person.find_element(By.XPATH, ".//a[contains(@href, '/in/')]")
                            name = profile_link.get_attribute('title') or profile_link.text
                        except:
                            pass
                    
                    if not name or name == "":
                        name = f"Profile_{idx}_Page_{page}"
                    
                    # Get profile URL
                    profile_url = "unknown_profile"
                    try:
                        profile_links = person.find_elements(By.XPATH, ".//a[contains(@href, '/in/')]")
                        for link in profile_links:
                            href = link.get_attribute('href')
                            if href and '/in/' in href:
                                profile_url = href.split('?')[0]
                                break
                    except:
                        pass
                        
                    print(f"[*] Processing profile {idx+1}: {name} ({profile_url})")
                    
                    # Find connect button using our improved function
                    connect_button = find_connect_button(driver, person)
                    
                    if connect_button:
                        print(f"[*] Found connect button for {name}")
                        
                        # Take screenshot before clicking connect
                        take_debug_screenshot(driver, f"before_click_connect_{idx}_page_{page}")
                        
                        try:
                            # Make sure it's in view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", connect_button)
                            sleep(1)
                            
                            # Try clicking with JavaScript first (more reliable)
                            driver.execute_script("arguments[0].click();", connect_button)
                        except:
                            try:
                                # If JS click fails, try regular click with ActionChains
                                actions = ActionChains(driver)
                                actions.move_to_element(connect_button).click().perform()
                            except Exception as e:
                                print(f"[!] Failed to click connect button: {e}")
                                continue
                        
                        sleep(random.uniform(2, 3))
                        
                        # Take screenshot after clicking connect
                        take_debug_screenshot(driver, f"after_click_connect_{idx}_page_{page}")
                        
                        # Handle the connection dialog
                        success = handle_connection_dialog(driver, name)
                        
                        if success:
                            # Log the connection
                            log_to_sheet(sheet, name, profile_url)
                            print(f"[✓] #{total_sent + 1}: Connection request sent to {name}")
                            
                            # Update counters
                            total_sent += 1
                            requests_on_page += 1
                            
                            # Save progress after each successful request
                            save_progress(total_sent)
                            
                            # Random delay between requests
                            sleep_time = random.uniform(5, 8)
                            print(f"[*] Waiting {sleep_time:.1f} seconds before next connection...")
                            sleep(sleep_time)
                        else:
                            print(f"[!] Failed to complete connection request for {name}")
                    else:
                        print(f"[!] No connect button found for {name}, skipping")
                
                except Exception as e:
                    print(f"[!] Error processing profile: {str(e)}")
                    traceback.print_exc()
                    continue
            
            # Check if there's a next page and navigate to it
            if page < NUM_PAGES:
                try:
                    # Try multiple patterns for next button
                    next_selectors = [
                        "//button[@aria-label='Next']",
                        "//button[contains(@aria-label, 'next')]",
                        "//button[contains(@aria-label, 'Next page')]",
                        "//li-icon[contains(@aria-label, 'Next')]/..",
                        "//span[text()='Next']/..",
                        "//span[contains(text(), 'Next')]//..",
                        "//button[contains(text(), 'Next')]"
                    ]
                    
                    next_button = None
                    for selector in next_selectors:
                        try:
                            buttons = driver.find_elements(By.XPATH, selector)
                            for btn in buttons:
                                if btn.is_displayed() and btn.is_enabled():
                                    next_button = btn
                                    print_debug(f"Found next button with selector: {selector}")
                                    break
                            if next_button:
                                break
                        except:
                            continue
                    
                    if next_button:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                        sleep(1)
                        next_button.click()
            
                        print(f"[*] Navigated to page {page + 1}")
                        sleep(random.uniform(3, 5))
                    else:
                        print("[!] No more pages (next button not found)")
                        take_debug_screenshot(driver, "no_next_button")
                        break
                except Exception as e:
                    print(f"[!] Error navigating to next page: {str(e)}")
                    traceback.print_exc()
                    take_debug_screenshot(driver, "next_page_error")
                    break
                        
            # Add a random delay between pages to avoid detection
            sleep_time = random.uniform(5, 10)
            print(f"[*] Waiting {sleep_time:.1f} seconds before next page...")
            sleep(sleep_time)
    
    return total_sent

# ========== SAVE PROGRESS ==========
def save_progress(total_sent):
    try:
        with open("linkedin_progress.txt", "w") as f:
            f.write(f"Total sent: {total_sent}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception as e:
        print(f"[!] Error saving progress: {e}")

# ========== LOAD PROGRESS ==========
def load_progress():
    return 0
    # try:
    #     if os.path.exists("linkedin_progress.txt"):
    #         with open("linkedin_progress.txt", "r") as f:
    #             lines = f.readlines()
    #             total_sent = int(lines[0].split(":")[1].strip())
    #             print(f"[*] Loaded previous progress: {total_sent} connections sent")
    #             return total_sent
    #     return 0
    # except Exception as e:
    #     print(f"[!] Error loading progress: {e}")
    #     return 0

# ========== CHECK INVITATION STATUS ==========
def check_invitation_status(driver, sheet):
    """Check the status of previously sent invitations"""
    try:
        if sheet is None:
            print("[!] No Google Sheet access, skipping invitation status check")
            return
            
        print("[*] Checking status of pending invitations...")
        
        # Navigate to sent invitations page
        driver.get("https://www.linkedin.com/mynetwork/invitation-manager/sent/")
        sleep(random.uniform(4, 6))
        
        # Take screenshot of invitations page
        take_debug_screenshot(driver, "invitations_page")
        
        # Try to get all pending invitations
        invitation_elements = driver.find_elements(By.XPATH, "//li[contains(@class, 'invitation-card')]")
        
        if not invitation_elements:
            print("[*] No pending invitations found or couldn't identify them")
            return
            
        print(f"[*] Found {len(invitation_elements)} pending invitations")
        
        # Get all sheet entries with "Pending" status to update
        try:
            all_pending = sheet.findall("Pending")
            pending_rows = [cell.row for cell in all_pending]
            print(f"[*] Found {len(pending_rows)} pending entries in sheet")
        except Exception as e:
            print(f"[!] Error finding pending entries in sheet: {e}")
            return
            
        # Process each invitation
        for idx, invitation in enumerate(invitation_elements):
            try:
                # Get profile info
                profile_name = "Unknown"
                profile_url = "Unknown"
                
                try:
                    name_element = invitation.find_element(By.XPATH, ".//span[contains(@class, 'invitation-card__name')]")
                    profile_name = name_element.text.strip()
                except:
                    pass
                    
                try:
                    link_element = invitation.find_element(By.XPATH, ".//a[contains(@href, '/in/')]")
                    profile_url = link_element.get_attribute("href").split("?")[0]
                except:
                    pass
                
                print(f"[*] Checking invitation {idx+1}: {profile_name}")
                
                # Look for withdraw button to check if still pending
                withdraw_buttons = invitation.find_elements(By.XPATH, ".//button[contains(., 'Withdraw')]")
                
                if withdraw_buttons:
                    # Still pending, nothing to update
                    print(f"[*] Invitation to {profile_name} is still pending")
                else:
                    # Check if accepted - look for "Message" button
                    message_buttons = invitation.find_elements(By.XPATH, ".//button[contains(., 'Message')]")
                    
                    if message_buttons:
                        print(f"[✓] Invitation to {profile_name} was ACCEPTED!")
                        
                        # Update in sheet if possible
                        for row in pending_rows:
                            try:
                                sheet_name = sheet.cell(row, 2).value
                                sheet_url = sheet.cell(row, 3).value
                                
                                # Match by URL or name
                                if (profile_url != "Unknown" and sheet_url == profile_url) or \
                                   (profile_name != "Unknown" and sheet_name == profile_name):
                                    sheet.update_cell(row, 4, "Accepted")
                                    sheet.update_cell(row, 5, f"Accepted on {datetime.now().strftime('%Y-%m-%d')}")
                                    print(f"[✓] Updated sheet for {profile_name}")
                                    break
                            except:
                                continue
                    else:
                        print(f"[!] Invitation to {profile_name} status unclear (possibly withdrawn)")
            except Exception as e:
                print(f"[!] Error processing invitation status: {e}")
                continue
                
    except Exception as e:
        print(f"[!] Error checking invitation status: {e}")
        traceback.print_exc()
        take_debug_screenshot(driver, "invitation_status_error")

# ========== CLEANUP OLD PENDING INVITATIONS ==========
def cleanup_old_invitations(driver, max_age_days=14):
    """Withdraw invitations that are older than the specified days"""
    try:
        print(f"[*] Cleaning up pending invitations older than {max_age_days} days...")
        
        # Navigate to sent invitations page
        driver.get("https://www.linkedin.com/mynetwork/invitation-manager/sent/")
        sleep(random.uniform(4, 6))
        
        # Scroll to load all invitations
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)
        
        # Find all invitation elements
        invitation_elements = driver.find_elements(By.XPATH, "//li[contains(@class, 'invitation-card')]")
        
        if not invitation_elements:
            print("[*] No pending invitations found or couldn't identify them")
            return
        
        print(f"[*] Found {len(invitation_elements)} pending invitations to review")
        
        # Get current date for comparison
        current_date = datetime.now()
        
        # Process each invitation
        for idx, invitation in enumerate(invitation_elements):
            try:
                # Get name for logging
                try:
                    name_element = invitation.find_element(By.XPATH, ".//span[contains(@class, 'invitation-card__name')]")
                    profile_name = name_element.text.strip()
                except:
                    profile_name = f"Unknown profile {idx}"
                
                # Try to find date element (need to adapt this to LinkedIn's format)
                date_text = None
                try:
                    date_element = invitation.find_element(By.XPATH, ".//time")
                    date_text = date_element.text.strip()
                except:
                    try:
                        # Try alternative date formats
                        date_spans = invitation.find_elements(By.XPATH, ".//span[contains(text(), 'ago') or contains(text(), 'week') or contains(text(), 'day')]")
                        for span in date_spans:
                            if any(word in span.text.lower() for word in ['day', 'week', 'month', 'ago']):
                                date_text = span.text.strip()
                                break
                    except:
                        pass
                
                # Skip if we couldn't find the date
                if not date_text:
                    print(f"[!] Could not determine invitation age for {profile_name}, skipping")
                    continue
                
                # Determine if invitation is old enough to withdraw
                should_withdraw = False
                date_lower = date_text.lower()
                
                # Parse date text
                if 'week' in date_lower or 'weeks' in date_lower:
                    try:
                        weeks = int(''.join(filter(str.isdigit, date_lower)))
                        if weeks >= (max_age_days // 7):
                            should_withdraw = True
                    except:
                        pass
                elif 'month' in date_lower or 'months' in date_lower:
                    should_withdraw = True
                elif 'day' in date_lower or 'days' in date_lower:
                    try:
                        days = int(''.join(filter(str.isdigit, date_lower)))
                        if days >= max_age_days:
                            should_withdraw = True
                    except:
                        pass
                
                # Withdraw if needed
                if should_withdraw:
                    print(f"[*] Withdrawing old invitation ({date_text}) to {profile_name}")
                    
                    try:
                        # Find and click withdraw button
                        withdraw_button = invitation.find_element(By.XPATH, ".//button[contains(., 'Withdraw')]")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", withdraw_button)
                        sleep(1)
                        withdraw_button.click()
                        sleep(1)
                        
                        # Confirm withdrawal if confirmation dialog appears
                        try:
                            confirm_button = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Withdraw') and contains(@class, 'confirm')]"))
                            )
                            confirm_button.click()
                            print(f"[✓] Successfully withdrew invitation to {profile_name}")
                            
                            # Random delay between withdrawals
                            sleep(random.uniform(2, 4))
                        except:
                            print(f"[!] No confirmation dialog appeared for {profile_name}")
                    except Exception as e:
                        print(f"[!] Error withdrawing invitation to {profile_name}: {e}")
                else:
                    print(f"[*] Keeping recent invitation ({date_text}) to {profile_name}")
            except Exception as e:
                print(f"[!] Error processing invitation element: {e}")
                continue
                
    except Exception as e:
        print(f"[!] Error cleaning up old invitations: {e}")
        traceback.print_exc()
        take_debug_screenshot(driver, "cleanup_invitations_error")

# ========== RANDOM USER ACTIVITY ==========
def perform_random_activity(driver):
    """Perform random human-like activity on LinkedIn to appear natural"""
    try:
        print("[*] Performing random activity to appear natural...")
        
        # List of activities to perform
        activities = [
            ("Visit home feed", "https://www.linkedin.com/feed/"),
            ("Check notifications", "https://www.linkedin.com/notifications/"),
            ("View own profile", "https://www.linkedin.com/in/"),
            ("Browse jobs", "https://www.linkedin.com/jobs/"),
            ("Browse my network", "https://www.linkedin.com/mynetwork/")
        ]
        
        # Select 2-3 random activities
        num_activities = random.randint(2, 3)
        selected_activities = random.sample(activities, num_activities)
        
        for activity_name, url in selected_activities:
            print(f"[*] {activity_name}...")
            driver.get(url)
            
            # Random wait time
            wait_time = random.uniform(5, 15)
            print(f"[*] Browsing for {wait_time:.1f} seconds...")
            
            # Scroll a few times
            for _ in range(random.randint(2, 5)):
                scroll_amount = random.randint(300, 700)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                sleep(random.uniform(1, 3))
            
            # Sleep for the remaining time
            sleep(wait_time)
        
        print("[✓] Random activity completed")
        
    except Exception as e:
        print(f"[!] Error during random activity: {e}")
        traceback.print_exc()

# ========== MAIN FUNCTION ==========
if __name__ == "__main__":
    driver = None
    try:
        print("[*] Starting LinkedIn Connection Bot...")
        
        # Set up initial debug info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"[*] Session started: {timestamp}")
        print(f"[*] Debug mode: {'ON' if DEBUG_MODE else 'OFF'}")
        print(f"[*] Headless mode: {'ON' if HEADLESS else 'OFF'}")
        print(f"[*] Search keyword: '{SEARCH_KEYWORD}'")
        print(f"[*] Max requests: {MAX_REQUESTS}")
        
        # Load previous progress
        previous_sent = load_progress()
        
        # Adjust MAX_REQUESTS based on previous progress
        remaining_requests = DAILY_REQUEST_LIMIT - previous_sent
        if remaining_requests <= 0:
            print("[!] Daily request limit reached. Please try again tomorrow.")
            exit(0)
        else:
            MAX_REQUESTS = min(MAX_REQUESTS, remaining_requests)
            print(f"[*] Adjusted request limit to {MAX_REQUESTS} based on previous activity")
        
        # Set up Google Sheets logging
        sheet = setup_gsheet()
        
        # Set up webdriver
        driver = setup_driver()
        
        # Login to LinkedIn
        login(driver)
        
        # Add delay after login
        sleep(random.uniform(5, 8))
        
        # First perform some random activity to appear more natural
        perform_random_activity(driver)
        
        # Check status of previous invitations
        check_invitation_status(driver, sheet)
        
        # Optionally clean up old pending invitations (uncomment to enable)
        # cleanup_old_invitations(driver, max_age_days=14)
        
        # Search for profiles
        search_urls = search_profiles(driver)
        
        # Process and send connection requests
        final_sent = send_connection_requests(driver, search_urls, sheet, previous_sent)
        
        # Update final progress
        save_progress(final_sent)
        
        # Perform a bit more random activity before closing
        perform_random_activity(driver)
        
        print(f"\n[✓] Bot completed successfully!")
        print(f"[✓] Total connection requests sent: {final_sent - previous_sent}")
        print(f"[✓] Total connections sent today: {final_sent}")
        
    except KeyboardInterrupt:
        print("\n[!] Bot stopped by user.")
    except Exception as e:
        print(f"\n[!] An unexpected error occurred: {e}")
        traceback.print_exc()
        if driver:
            take_debug_screenshot(driver, "critical_error")
    finally:
        if driver:
            print("[*] Closing browser...")
            driver.quit()
        print("[*] Bot session ended.")
