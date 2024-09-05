from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.chrome.options import Options  
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from selenium import webdriver
  
# Setup Chrome options  
chrome_options = Options()  
chrome_options.add_argument("--incognito")  # Enable incognito mode  
  
# Setup WebDriver  
webdriver_service = Service(ChromeDriverManager().install())  
driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)  
  
# Open a website  
driver.get("https://www.bilibili.com/video/BV1pRV5ezEtW/?spm_id_from=333.337.search-card.all.click")
sleep(10)
  
# Remember to close the browser after you're done  
driver.quit()