from papers import *
# PaperExt for ads paper

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# Webdriver use chrome
exec_path = r"/usr/local/bin/chromedriver"

def ads_get_ref_cit(url, nap=5.):
    """Get the reference list or citation list from ADS."""
    wait_for_response = 10. #sec
    try:
        t0 = time.time()
        options = Options()
        options.add_argument(f'user-agent='+random.choice(user_agent_list))
        driver = webdriver.Chrome(chrome_options=options, executable_path=r"/usr/local/bin/chromedriver")
        #driver = webdriver.Chrome(executable_path=r"/usr/local/bin/chromedriver")
        driver.get(url)
        element = WebDriverWait(driver, 50).until(
            EC.presence_of_element_located((By.CLASS_NAME, 's-results-title'))
            )
        #el_per_page = driver.find_element_by_id("per-page-select")
        #el_per_page_500 = el_per_page.find_element_by_xpath("//select[@name='per-page-select']/option[text()='500']")
        #el_per_page_500.click()
        ## Wait for respond
        #time.sleep(wait_for_response)
        source_code = driver.page_source
        soup = BeautifulSoup(source_code)

        bibcode_list_sp = soup.findAll("a", {"aria-label":"bibcode"})
        # Maximum is 500
        page_loop = False
        if (len(bibcode_list_sp) >= 25):
            #print("Warning: this page has at least 500 papers, which means the list could be larger than that.")
            page_loop = True

        print("The number of current page is ", len(bibcode_list_sp))

        paper_list = []
        count = 0
        for bb in bibcode_list_sp:
            tt = time.time()
            paper1 = PaperExt(ads_id=bb.get_text().strip(), nap=pl_nap(tt-t0, nap))
            paper_list.append(paper1)
            print(count, paper1.title)
            count += 1

        count_page = 0
        while(page_loop):
            count_page += 1
            print("Page read ", count_page)
            np_button = driver.find_element(By.XPATH, "//li/a[@class='page-control next-page']")
            try:
                np_button.click()
            except WebDriverException:
                break
            time.sleep(wait_for_response)
            source_code = driver.page_source
            soup = BeautifulSoup(source_code)
            bibcode_list_sp = soup.findAll("a", {"aria-label":"bibcode"})
            print("The number of current page is ", len(bibcode_list_sp))
            for bb in bibcode_list_sp:
                tt = time.time()
                paper1 = PaperExt(ads_id=bb.get_text().strip(), nap=pl_nap(tt-t0, nap))
                paper_list.append(paper1)
                print(count, paper1.title)
                count += 1
            if (count_page>40):
                print("Warning: Pages exceed 40. Break.")
                break
    except:
        raise
    finally:
        driver.quit()

    print("Sleep...")
    time.sleep(random.random()*nap)
    print("Awake...")
    return ListPapers(paper_list)

def pl_nap(time, nap_min):
    """power law nap time"""
    if(time<nap_min):
        return nap_min
    a = 2.
    b = 0.5
    nap_max = 3600 #1 hour
    return (a*time**b)%nap_max

