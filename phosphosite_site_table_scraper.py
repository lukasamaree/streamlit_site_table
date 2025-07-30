from playwright.async_api import async_playwright
import pandas as pd
import time
import os
import json
import re
from datetime import datetime
import random
import sys
import traceback
import cloudscraper
import asyncio

# Configuration
CONFIG = {
    'headless': True,  # Run in headless mode for better performance
    'start_protein_id': 583,  # Starting protein ID
    'end_protein_id': 583,  # Ending protein ID
    'max_retries': 3,  # Maximum number of retries per protein
    'notification_email': 'lukasamaree@gmail.com',  # Set this to your email to receive notifications
    'smtp_server': 'smtp.gmail.com',  # Your SMTP server
    'smtp_port': 587,  # SMTP port
    'smtp_username': "lukasamaree@gmail.com",  # Your SMTP username
    'smtp_password': "jvzz npkj fhqx umtu",  # Your SMTP password
}

def get_last_processed_id(output_dir):
    """Get the last successfully processed protein ID"""
    try:
        files = [f for f in os.listdir(output_dir) if f.startswith('protein_') and f.endswith('_site_data.csv')]
        if not files:
            return None
        ids = [int(f.split('_')[1]) for f in files]
        return max(ids)
    except Exception:
        return None

def get_random_delay():
    """Return a random delay between 1 and 3 seconds"""
    return random.uniform(1, 3)

async def handle_cloudflare_challenge(page):
    """Handle Cloudflare challenge if encountered"""
    try:
        # Check for Cloudflare challenge
        if await page.query_selector("iframe[src*='challenges.cloudflare.com']"):
            print("[DEBUG] Detected Cloudflare challenge, attempting to solve...")
            
            # Create a cloudscraper session
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'darwin',
                    'mobile': False
                },
                delay=10
            )
            
            # Get the current URL
            current_url = page.url
            
            # Try to get the page using cloudscraper
            print("[DEBUG] Using cloudscraper to bypass challenge...")
            response = scraper.get(current_url)
            
            if response.status_code == 200:
                print("[DEBUG] Successfully bypassed Cloudflare")
                # Extract cookies from cloudscraper session
                cookies = scraper.cookies.get_dict()
                
                # Add cookies to playwright context
                for name, value in cookies.items():
                    await page.context.add_cookies([{
                        'name': name,
                        'value': value,
                        'url': current_url
                    }])
                
                # Reload the page with the new cookies
                await page.reload()
                await page.wait_for_load_state('networkidle', timeout=30000)
                return True
            else:
                print(f"[DEBUG] Cloudscraper failed with status code: {response.status_code}")
                
        return False
            
    except Exception as e:
        print(f"[ERROR] Failed to handle Cloudflare challenge: {str(e)}")
        traceback.print_exc()
    return False

async def add_random_behavior(page):
    """Add random human-like behavior"""
    try:
        # Random mouse movements
        for _ in range(random.randint(2, 5)):
            await page.mouse.move(
                random.randint(0, 800),
                random.randint(0, 600)
            )
            await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Random scrolling
        await page.mouse.wheel(0, random.randint(100, 500))
        await asyncio.sleep(random.uniform(0.5, 1.5))
        await page.mouse.wheel(0, random.randint(-200, -100))
        
        # Random viewport changes
        await page.set_viewport_size({
            'width': random.randint(1050, 1920),
            'height': random.randint(800, 1080)
        })
        
        # Simulate random key presses (tab, arrow keys)
        for _ in range(random.randint(1, 3)):
            await page.keyboard.press('Tab')
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
    except Exception as e:
        print(f"[WARNING] Error in random behavior: {str(e)}")

async def load_cookies(context, cookie_file='cookies.json'):
    """Load cookies from file if exists"""
    try:
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
                print(f"[DEBUG] Loaded {len(cookies)} cookies")
    except Exception as e:
        print(f"[WARNING] Error loading cookies: {str(e)}")

async def save_cookies(context, cookie_file='cookies.json'):
    """Save cookies to file"""
    try:
        cookies = await context.cookies()
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f)
            print(f"[DEBUG] Saved {len(cookies)} cookies")
    except Exception as e:
        print(f"[WARNING] Error saving cookies: {str(e)}")

