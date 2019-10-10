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
driver_exec_path = r"/usr/local/bin/chromedriver"

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
        soup = BeautifulSoup(source_code, "html.parser")

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
            soup = BeautifulSoup(source_code, "html.parser")
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
            self.bib_text = self._get_bib(self.ads_id, self.get_bib_url(self.ads_id))
            #print(self.arxiv_id)
        else:
            # arxiv_id provided
            print("From arxiv id %s to ADS bibcode ..." %self.arxiv_id)
            self.get_ads_id()
            print(self.ads_id, self.arxiv_id)
            (self.reference_url, self.citation_url) = self.get_ref_cit_url(self.ads_id)
            self.bib_text = self._get_bib(self.ads_id, self.get_bib_url(self.ads_id))

    def get_ads_id(self):
        """Get the ads bibcode as an id. And get something from ads page by the way."""
        if(self.link_ads==""):
            self.search_online()
        (self.title, self.authors, self.abstract, self.date, self.std_keywords, \
            self.doi, _ , self.ads_pdf_url, self.ads_id) = \
            self._read_ads_page("", self.link_ads, use_driver=True)

    def get_bib_url(self, ads_id):
        """Return the link for export citation."""
        return self._url_prefix+ads_id.strip()+"/exportcitation"

    def get_ref_cit_url(self, ads_id):
        """Return the link to refernce and citation page of an ads_id"""
        return (self._url_prefix+ads_id.strip()+"/references", self._url_prefix+ads_id.strip()+"/citations")

        #https://ui.adsabs.harvard.edu/abs/2010ApJ...714..320A/references

    def _get_bib(self, ads_id, url):
        """Get the export citation as bib format."""
        return self._read_bib_page(ads_id, url, nap=self.nap_interval)

    @staticmethod
    def _read_bib_page(ads_id, url, nap=5.):
        """Read the bib citation"""
        header = {'User-Agent':random.choice(user_agent_list)}
        try:
            source_code = requests.get(url, headers=header)
            source_code.raise_for_status()
        except Exception as e:
            print(e)
            return ""

        plain_text = source_code.text
        soup = BeautifulSoup(plain_text, "html.parser")
        try:
            cite_bib = soup.find("textarea", {"class":"export-textarea form-control"}).get_text().strip()
            return cite_bib
        except:
            return ""

    def _find_ads_page(self, ads_id, url):
        """Find a page on ads"""
        if (self.arxiv_id!=""):
            (self.title, self.authors, self.abstract, self.date, self.std_keywords, \
                self.doi, _, self.ads_pdf_url, _) = \
                self._read_ads_page(ads_id, self.link_ads, nap=self.nap_interval)
        else:
            (self.title, self.authors, self.abstract, self.date, self.std_keywords, \
                self.doi, self.arxiv_id, self.ads_pdf_url, _) = \
                self._read_ads_page(ads_id, self.link_ads, nap=self.nap_interval)
        return

    @staticmethod
    def _read_ads_page(ads_id, url, nap=5., use_driver=False):
        """Read from an ADS abstract page."""
        header = {'User-Agent':random.choice(user_agent_list)}
        if (use_driver):
            try:
                options = Options()
                options.add_argument(f'user-agent='+random.choice(user_agent_list))
                driver = webdriver.Chrome(chrome_options=options, executable_path=driver_exec_path)
                #driver = webdriver.Chrome(executable_path=r"/usr/local/bin/chromedriver")
                driver.get(url)
                element = WebDriverWait(driver, 50).until(
                    EC.presence_of_element_located((By.XPATH, '//meta[@name="citation_title"]'))
                    )
                plain_text = driver.page_source
            except Exception as e:
                print(e)
                return ("", [], "", "", [], "", "", "", "")
            finally:
                driver.quit()
        else:
            try:
                source_code = requests.get(url, time.sleep(nap), headers=header)
                source_code.raise_for_status()
            except Exception as e:
                print(e)
                return ("", [], "", "", [], "", "", "", "")
    #        time.sleep(random.random()*nap)
            plain_text = source_code.text
        soup = BeautifulSoup(plain_text, "html.parser")

        try:
            #title = soup.find("meta", {"property":"og:title"}).get("content").strip()
            title = soup.find("meta", {"name":"citation_title"}).get("content").strip()
        except:
            title = ""
            print("Warning: no title for %s" % url)
        author_list = []
        try:
#            for ss in soup.findAll("meta", {"property":"article:author"}):
            for ss in soup.findAll("meta", {"name":"citation_author"}):
                author_list.append(ss.get("content").strip())
        except:
            pass
        ads_link = url
        try:
