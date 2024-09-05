#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
This code allows accessing a list of publications data from Google Scholar.
Specifically, these steps are often useful when doing literature review
(1) Search for a (seminal paper)
(2) Click on "cited by"
(3) Sort "cited by" with number of citations, year published, etc.

As output this program will plot the number of citations in the Y axis and the 
rank of the result in the X axis. It also, optionally, export the database to
a .csv file.
"""

import requests, os, datetime, argparse, warnings
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import pandas as pd
from time import sleep
import arxiv


# NAME = 'attention is all you need'
NUMRESULTS = 100
SAVEPATH = os.getcwd()
SORTBY = 'Citations'
STARTYEAR = None
now = datetime.datetime.now()
ENDYEAR = now.year

# Websession Parameters
GSCHOLAR_URL = 'https://scholar.google.com/scholar?start={}&q={}&hl=en&as_sdt=0,5'
YEAR_RANGE = '' #&as_ylo={start_year}&as_yhi={end_year}'
STARTYEAR_URL = '&as_ylo={}'
ENDYEAR_URL = '&as_yhi={}'
ROBOT_KW=['unusual traffic from your computer network', 'not a robot']

def get_element(driver, xpath, attempts=5, _count=0):
    '''Safe get_element method with multiple attempts'''
    try:
        element = driver.find_element_by_xpath(xpath)
        return element
    except Exception as e:
        if _count<attempts:
            sleep(1)
            get_element(driver, xpath, attempts=attempts, _count=_count+1)
        else:
            print("Element not found")

def get_content_with_selenium(url):
    if 'driver' not in globals():
        global driver
        driver = setup_driver()
    driver.get(url)

    # Get element from page
    el = get_element(driver, "/html/body")
    c = el.get_attribute('innerHTML')

    if any(kw in el.text for kw in ROBOT_KW):
        print("Solve captcha manually and press enter here to continue...")
        el = get_element(driver, "/html/body")
        c = el.get_attribute('innerHTML')

    return c.encode('utf-8')

def setup_driver():
    try:
        from selenium import webdriver
        from selenium.webdriver import ChromeOptions
        from selenium.common.exceptions import StaleElementReferenceException
    except Exception as e:
        print(e)
        print("Please install Selenium and chrome webdriver for manual checking of captchas")

    print('Loading driver...')
    options = ChromeOptions()
    options.add_argument("disable-infobars")
    driver = webdriver.Chrome(options=options)
    return driver

def find_cited_by_link(div):
    for a in div.find_all('a', href=True):
        if 'Cited by' in a.text:
            assert "cites" in a["href"]
            link = "https://scholar.google.com" + a["href"]
            # citations = int(a.text.split()[-1])
    return link

def handle_robot_checking(content, url):
    if any(kw in content.decode('ISO-8859-1') for kw in ROBOT_KW):
        print("Robot checking detected, handling with selenium (if installed)")
        try:
            content = get_content_with_selenium(url)
        except Exception as e:
            print("No success. The following error was raised:")
            print(e)
    return content

def do_search(args, session):
    
    final_citations = []
    authors = []
    
    url = GSCHOLAR_URL.format("0", args.name.replace(' ','+'))
    page = session.get(url)#, headers=headers)
    content = handle_robot_checking(page.content, url)

    # Create parser
    soup = BeautifulSoup(content, 'html.parser', from_encoding='utf-8')

    # Get stuff
    mydivs = soup.findAll("div", { "class" : "gs_or" })
    # "gs_a stands for authors"
    
    mydivs = soup.findAll("div", { "id" : "gs_n" })
    assert len(mydivs) == 1
    for div in mydivs:
        for a in div.find_all('a', href=True):
            if a.text == "Next":
                link = "https://scholar.google.com" + a["href"]
                break
            else:
                print("end of search, terminating")

    # If we provide the specific paper and we are looking for "cited by"
    if args.cited_by:
        # I am assuming that the first result is the one that I want
        div = mydivs[0]
        link = find_cited_by_link(div)

        page = session.get(link)#, headers=headers)
        content = handle_robot_checking(page.content, url)

        soup = BeautifulSoup(content, 'html.parser', from_encoding='utf-8')
        mydivs = soup.findAll("div", { "class" : "gs_or" })

    # Otherwise, we are looking for the number of citations under a general keyword
    for div in mydivs:
        try:
            link = div.find('h3').find('a').get('href')
        except:
            warnings.warn('LINK NOT FOUND ERROR: Look manually at for {}'.format(div))
            link = 'Look manually at: '+url

        try:
            title = div.find('h3').find('a').text
        except:
            warnings.warn("TITLE NOT FOUND ERROR: Could not catch title for {}".format(link[-1]))
            title = 'Could not catch title'

        try:
            for a in div.find_all('a', href=True):
                if 'Cited by' in a.text:
                    assert "cites" in a["href"]
                    final_citations.append(int(a.text.split()[-1]))
                    break
        except:
            warnings.warn("CITATIONS NOT FOUND ERROR: Number of citations not found for {}".format(title[-1]))
            citations = 0
                    
        try:
            # unfortunately, gs does not handle the display of authors very well
            client = arxiv.Client()
            search = arxiv.Search(query=title, max_results=100)
            results = client.results(search)
            for r in results:
                if r.title.lower() == title.lower():
                    authors.append(r.authors)
                    break  
        except:
            warnings.warn("AUTHOR NOT FOUND ERROR: Author not found for {}".format(title[-1]))
            author = "Author not found"
        

        # try:
        #     year = get_year(div.find('div',{'class' : 'gs_a'}).text)
        # except:
        #     warnings.warn("YEAR NOT FOUND ERROR: Year not found for {}".format(title[-1]))
        #     year = 0
        
        # try:
        #     publisher = div.find('div',{'class' : 'gs_a'}).text.split("-")[-1]
        # except:
        #     warnings.warn("PUBLISHER NOT FOUND ERROR: Publisher not found for {}".format(title[-1]))
        #     publisher = "Publisher not found"

        # try:
        #     venue = " ".join(div.find('div',{'class' : 'gs_a'}).text.split("-")[-2].split(",")[:-1])
        # except:
        #     warnings.warn("VENUE NOT FOUND ERROR: Venue not found for {}".format(title[-1]))
        #     venue = "Venue not fount"

        # rank.append(rank[-1]+1)
        
    return final_citations
    
def main():  
    parser = argparse.ArgumentParser()  
  
    parser.add_argument('--name', type=str, help='Name of paper', default='inverse decision modelling')
    parser.add_argument('--cited-by', type=str, help='Whether the provided name is a keyword or a paper', default=True)
  
    args = parser.parse_args()
    
    # # Option: Start year is either a number of None
    # if STARTYEAR:
    #     GSCHOLAR_MAIN_URL = GSCHOLAR_URL + STARTYEAR_URL.format(STARTYEAR)
    # else:
    #     GSCHOLAR_MAIN_URL = GSCHOLAR_URL

    # # Option: Can change end year
    # if ENDYEAR != now.year:
    #     GSCHOLAR_MAIN_URL = GSCHOLAR_MAIN_URL + ENDYEAR_URL.format(ENDYEAR)

    # if debug:
    #     GSCHOLAR_MAIN_URL='https://web.archive.org/web/20210314203256/'+GSCHOLAR_URL

    # Start new session
    session = requests.Session()
    #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    # Variables to save
    links = []
    title = []
    citations = []
    year = []
    author = []
    venue = []
    publisher = []
    rank = [0]

    final_citations = do_search(args, session)

    # Delay 
    sleep(0.5)

    # url = GSCHOLAR_MAIN_URL.format(str(n), keyword.replace(' ','+'))

    # # print("Loading next {} results".format(n+10))
    # page = session.get(url)#, headers=headers)
    # c = page.content
    # if any(kw in c.decode('ISO-8859-1') for kw in ROBOT_KW):
    #     print("Robot checking detected, handling with selenium (if installed)")
    #     try:
    #         c = get_content_with_selenium(url)
    #     except Exception as e:
    #         print("No success. The following error was raised:")
    #         print(e)

    # # Create parser
    # soup = BeautifulSoup(c, 'html.parser', from_encoding='utf-8')
    # # print(soup)

    # # Get stuff
    # mydivs = soup.findAll("div", { "class" : "gs_or" })
    # # print(mydivs)

    # for div in mydivs:
    #     print(div)
    #     try:
    #         links.append(div.find('h3').find('a').get('href'))
    #     except: # catch *all* exceptions
    #         links.append('Look manually at: '+url)

    #     try:
    #         title.append(div.find('h3').find('a').text)
    #     except:
    #         title.append('Could not catch title')

    #     try:
    #         citations.append(get_citations(str(div.format_string)))
    #     except:
    #         warnings.warn("Number of citations not found for {}. Appending 0".format(title[-1]))
    #         citations.append(0)

    #     try:
    #         year.append(get_year(div.find('div',{'class' : 'gs_a'}).text))
    #     except:
    #         warnings.warn("Year not found for {}, appending 0".format(title[-1]))
    #         year.append(0)

    #     try:
    #         author.append(get_author(div.find('div',{'class' : 'gs_a'}).text))
    #     except:
    #         author.append("Author not found")

    #     try:
    #         publisher.append(div.find('div',{'class' : 'gs_a'}).text.split("-")[-1])
    #     except:
    #         publisher.append("Publisher not found")

    #     try:
    #         venue.append(" ".join(div.find('div',{'class' : 'gs_a'}).text.split("-")[-2].split(",")[:-1]))
    #     except:
    #         venue.append("Venue not fount")

    #     rank.append(rank[-1]+1)


    
    

    # data = pd.DataFrame(list(zip(author, title, citations, year, publisher, venue, links)), index = rank[1:],
    #                     columns=['Author', 'Title', 'Citations', 'Year', 'Publisher', 'Venue', 'Source'])
    # data.index.name = 'Rank'

    # # Avoid years that are higher than the current year by clipping it to end_year
    # data['cit/year']=data['Citations']/(end_year + 1 - data['Year'].clip(upper=end_year))
    # data['cit/year']=data['cit/year'].round(0).astype(int)

    # # Sort by the selected columns, if exists
    # try:
    #     data_ranked = data.sort_values(by=sortby_column, ascending=False)
    # except Exception as e:
    #     print('Column name to be sorted not found. Sorting by the number of citations...')
    #     data_ranked = data.sort_values(by='Citations', ascending=False)
    #     print(e)

    # # Print data
    # print(data_ranked)

    # # Plot by citation number
    # if plot_results:
    #     plt.plot(rank[1:],citations,'*')
    #     plt.ylabel('Number of Citations')
    #     plt.xlabel('Rank of the keyword on Google Scholar')
    #     plt.title('Keyword: '+keyword)
    #     plt.show()

    # # Save results
    # if save_database:
    #     fpath_csv = os.path.join(path,keyword.replace(' ','_')+'.csv')
    #     fpath_csv = fpath_csv[:MAX_CSV_FNAME]
    #     data_ranked.to_csv(fpath_csv, encoding='utf-8')
    #     print('Results saved to', fpath_csv)
    
if __name__ == '__main__':  
    main()