async def scrape_phosphosite_site_table(protein_id, protein_name, page, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Navigate to the protein page
            url = f"https://www.phosphosite.org/proteinAction.action?id={protein_id}&showAllSites=true"
            await page.goto(url)
            
            # Extract protein name from breadcrumb
            breadcrumb = await page.query_selector("#titleMainHeader")
            if breadcrumb:
                breadcrumb_text = await breadcrumb.inner_text()
                # Try to extract the last part after '> Protein >'
                match = re.search(r">\s*Protein\s*>\s*([A-Za-z0-9_\-]+)", breadcrumb_text)
                if match:
                    protein_name = match.group(1).strip()
                    print(f"[DEBUG] Extracted protein name from breadcrumb: {protein_name}")
            # Check for Cloudflare
            if await handle_cloudflare_challenge(page):
                await asyncio.sleep(random.uniform(5, 8))
            await add_random_behavior(page)
            if protein_id == 556:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Protein ID 556 detected - waiting 30 seconds...")
                await asyncio.sleep(30)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 30-second wait completed for protein ID 556")
            await page.wait_for_load_state('domcontentloaded')
            no_record = await page.query_selector("p.noRecordFoundText")
            if no_record and "No Protein Record found !!" in await no_record.inner_text():
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Protein ID {protein_id}: No protein record found in database")
                return None
            print(f"[DEBUG] Protein exists!")
            print("[DEBUG] Waiting 2 seconds before looking for Protein Information tab...")
            await asyncio.sleep(2)
            print("[DEBUG] Looking for Protein Information tab...")
            info_tab = await page.query_selector("xpath=//*[@id='tabs1']/ul/li[1]/a")
            if info_tab:
                print("[DEBUG] Found Protein Information tab, clicking...")
                await info_tab.click()
                print("[DEBUG] Clicked Protein Information tab")
                await asyncio.sleep(3)
                print("[DEBUG] Waited for tab content to load")
                print("[DEBUG] Now looking for protein name after tab click...")
                element = await page.query_selector("xpath=/html/body/table/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/span")
                if element:
                    protein_name = await element.inner_text()
                    protein_name = protein_name.strip()
                    print(f"[DEBUG] Found protein name using XPath: {protein_name}")
                    print("[DEBUG] Looking for Chromosomal Location...")
                    chrom_loc_element = await page.query_selector("xpath=/html/body/table/tbody/tr[1]/td[1]/table/tbody/tr[3]/td/span")
                    organism = None
                    if chrom_loc_element:
                        chrom_loc_text = await chrom_loc_element.inner_text()
                        chrom_loc_text = chrom_loc_text.strip()
                        print(f"[DEBUG] Found Chromosomal Location text: {chrom_loc_text}")
                        words = chrom_loc_text.split()
                        if len(words) >= 4:
                            organism = words[3]
                            print(f"[DEBUG] Extracted organism: {organism}")
                    print("[DEBUG] Navigating to site table page...")
                    site_table_url = f"https://www.phosphosite.org/proteinAction.action?id={protein_id}&showAllSites=true"
                    await page.goto(site_table_url)
                    print(f"[DEBUG] Navigated to: {site_table_url}")
                    await page.wait_for_load_state('domcontentloaded')
                    await asyncio.sleep(2)
                    print("[DEBUG] Looking for Site Table tab...")
                    site_table_tab = None
                    selectors = [
                        "xpath=//a[contains(text(), 'Site Table')]",
                        "xpath=//a[contains(@href, 'siteTable')]",
                        "xpath=/html/body/div[4]/div[5]/ul/li[2]/a",
                        "xpath=//*[@id='tabs1']/ul/li[2]/a",
                        "css=a[href*='siteTable']",
                        "css=a:has-text('Site Table')"
                    ]
                    for selector in selectors:
                        try:
                            site_table_tab = await page.query_selector(selector)
                            if site_table_tab:
                                print(f"[DEBUG] Found Site Table tab using selector: {selector}")
                                break
                        except Exception as e:
                            print(f"[DEBUG] Selector {selector} failed: {str(e)}")
                            continue
                    if not site_table_tab:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Protein ID {protein_id}: No Site Table tab found")
                        return None
                    print("[DEBUG] Clicking Site Table tab...")
                    await site_table_tab.click()
                    await asyncio.sleep(3)
                else:
                    print("[DEBUG] XPath not found, trying CSS selector...")
                    try:
                        await page.wait_for_selector("span.bold01", timeout=5000)
                        element = await page.query_selector("span.bold01")
                        if element:
                            actual_protein_name = await element.inner_text()
                            actual_protein_name = actual_protein_name.strip()
                            print(f"[DEBUG] Found protein name using CSS selector: {actual_protein_name}")
                            protein_name = actual_protein_name
                            print("[DEBUG] Looking for Chromosomal Location...")
                            chrom_loc_element = await page.query_selector("span.bold01")
                            organism = None
                            if chrom_loc_element:
                                chrom_loc_text = await chrom_loc_element.inner_text()
                                chrom_loc_text = chrom_loc_text.strip()
                                print(f"[DEBUG] Found Chromosomal Location text: {chrom_loc_text}")
                                words = chrom_loc_text.split()
                                if len(words) >= 4:
                                    organism = words[3]
                                    print(f"[DEBUG] Extracted organism: {organism}")
                            print("[DEBUG] Navigating to site table page...")
                            site_table_url = f"https://www.phosphosite.org/proteinAction.action?id={protein_id}&showAllSites=true"
                            await page.goto(site_table_url)
                            print(f"[DEBUG] Navigated to: {site_table_url}")
                            await page.wait_for_load_state('domcontentloaded')
                            await asyncio.sleep(2)
                            print("[DEBUG] Looking for Site Table tab...")
                            site_table_tab = None
                            selectors = [
                                "xpath=//a[contains(text(), 'Site Table')]",
                                "xpath=//a[contains(@href, 'siteTable')]",
                                "xpath=/html/body/div[4]/div[5]/ul/li[2]/a",
                                "xpath=//*[@id='tabs1']/ul/li[2]/a",
                                "css=a[href*='siteTable']",
                                "css=a:has-text('Site Table')"
                            ]
                            for selector in selectors:
                                try:
                                    site_table_tab = await page.query_selector(selector)
                                    if site_table_tab:
                                        print(f"[DEBUG] Found Site Table tab using selector: {selector}")
                                        break
                                except Exception as e:
                                    print(f"[DEBUG] Selector {selector} failed: {str(e)}")
                                    continue
                            if not site_table_tab:
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] Protein ID {protein_id}: No Site Table tab found")
                                return None
                            print("[DEBUG] Clicking Site Table tab...")
                            await site_table_tab.click()
                            await asyncio.sleep(3)
                        else:
                            print("[ERROR] Could not find protein name using CSS selector")
                            return None
                    except Exception as e:
                        print(f"[ERROR] Error finding protein name with CSS selector: {str(e)}")
                        return None
            else:
                print("[ERROR] Could not find Protein Information tab")
                return None
            print("[DEBUG] Looking for site table...")
            table = None
            table_selectors = [
                "#siteTable_human",                # Most specific and reliable
                "table.siteTableNew",              # By class
                "table[style*='padding-left:20px']",
                "table.table",
                "table[class*='table']",
                "xpath=//table[contains(@class, 'table')]",
                "xpath=//table[contains(@style, 'padding')]",
                "xpath=//div[contains(@class, 'table')]//table"
            ]
            for selector in table_selectors:
                try:
                    table = await page.wait_for_selector(selector, timeout=10000)
                    if table:
                        print(f"[DEBUG] Found table using selector: {selector}")
                        break
                except Exception as e:
                    print(f"[DEBUG] Table selector {selector} failed: {str(e)}")
                    continue
            if not table:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Protein ID {protein_id}: No site table found")
                return None
            # Extract data from the site table
            data = []
            rows = await table.query_selector_all("tr")
            print(f"[DEBUG] Found {len(rows)} rows in table")
            for i, row in enumerate(rows[1:], 1):
                try:
                    cells = await row.query_selector_all("td")
                    if len(cells) < 6:
                        continue
                    site = await cells[0].inner_text()
                    sequence = await cells[1].inner_text()
                    
                    # Check for upstream button in the 3rd column (index 2)
                    upstream_btn = await cells[2].query_selector("span.searchButton")
                    upstream = False
                    if upstream_btn:
                        upstream_text = await upstream_btn.inner_text()
                        if "upstream" in upstream_text.lower():
                            upstream = True
                            print(f"[DEBUG] Found upstream button for site {site.strip()}")
                    
                    # Check for downstream button in the 4th column (index 3)
                    downstream_btn = await cells[3].query_selector("span.searchButton")
                    downstream = False
                    if downstream_btn:
                        downstream_text = await downstream_btn.inner_text()
                        if "downstream" in downstream_text.lower():
                            downstream = True
                            print(f"[DEBUG] Found downstream button for site {site.strip()}")
                    
                    # LTP and HTP
                    ltp = await cells[4].inner_text()
                    htp = await cells[5].inner_text()
                    try:
                        ltp = int(ltp.strip())
                    except:
                        ltp = None
                    try:
                        htp = int(htp.strip())
                    except:
                        htp = None
                    
                    data.append({
                        "Protein": protein_name,
                        "Site": site.strip(),
                        "Sequence": sequence.strip(),
                        "Upstream": upstream,
                        "Downstream": downstream,
                        "LTP": ltp,
                        "HTP": htp,
                        "Organism": organism
                    })
                except Exception as e:
                    print(f"[DEBUG] Error processing row {i}: {str(e)}")
                    continue
            if not data:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Protein ID {protein_id}: No site data found in table")
                return None
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Protein ID {protein_id}: Successfully scraped {len(data)} site rows")
            return data
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            return None