#            abstract = soup.find("meta", {"property":"og:description"}).get("content").strip()
            abstract = soup.find("meta", {"name":"description"}).get("content").strip()
        except:
            abstract = ""
        try:
#            date = soup.find("meta", {"property":"article:published_time"}).get("content").strip()
            date = soup.find("meta", {"name":"citation_publication_date"}).get("content").strip()
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
            ads_pdf_url = soup.find("meta", {"name":"citation_pdf_url"}).get("content").strip()
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
            if(bibcode_sp==None):
                bibcode_sp = soup.find("i", {"data-content":"The bibcode is assigned by the ADS as a unique identifier for the paper."})
        except:
            print("Warning: Bibcode not found for %s" % url)
        try:
            ads_id = bibcode_sp.find_previous_sibling("a").get_text().strip()
        except:
            print("Warning: Bibcode not found for %s" % url)
        #print(ads_id)
        time.sleep(nap)
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

#import copy

#driver_exec_path = r"/usr/local/bin/chromedriver"

class ListPapersExt(ListPapers):
    """Extend the ListPapers to ADS fields"""
    def __init__(self, *args, **kwargs):
        if(len(args)>0):
            if(type(args[0]) is ListPapers):
                attr_dict = args[0].__dict__
                for kk in attr_dict:
                    setattr(self, kk, attr_dict[kk])
                # make all the Paper to PaperExt
            else:
                super().__init__(*args, **kwargs)
        else:
            super().__init__()
        # make sure papers are all
        for ii in range(len(self)):
            if (type(self.list_paper[ii]) is Paper):
                self.list_paper[ii] = PaperExt(arxiv_id=self.list_paper[ii].arxiv_id)

    def filter_std_key_words(self, std_kw, exclude=False):
        """Make a new ListPaperExt object with the keywords in std_kw_list.
        Or exclude them.
        std_kw:   accept list of str
                  or str
        """
        if (type(std_kw) is str):
            std_kw = [std_kw]
        if (not exclude):
            new_list = list([pp for pp in self.list_paper if self._std_kw_contain(pp, std_kw)])
        else:
            new_list = list([pp for pp in self.list_paper if not self._std_kw_contain(pp, std_kw)])
        try:
            return ListPapersExt(new_list, key_words=self.key_words, exclude_key_words=self.exclude_key_words, boost=self._boost)
        except:
            try:
                return ListPapersExt(new_list, key_words=self.key_words, boost=self._boost)
            except AttributeError:
                return ListPapersExt(new_list)
        raise

    def _std_kw_contain(self, pp, kw):
        """Return True if a paper pp contains any of kw as std_keywords."""
        # kw is a list
        for kk in kw:
            if (kk in pp.std_keywords):
                return True
        return False

    def all_std_keywords(self):
        """Show all the std key words from ADS"""
        try:
            self.std_kw_list
        except AttributeError:
            self.std_kw_list = []
        for pp in self.list_paper:
            #std_kw = [cc.strip() for cc in pp.std_keywords]
            for ss in pp.std_keywords:
                if (ss not in self.std_kw_list):
                    self.std_kw_list.append(ss)
        return self.std_kw_list

    def summary(self):
        """Change the way it summarizes."""
        super().summary()
        print("Common keywords: ")
        try:
            print(self.all_std_keywords())
        except:
            print("")

    @staticmethod
    def ext_ads_get_ref_cit(url, nap=5.):
        """Get the reference list or citation list from ADS."""
        wait_for_response = 10. #sec
        trytime = 3
        while(trytime>0):
            trytime-=1
            t0 = time.time()
            options = Options()
            options.add_argument(f'user-agent='+random.choice(user_agent_list))
            driver = webdriver.Chrome(chrome_options=options, executable_path=driver_exec_path)
            #driver = webdriver.Chrome(executable_path=r"/usr/local/bin/chromedriver")
            try:
                driver.get(url)
                element = WebDriverWait(driver, 50).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 's-results-title'))
                    )
            except Exception as e:
                print(e)
            #el_per_page = driver.find_element_by_id("per-page-select")
            #el_per_page_500 = el_per_page.find_element_by_xpath("//select[@name='per-page-select']/option[text()='500']")
            #el_per_page_500.click()
            ## Wait for respond
            #time.sleep(wait_for_response)

            source_code = driver.page_source
            soup = BeautifulSoup(source_code, "html.parser")

            bibcode_list_sp = soup.findAll("a", {"aria-label":"bibcode"})
            # Maximum is 500
            if(bibcode_list_sp==None):
                bibcode_list_sp = []
            else:
                trytime = 0
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
                soup = BeautifulSoup(source_code, "html.parser")
                bibcode_list_sp = soup.findAll("a", {"aria-label":"bibcode"})
                if(bibcode_list_sp==None):
                    bibcode_list_sp = []
                print("The number of current page is ", len(bibcode_list_sp))
                for bb in bibcode_list_sp:
                    tt = time.time()
                    paper1 = PaperExt(ads_id=bb.get_text().strip(), nap=pl_nap(tt-t0, nap))
                    paper_list.append(paper1)
                    print(count, paper1.title)
                    count += 1
                if (count_page>400):
                    print("Warning: Pages exceed 400. Citation is over 10000. I quit.")
                    break
