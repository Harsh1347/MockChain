import os
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class InterviewDataScraper:
    def __init__(self):
        pass

    def setup_selenium_driver(self):
        """Setup Selenium WebDriver with appropriate options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        ua = UserAgent()
        chrome_options.add_argument(f'user-agent={ua.random}')
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def scrape_linkedin(self, company_name):
        """Scrape LinkedIn for interview information."""
        try:
            driver = self.setup_selenium_driver()
            search_url = f"https://www.linkedin.com/search/results/content/?keywords={company_name}%20interview%20process"
            
            driver.get(search_url)
            time.sleep(5)  # Wait for dynamic content to load
            
            # Extract relevant information
            posts = driver.find_elements(By.CSS_SELECTOR, ".feed-shared-update-v2")
            results = []
            
            for post in posts[:5]:  # Limit to 5 posts
                try:
                    content = post.find_element(By.CSS_SELECTOR, ".feed-shared-text").text
                    results.append({
                        "content": content,
                        "source": "LinkedIn"
                    })
                except:
                    continue
            
            driver.quit()
            return results
        except Exception as e:
            return f"Error scraping LinkedIn: {str(e)}"

    def scrape_glassdoor(self, company_name):
        """Scrape Glassdoor for interview reviews."""
        try:
            driver = self.setup_selenium_driver()
            search_url = f"https://www.glassdoor.com/Interview/{company_name}-interview-questions-SRCH_KE0,{len(company_name)}.htm"
            
            driver.get(search_url)
            time.sleep(5)
            
            reviews = driver.find_elements(By.CSS_SELECTOR, ".interviewReview")
            results = []
            
            for review in reviews[:5]:
                try:
                    content = review.find_element(By.CSS_SELECTOR, ".interviewDetails").text
                    results.append({
                        "content": content,
                        "source": "Glassdoor"
                    })
                except:
                    continue
            
            driver.quit()
            return results
        except Exception as e:
            return f"Error scraping Glassdoor: {str(e)}"

    def scrape_leetcode(self, company_name):
        """Scrape LeetCode for company-specific problems."""
        try:
            driver = self.setup_selenium_driver()
            search_url = f"https://leetcode.com/company/{company_name}/"
            
            driver.get(search_url)
            time.sleep(5)
            
            problems = driver.find_elements(By.CSS_SELECTOR, ".company-tag-wrapper")
            results = []
            
            for problem in problems[:5]:
                try:
                    title = problem.find_element(By.CSS_SELECTOR, ".title").text
                    difficulty = problem.find_element(By.CSS_SELECTOR, ".difficulty").text
                    results.append({
                        "title": title,
                        "difficulty": difficulty,
                        "source": "LeetCode"
                    })
                except:
                    continue
            
            driver.quit()
            return results
        except Exception as e:
            return f"Error scraping LeetCode: {str(e)}"

    def scrape_indeed(self, company_name):
        """Scrape Indeed for interview reviews."""
        try:
            driver = self.setup_selenium_driver()
            search_url = f"https://www.indeed.com/cmp/{company_name}/interviews"
            
            driver.get(search_url)
            time.sleep(5)
            
            reviews = driver.find_elements(By.CSS_SELECTOR, ".interview-review")
            results = []
            
            for review in reviews[:5]:
                try:
                    content = review.find_element(By.CSS_SELECTOR, ".interview-details").text
                    results.append({
                        "content": content,
                        "source": "Indeed"
                    })
                except:
                    continue
            
            driver.quit()
            return results
        except Exception as e:
            return f"Error scraping Indeed: {str(e)}"

    def aggregate_company_info(self, company_name):
        """Aggregate information from multiple sources."""
        try:
            linkedin_data = self.scrape_linkedin(company_name)
            glassdoor_data = self.scrape_glassdoor(company_name)
            leetcode_data = self.scrape_leetcode(company_name)
            indeed_data = self.scrape_indeed(company_name)
            
            aggregated_data = {
                "linkedin": linkedin_data,
                "glassdoor": glassdoor_data,
                "leetcode": leetcode_data,
                "indeed": indeed_data,
                "timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(aggregated_data, indent=2)
        except Exception as e:
            return f"Error aggregating data: {str(e)}"

    def save_to_file(self, data, filename):
        """Save aggregated data to a JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            return f"Error saving to file: {str(e)}"

    def load_from_file(self, filename):
        """Load aggregated data from a JSON file."""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            return f"Error loading from file: {str(e)}"

# Example usage
if __name__ == "__main__":
    scraper = InterviewDataScraper()
    company_name = "Google"  # Example company
    data = scraper.aggregate_company_info(company_name)
    print(data) 