async def scrape_upstream_downstream_data(page, protein_id):
    """Scrape upstream and downstream data separately"""
    try:
        print(f"[DEBUG] Starting upstream/downstream data scraping for protein {protein_id}")
        
        # Navigate to the site table page
        site_table_url = f"https://www.phosphosite.org/proteinAction.action?id={protein_id}&showAllSites=true"
        await page.goto(site_table_url)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)
        
        # Look for site table
        table = None
        table_selectors = [
            "#siteTable_human",
            "table.siteTableNew",
            "table[style*='padding-left:20px']",
            "table.table",
            "table[class*='table']"
        ]
        
        for selector in table_selectors:
            try:
                table = await page.wait_for_selector(selector, timeout=10000)
                if table:
                    print(f"[DEBUG] Found table using selector: {selector}")
                    break
            except Exception as e:
                print(f"[DEBUG] Table selector {selector} failed: {str(e)}")
                continue
        
        if not table:
            print(f"[ERROR] No site table found for upstream/downstream scraping")
            return None
        
        # Extract data from the site table
        data = []
        rows = await table.query_selector_all("tr")
        print(f"[DEBUG] Found {len(rows)} rows for upstream/downstream analysis")
        
        for i, row in enumerate(rows[1:], 1):  # Skip header row
            try:
                cells = await row.query_selector_all("td")
                if len(cells) < 6:
                    continue
                
                site = await cells[0].inner_text()
                sequence = await cells[1].inner_text()
                
                # Check for upstream button (span with class="searchButton")
                upstream_btn = await cells[2].query_selector("span.searchButton")
                upstream_data = None
                if upstream_btn:
                    upstream_text = await upstream_btn.inner_text()
                    if "upstream" in upstream_text.lower():
                        print(f"[DEBUG] Found upstream button for site {site.strip()}: {upstream_text}")
                        
                        # Click the upstream button to get data
                        try:
                            await upstream_btn.click()
                            await asyncio.sleep(2)
                            
                            # Look for the upstream table that appears
                            upstream_table = await page.query_selector("div[id*='upstreamTable'], table[id*='upstream']")
                            if upstream_table:
                                # Extract upstream data
                                upstream_rows = await upstream_table.query_selector_all("tr")
                                upstream_data = []
                                for up_row in upstream_rows[1:]:  # Skip header
                                    up_cells = await up_row.query_selector_all("td")
                                    if len(up_cells) >= 2:
                                        kinase = await up_cells[0].inner_text()
                                        substrate = await up_cells[1].inner_text()
                                        upstream_data.append(f"{kinase.strip()} -> {substrate.strip()}")
                                
                                # Close the upstream table (look for close button or click outside)
                                close_btn = await page.query_selector("button[onclick*='close'], .close, .cancel")
                                if close_btn:
                                    await close_btn.click()
                                else:
                                    # Click outside to close
                                    await page.click("body")
                                await asyncio.sleep(1)
                            else:
                                print(f"[DEBUG] No upstream table found for site {site.strip()}")
                        except Exception as e:
                            print(f"[DEBUG] Error clicking upstream button: {str(e)}")
                
                # Check for downstream button
                downstream_btn = await cells[3].query_selector("span.searchButton")
                downstream_data = None
                if downstream_btn:
                    downstream_text = await downstream_btn.inner_text()
                    if "downstream" in downstream_text.lower():
                        print(f"[DEBUG] Found downstream button for site {site.strip()}: {downstream_text}")
                        
                        # Click the downstream button to get data
                        try:
                            await downstream_btn.click()
                            await asyncio.sleep(2)
                            
                            # Look for the downstream table that appears
                            downstream_table = await page.query_selector("div[id*='downstreamTable'], table[id*='downstream']")
                            if downstream_table:
                                # Extract downstream data
                                downstream_rows = await downstream_table.query_selector_all("tr")
                                downstream_data = []
                                for down_row in downstream_rows[1:]:  # Skip header
                                    down_cells = await down_row.query_selector_all("td")
                                    if len(down_cells) >= 2:
                                        kinase = await down_cells[0].inner_text()
                                        substrate = await down_cells[1].inner_text()
                                        downstream_data.append(f"{kinase.strip()} -> {substrate.strip()}")
                                
                                # Close the downstream table
                                close_btn = await page.query_selector("button[onclick*='close'], .close, .cancel")
                                if close_btn:
                                    await close_btn.click()
                                else:
                                    # Click outside to close
                                    await page.click("body")
                                await asyncio.sleep(1)
                            else:
                                print(f"[DEBUG] No downstream table found for site {site.strip()}")
                        except Exception as e:
                            print(f"[DEBUG] Error clicking downstream button: {str(e)}")
                
                # LTP and HTP
                ltp = await cells[4].inner_text()
                htp = await cells[5].inner_text()
                try:
                    ltp = int(ltp.strip())
                except:
                    ltp = None
                try:
                    htp = int(htp.strip())
                except:
                    htp = None
                
                data.append({
                    "Site": site.strip(),
                    "Sequence": sequence.strip(),
                    "Upstream_Data": upstream_data,
                    "Downstream_Data": downstream_data,
                    "LTP": ltp,
                    "HTP": htp
                })
                
            except Exception as e:
                print(f"[DEBUG] Error processing row {i}: {str(e)}")
                continue
        
        if not data:
            print(f"[ERROR] No upstream/downstream data found")
            return None
        
        print(f"[DEBUG] Successfully scraped upstream/downstream data for {len(data)} sites")
        return data
        
    except Exception as e:
        print(f"[ERROR] Error in scrape_upstream_downstream_data: {str(e)}")
        traceback.print_exc()
        return None