class PaperExt(Paper):
    """Extend Paper class to ADS"""
    def __init__(self, ads_id=None, arxiv_id=None, url="https://ui.adsabs.harvard.edu/abs/", nap=5.):
        super().__init__(arxiv_id=arxiv_id, url=url, nap=nap)
        if((ads_id is None) and (arxiv_id is None)):
            self.ads_id = ""
            self.reference_url = ""
            self.citation_url = ""
        elif(arxiv_id is None):
            self.ads_id = ads_id
            self.link_ads = url+ads_id
            (self.reference_url, self.citation_url) = self.get_ref_cit_url(ads_id)
            self._find_ads_page(ads_id, self.link_ads)
            #print(self.arxiv_id)
        else:
            # arxiv_id provided
            self.get_ads_id()
            (self.reference_url, self.citation_url) = self.get_ref_cit_url(self.ads_id)
        pass

    def get_ads_id(self):
        """Get the ads bibcode as an id. And get something from ads page by the way."""
        (self.title, self.authors, self.abstract, self.date, self.std_keywords, \
            self.doi, self.arxiv_id, self.ads_pdf_url, self.ads_id) = \
            self._read_ads_page("",self.ads_link)

    def get_ref_cit_url(self, ads_id):
        """Return the link to refernce and citation page of an ads_id"""
        return (self._url_prefix+ads_id.strip()+"/references", self._url_prefix+ads_id.strip()+"/citations")

        #https://ui.adsabs.harvard.edu/abs/2010ApJ...714..320A/references

    def _find_ads_page(self, ads_id, url):
        """Find a page on ads"""
        (self.title, self.authors, self.abstract, self.date, self.std_keywords, \
            self.doi, self.arxiv_id, self.ads_pdf_url, _) = \
            self._read_ads_page(ads_id, self.link_ads, nap=self.nap_interval)
        return

    @staticmethod
    def _read_ads_page(ads_id, url, nap=5.):
        """Read from an ADS abstract page."""
        header = {'User-Agent':random.choice(user_agent_list)}
        try:
            source_code = requests.get(url, headers=header)
            source_code.raise_for_status()
        except HTTPError as e:
            print(e)
            return ("", [], "", "", [], "", "", "", "")
        plain_text = source_code.text
        soup = BeautifulSoup(plain_text)

        try:
            title = soup.find("meta", {"property":"og:title"}).get("content").strip()
        except:
            title = ""
            print("Warning: no title for %s" % url)
        author_list = []
        try:
            for ss in soup.findAll("meta", {"property":"article:author"}):
                author_list.append(ss.get("content").strip())
        except:
            pass
        ads_link = url
        try:
            abstract = soup.find("meta", {"property":"og:description"}).get("content").strip()
        except:
            abstract = ""
        try:
            date = soup.find("meta", {"property":"article:published_time"}).get("content").strip()
        except:
            date = ""
        comments = ""
        try:
            std_key_words_list = list(ss.get("content").strip() for ss in \
                                  soup.findAll("meta", {"name":"citation_keywords"}))
        except:
            std_key_words_list = ""
        try:
            doi = soup.find("meta", {"name":"citation_doi"}).get("content").strip()
        except:
            doi = ""
        try:
            ads_pdf_url = soup.find("meta", {"name":"citation_pdf_url"})
        except:
            ads_pdf_url = ""
        arxiv_id_sp = soup.find("a", text=re.compile("arXiv*"))
        try:
            arxiv_id = arxiv_id_sp.get_text().strip()
        except AttributeError as e:
            if(arxiv_id_sp is None):
                arxiv_id = ""
            else:
                raise e
        try:
            bibcode_sp = soup.find("i", {"title":"The bibcode is assigned by the ADS as a unique identifier for the paper."})
        except:
            print("Warning: Bibcode not found for %s" % url)
        try:
            ads_id = bibcode_sp.find_previous_sibling("a").get_text().strip()
        except:
            pass
        #print(ads_id)
        time.sleep(random.random()*nap)
        return (title, author_list, abstract, date, std_key_words_list, doi, arxiv_id, ads_pdf_url, ads_id)

    def access_arxiv(self, change_prefix=False, use_date="ads"):
        """Should the name be clear?"""
        # change the url_prefix to arxiv one
        url_pref = self._url_prefix
        date = self.date
        self._url_prefix = "https://arxiv.org/abs/"
        self.search_online()
        if(use_date=="ads"):
            self.date = date
        if (change_prefix):
            return
        else:
            self._url_prefix = url_pref
            return

    def get_ref_cit(self, target="reference"):
        """Return a ListPaper of the reference or citation."""
        if (target=="reference"):
            list_url = self.reference_url
        elif (target=="citation"):
            list_url = self.citation_url
        return self.ads_list_reading(list_url, deep=False)

    @staticmethod
    def ads_list_reading(url, deep=False):
        """Read from a list page on ADS"""
        pass

# Extend list
class ListPapersExt(ListPapers):
    pass
