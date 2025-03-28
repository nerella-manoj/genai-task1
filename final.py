import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import pandas as pd
import re
import time

# List of the provided URLs
urls = [
    "https://www.bayer.com",
    "https://www.hyundai.com",
    "https://www.sap.com",
    "https://www.kelloggcompany.com",
    "https://www.sonymusic.com",
    "https://www.fedex.com",
    "https://www.3m.com",
    "https://www.paypal.com",
    "https://global.honda"
]
 



# ua = UserAgent()
#     options.add_argument(f"user-agent={ua.random}")  # Random User-Agent
#     options.add_argument("--ignore-certificate-errors")
#     options.add_argument("--ignore-ssl-errors")


# Function to fetch content using requests
def fetch_content(url):
    headers = {"User-Agent": "Mozilla/5.0"}
   
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None, None
 
    soup = BeautifulSoup(response.text, 'html.parser')
    #print(soup.prettify())
 
    # Extract JavaScript-based links
    js_links = re.findall(r'https?://[^\s"\'<>]+', response.text)
 
    return soup, js_links
 
# Function to clean the scraped data
def clean_data(soup):
    # Remove unwanted elements
    for script in soup(['script', 'style']):
        script.decompose()
 
    # Preserve links with their text
    for a in soup.find_all('a', href=True):
        a.insert_after(f" ({a['href']})")  # Append the link next to its text
 
    return soup.get_text(separator=' ', strip=True)
 
# Initialize Gemini API
genai.configure(api_key="", transport="rest")
 
def call_gemini_api(prompt):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text if response else ""
 
# Function to extract company details using Gemini
def extract_information_with_gemini(cleaned_text):
    pre_prompt = """
    Please extract the following information from the given text. If any information is missing, write "Not Provided" explicitly.
    1. What is the company's mission statement or core values?
    2. What products or services does the company offer?
    3. When was the company founded, and who were the founders?
    4. Where is the company's headquarters located?
    5. Who are the key executives or leadership team members?
    6. Has the company received any notable awards or recognitions?
    dont give assumptions about the company, only extract the information that is present in the text.
   
    Text: {cleaned_text}
    """
    prompt = pre_prompt.format(cleaned_text=cleaned_text)
    return call_gemini_api(prompt)
 
# Function to extract additional links like "About Us"
def extract_relevant_links(soup, js_links, base_url):
    keywords = ["leadership","about-us","company-overview","mission","team","contact-us","company","overview","our-company"] 
    links = []
 
    # Search for links in <a> tags
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if any(keyword in href for keyword in keywords):
            full_link = href if href.startswith("http") else base_url + href
            links.append(full_link)
 
    # Search for relevant links in JavaScript-extracted URLs
    for link in js_links:
        if any(keyword in link.lower() for keyword in keywords):
            links.append(link)
 
    return list(set(links))
 
# Function to get complete information, checking additional pages if needed
def get_complete_information(url):
    soup, js_links = fetch_content(url)
    if not soup:
        return "Failed to fetch content."
 
    cleaned_text = clean_data(soup)
    extracted_info = extract_information_with_gemini(cleaned_text)
 
    if "Not Provided" in extracted_info:
        additional_links = extract_relevant_links(soup, js_links, url)
        for link in additional_links:
            print(f"Scraping additional link: {link}")
            soup, _ = fetch_content(link)
            if not soup:
                continue  # Skip if fetch fails
            cleaned_text += "\n" + clean_data(soup)
            extracted_info = extract_information_with_gemini(cleaned_text)
            if "Not Provided" not in extracted_info:
                break  # Stop once we find enough info
 
    return extracted_info
 

# Save results to CSV
def save_to_csv(data, filename="final1.csv"):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
 
# def save_to_json(data, filename="final.json"):
#     df = pd.DataFrame(data)
#     df.to_json(filename, index=False)


# Main function to process URLs
def process_urls(urls):
    all_extracted_data = []
    for url in urls:
        print(f"Scraping {url}...")
        extracted_info = get_complete_information(url)
        all_extracted_data.append({"URL": url, "Extracted Info": extracted_info})
        time.sleep(2)
    save_to_csv(all_extracted_data)
    print("Extraction complete. Data saved to company_details.csv.")
 
# Run the script
process_urls(urls)