def merge_upstream_downstream_data(main_df, upstream_downstream_data):
    """Merge upstream/downstream data with main DataFrame"""
    try:
        if upstream_downstream_data is None or not upstream_downstream_data:
            print("[DEBUG] No upstream/downstream data to merge")
            return main_df
        
        # Create DataFrame from upstream/downstream data
        upstream_df = pd.DataFrame(upstream_downstream_data)
        
        # Merge on Site column
        if 'Site' in main_df.columns and 'Site' in upstream_df.columns:
            merged_df = main_df.merge(upstream_df, on='Site', how='left')
            print(f"[DEBUG] Merged upstream/downstream data. Original: {len(main_df)} rows, Merged: {len(merged_df)} rows")
            return merged_df
        else:
            print("[DEBUG] Site column not found for merging")
            return main_df
            
    except Exception as e:
        print(f"[ERROR] Error merging upstream/downstream data: {str(e)}")
        traceback.print_exc()
        return main_df

def process_site_data(data):
    try:
        print(f"[DEBUG] Processing site data, {len(data)} rows")
        if not data:
            print(f"[ERROR] No data to process")
            return None
        df = pd.DataFrame(data)
        print(f"[DEBUG] Created DataFrame with {len(df)} rows")
        # Remove rows where Sequence contains Protein name (case-insensitive)
        mask = ~df.apply(lambda row: str(row['Protein']).lower() in str(row['Sequence']).lower(), axis=1)
        df = df[mask].reset_index(drop=True)
        
        # Remove rows that contain "Kinase, in vitro" in any text column
        text_columns = ['Site', 'Sequence', 'Protein']
        kinase_mask = ~df.apply(lambda row: any('kinase, in vitro' in str(row[col]).lower() for col in text_columns if col in df.columns), axis=1)
        df = df[kinase_mask].reset_index(drop=True)
        
        print(f"[DEBUG] DataFrame after removing Kinase, in vitro rows: {len(df)} rows")
        return df
    except Exception as e:
        print(f"[ERROR] Error in process_site_data: {str(e)}")
        traceback.print_exc()
        return None

