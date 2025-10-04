import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import time


# Creates a driver on the ifsc results website for dynamic web searching for Safari
driver = webdriver.Safari()

driver.get("https://ifsc.results.info")
time.sleep(3)


# Creates a list of all three dropdowns in the website
dropdowns = driver.find_elements(By.CSS_SELECTOR, "div.el-input.el-input--small.el-input--suffix")
# Second dropdown
events = dropdowns[1]
events.click()


# Dynamically selects all events from the second dropdown
all_events = WebDriverWait(driver, 5).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div ul li.el-select-dropdown__item"))
)

# Clicks on the All events subcategory
for option in all_events:
    span = option.find_element(By.TAG_NAME, "span")
    if span.text.strip() == "All events":
        option.click()
        break

# Third dropdown
disciplines = dropdowns[2]
disciplines.click()

# Dynamically selects lead from the third dropdown
all_disciplines = WebDriverWait(driver, 5).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div ul li.el-select-dropdown__item"))
)

# Clicks on the Lead subcategory
for option in all_disciplines:
    span = option.find_element(By.TAG_NAME, "span")
    if span.text.strip() == "Lead":
        option.click()
        break

years = ["2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015", "2014", "2013", "2012", "2011", "2010", "2009", "2008", "2007"]

# First dropdown
year = dropdowns[0]
year.click()

# Gathers all data for all ifsc world cup competitions from 2007 to 2025
links_dict = {}
for year in years:
    # Open dropdown fresh each loop
    # Re-fetch list of options after dropdown opens
    li_elements = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div ul li.el-select-dropdown__item"))
    )

    # Find and click the matching year
    for option in li_elements:
        span = option.find_element(By.TAG_NAME, "span")
        if span.text.strip() == year:
            driver.execute_script("arguments[0].click();", option)
            break

    # Scrapes all competitions for the year
    used = []
    comp_list = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.font-weight-bold.h5.mb-0"))
    )

    # Gathers data only on ifsc world cup competitions
    for comp in comp_list:
        try:
            comp_name = comp.text.strip()
            if comp_name not in used and ("IFSC World Cup" in comp_name or "IFSC Climbing Worldcup" in comp_name):
                used.append(comp_name)
                parent = comp.find_element(By.XPATH, "ancestor::a")
                link = parent.get_attribute("href")
                links_dict[comp_name] = link
                    
        except Exception:
            continue

# Gathers data for all athletes in every round in all ifsc world cup competitions from 2007 to 2025
qualifications = []
semis = []
finals = []

desired_rounds = {
    "Q": qualifications,
    "S": semis,
    "F": finals
}

for key, val in links_dict.items():
    comp_name_list = key.split(" ")
    comp_name = " ".join(comp_name_list[:-1]) #Comp Name
    comp_year = comp_name_list[-1] #Come year
    driver.get(val)

    # Gathers all sections in the competition 
    tab_containers = WebDriverWait(driver, 5).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.tab-container.default"))
    )

    # Finds and clicks on the Lead section
    lead_tab = None
    for container in tab_containers:
        tab_items = container.find_elements(By.CSS_SELECTOR, "div.tab-item")
        for item in tab_items:
            child_div = item.find_element(By.TAG_NAME, "div")
            if "Lead" in child_div.text:
                lead_tab = item
                break
    if lead_tab:
        driver.execute_script("arguments[0].click();", lead_tab)
    
    # Gets the mens section
    mens = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.dcat-row.d-flex.justify-content-between.align-items-center.border-bottom"))
    )
    # Gets all the rounds for the mens section
    mens_section = mens[0]
    men_rounds = mens_section.find_elements(By.CSS_SELECTOR, "a.cr-nav-button")

    start_time = time.time()
    men_finals = None
    num_rounds = len(men_rounds)

    for i in range(num_rounds):
        try:
            # Re-find all round buttons on each loop
            men_rounds = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.cr-nav-button"))
            )
            if i >= len(men_rounds):
                break  
    
            r = men_rounds[i]
            round_name = r.text.strip()
    
            # Decide which list to store in
            match_key = next((k for k in desired_rounds.keys() if k in round_name), None)
            if not match_key:
                continue
            target_list = desired_rounds[match_key]
    
            # Click the corresponding round button
            driver.execute_script("arguments[0].scrollIntoView(true);", r)
            driver.execute_script("arguments[0].click();", r)
            time.sleep(1)
    
            # Gets the table 
            table = WebDriverWait(driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "table"))
            )[0]
            participants = table.find_elements(By.CSS_SELECTOR, "tr")

            # extract each athlete from the table and get their data
            for participant in participants:
                stats = participant.find_elements(By.CSS_SELECTOR, "td")
                if len(stats) < 3:
                    continue
                rank = stats[0].text.strip()
                name = stats[1].text.strip()
                full_name = " ".join(name.split(" ")[:-3]).title()
                result = stats[2].text.strip()
                climber = {
                    "Year": comp_year,
                    "Competition": comp_name,
                    "Round": round_name,
                    "Rank": rank,
                    "Name": full_name,
                    "Result": result
                }
                target_list.append(climber)
    
        except StaleElementReferenceException:
            continue
    

# Converts the three lists into dataframes and creates a csv file for each one
qualifications_csv = pd.DataFrame(qualifications)
qualifications_csv.to_csv("IFSC_WC_Mens_Qualifications.csv", index=True)
semis_csv = pd.DataFrame(semis)
semis_csv.to_csv("IFSC_WC_Mens_Semis.csv", index=True)
finals_csv = pd.DataFrame(finals)
finals_csv.to_csv("IFSC_WC_Mens_Finals.csv", index=True)  