#        except Exception as e:
#            paper_list = []
#            print(e)
#        finally:
            driver.quit()


        print("Sleep...")
        time.sleep(random.random()*nap)
        print("Awake...")
        return ListPapersExt(paper_list)

    def export_bib(self, file_name="cite.bib", change_index=False):
        """Based on PaperExt"""
        with open(file_name, "w") as f:
            f.write("%% This file is created by 'export_bib' function in ListPapersExt module.\n\n")
            for pp in self.list_paper:
                if(type(pp) is not PaperExt):
                    print("Warning: paper may not contain any citation text.")
                    continue
                if(pp.bib_text==""):
                    print("Warning: no bib information available.")
                f.write(pp.bib_text)
                f.write("\n\n")
        return

    @staticmethod
    def _change_index(*args, to_format="author+year"):
        """Index change to other format.
        Args[0] is the text, args[1] is bibcode, args[2] is authors, args[3] is year"""
        if(to_format=="arxiv"):
            pass
        else:
            pass

    def _ads_id_list(self):
        return [pp.ads_id for pp in self.list_paper]

    def _arxiv_id_list(self):
        return [pp.arxiv_id for pp in self.list_paper]

    def _ids_list(self):
        return self._ads_id_list()+self._arxiv_id_list()

    def __add__(self, other_listpaper):
        """Enable add. Exclude duplicate."""
        #new_list = #copy.deepcopy(other_listpaper.list_paper)
        new_list = [pp for pp in other_listpaper.list_paper \
                        if not self._contain_paper(pp)]
        #for pp in other_listpaper.list_paper:
        #    if ((pp.arxiv_id in self._ids_list()) or (pp.ads_id in self._ids_list())):
        return ListPapersExt(self.list_paper+list(new_list))

    def _contain_paper(self, pp):
        """Return True if this list contain a paper."""
        try:
            if(pp.ads_id in self._ads_id_list()):
                return True
        except:
            if(pp.arxiv_id in self._arxiv_id_list()):
                return True
        return False

    @staticmethod
    def dig_deep(pp, nap=5., deep=1, only=False):
        """Loop the search for referencs and citations"""
        if (type(pp) is not PaperExt):
            raise TypeError("Paper need to be PaperExt!")

        # nap should be a function
        output_lp = ListPapersExt()
        while(deep>1):
            deep -= 1
            for ppp in ListPapersExt.dig_deep(pp, nap=nap, deep=deep, only=only).list_paper:
                output_lp = output_lp + ListPapersExt.dig_deep(ppp, nap=nap, deep=deep)

        if (only=="reference"):
            return ListPapersExt.ext_ads_get_ref_cit(pp.reference_url, nap=nap)
        elif (only=="citation"):
            return ListPapersExt.ext_ads_get_ref_cit(pp.citation_url, nap=nap)
        else:
            return ListPapersExt.ext_ads_get_ref_cit(pp.reference_url, nap=nap) + \
                    ListPapersExt.ext_ads_get_ref_cit(pp.citation_url, nap=nap)

    def check_duplicate(self):
        """Check duplicate by ADS ID"""
        tmp_ads_id_list = list(self._ads_id_list())
        for pp in self.list_paper:
            if(pp.ads_id==""):
                if (pp.arxiv_id==""):
                    print("Who are you? %s.", pp.title)
                else:
                    pp.get_ads_id()
                    if((pp.ads_id!="") and (pp.ads_id in tmp_ads_id_list)):
                        self.delete(pp)
                        print("Deleting %s" % pp.ads_id)

        num_no_ads_id = sum([1 for pp in self.list_paper if pp.ads_id==""])
        print("There are %d papers without ads id." % num_no_ads_id)

    def delete(self, pp):
        """Delete a paper"""
        self.list_paper.remove(pp)
        self.tot_num = len(self.list_paper)
        self.recal_scores()
        return 1

    def recal_scores(self):
        """Calculate the scores again."""
        #self.key_words
        #self._boost
        del self.scores
        del self.tot_score
        del self.aver_length
        for kk in self.key_words:
            self.cal_key_word_scores(kk)
        for kk in self.exclude_kws:
            self.cal_key_word_scores(kk, exclude=True)
        self._update_tot_scores()