def load_proxies(proxy_file='proxies.txt'):
    if not os.path.exists(proxy_file):
        return []
    with open(proxy_file, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    return proxies

async def main():
    # Create output directory if it doesn't exist
    output_dir = "sitetable_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a logs directory if it doesn't exist
    logs_dir = os.path.join(output_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create a new log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f'site_table_scraping_log_{timestamp}.txt')
    
    # Check for resume point
    start_id = CONFIG['start_protein_id']
    end_id = CONFIG['end_protein_id']
    
    # Write header to log file
    with open(log_file, 'w') as f:
        f.write(f"Site Table Scraping Log - Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Starting from Protein ID: {start_id}\n")
        f.write("=" * 80 + "\n\n")
    
    try:
        async with async_playwright() as p:
            proxies = load_proxies()
            all_results = []
            protein_name_for_file = None
            
            # Create persistent context for cookies
            browser_context = None
            
            # Iterate through protein IDs
            for protein_id in range(start_id, CONFIG['end_protein_id'] + 1):
                user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
                proxy = random.choice(proxies) if proxies else None
                
                try:
                    # Launch browser with enhanced anti-detection settings
                    browser = await p.chromium.launch(
                        headless=CONFIG['headless'],
                        args=[
                            '--disable-gpu',
                            '--no-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-features=IsolateOrigins,site-per-process',
                            '--disable-site-isolation-trials',
                            '--disable-web-security',
                            '--disable-features=IsolateOrigins',
                            '--disable-site-isolation-trials',
                            '--disable-setuid-sandbox',
                            '--disable-webgl',
                            '--disable-threaded-animation',
                            '--disable-threaded-scrolling',
                            '--disable-in-process-stack-traces',
                            '--disable-histogram-customizer',
                            '--disable-extensions',
                            '--metrics-recording-only',
                            '--no-first-run',
                            '--password-store=basic',
                            '--use-mock-keychain',
                            f'--window-size={random.randint(1050, 1920)},{random.randint(800, 1080)}',
                        ],
                        proxy={"server": proxy} if proxy else None
                    )
                    
                    # Create or reuse context
                    if not browser_context:
                        browser_context = await browser.new_context(
                            viewport={'width': random.randint(1050, 1920), 'height': random.randint(800, 1080)},
                            user_agent=user_agent,
                            locale='en-US',
                            timezone_id='America/New_York',
                            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                            permissions=['geolocation'],
                            extra_http_headers={
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                                'Accept-Language': 'en-US,en;q=0.9',
                                'Accept-Encoding': 'gzip, deflate, br',
                                'Connection': 'keep-alive',
                                'Upgrade-Insecure-Requests': '1',
                                'Sec-Fetch-Dest': 'document',
                                'Sec-Fetch-Mode': 'navigate',
                                'Sec-Fetch-Site': 'none',
                                'Sec-Fetch-User': '?1',
                                'Cache-Control': 'max-age=0',
                                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                                'sec-ch-ua-mobile': '?0',
                                'sec-ch-ua-platform': '"macOS"'
                            }
                        )
                        await load_cookies(browser_context)
                    
                    page = await browser_context.new_page()
                    
                    # Add additional page configurations
                    page.set_default_timeout(30000)
                    page.set_default_navigation_timeout(30000)
                    
                    # Add random delays and behaviors between requests
                    delay = random.uniform(3, 7)
                    print(f"[DEBUG] Adding random delay of {delay:.2f} seconds between requests")
                    await asyncio.sleep(delay)
                    
                    # Process the protein
                    protein_name = f"Protein_{protein_id}"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Protein ID {protein_id}")
                    
                    result = await scrape_phosphosite_site_table(protein_id, protein_name, page)
                    # If we successfully extracted a protein name from the breadcrumb, use it for the file
                    if result and len(result) > 0:
                        protein_name_for_file = result[0]["Protein"]
                    
                    if result is not None:
                        df = process_site_data(result)
                        if df is not None:
                            # Now scrape detailed upstream/downstream data
                            print(f"[DEBUG] Scraping detailed upstream/downstream data for protein {protein_id}")
                            upstream_downstream_data = await scrape_upstream_downstream_data(page, protein_id)
                            
                            # Merge the detailed data with main DataFrame
                            if upstream_downstream_data:
                                df = merge_upstream_downstream_data(df, upstream_downstream_data)
                            
                            all_results.append(df)
                            print(f"[DEBUG] Added DataFrame to all_results. Current count: {len(all_results)}")
                    
                    # Save cookies after successful request
                    await save_cookies(browser_context)
                    
                    # Add random behavior between requests
                    await add_random_behavior(page)
                    
                    # Write to log file
                    with open(log_file, 'a') as f:
                        status = "Success" if result is not None else "No data"
                        actual_name = protein_name_for_file if protein_name_for_file else protein_name
                        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Protein ID {protein_id} ({actual_name}): {status}\n")
                    
                except Exception as e:
                    error_msg = f"Error processing Protein ID {protein_id}: {str(e)}\n{traceback.format_exc()}"
                    print(error_msg)
                    with open(log_file, 'a') as f:
                        f.write(f"\n{error_msg}\n")
                    
                    if isinstance(e, (TimeoutError, ConnectionError)):
                        continue
                
                finally:
                    try:
                        if page:
                            await page.close()
                        if browser and browser_context != browser.contexts[0]:
                            await browser.close()
                    except Exception:
                        pass
            
            # Combine all results and save
            if all_results:
                print(f"[DEBUG] Number of results to combine: {len(all_results)}")
                print(f"[DEBUG] Types of results: {[type(r) for r in all_results]}")
                try:
                    combined_df = pd.concat(all_results, ignore_index=True)
                    print(f"[DEBUG] Combined DataFrame shape: {combined_df.shape}")
                    # Use protein name for file if available and only one protein scraped
                    if protein_name_for_file and len(all_results) == 1:
                        combined_output_path = os.path.join(output_dir, f'{protein_name_for_file}_site_data.csv')
                    else:
                        combined_output_path = os.path.join(output_dir, f'all_proteins_site_data_{start_id}_{end_id}.csv')
                    print(f"[DEBUG] Attempting to save to: {combined_output_path}")
                    combined_df.to_csv(combined_output_path, index=False)
                    print(f"[DEBUG] Successfully saved combined data to CSV")
                    completion_msg = f"\nSite Table Scraping completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    completion_msg += f"Total proteins processed: {len(all_results)}\n"
                    completion_msg += f"Combined data saved to: {combined_output_path}"
                    print(completion_msg)
                    with open(log_file, 'a') as f:
                        f.write("\n" + "=" * 80 + "\n")
                        f.write(completion_msg)
                except Exception as e:
                    print(f"[ERROR] Failed to save combined CSV: {str(e)}")
                    traceback.print_exc()
            else:
                print("[DEBUG] No results to combine into CSV - all_results is empty")
                with open(log_file, 'a') as f:
                    f.write("\n[WARNING] No results to combine into CSV - all_results is empty\n")
    except Exception as e:
        error_msg = f"Fatal error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        with open(log_file, 'a') as f:
            f.write(f"\n{error_msg}\n")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 