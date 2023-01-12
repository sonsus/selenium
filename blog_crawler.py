'''
selenium >= 4.0 의 코드이므로 참조 (find_element 메서드 이름이 약간 다름)

crawl_post: 작성 완료된 프로그램은 아니나 동작은 함
crawl_post: 웹드라이버를 끄고 켜는 컨트롤에 대한 고려를 하지 않은 디자인이므로 경우에 따라 수정이 필요함
get_post_url, crawl_post: selenium을 사용하는 이유인 explicit wait을 적용하지 않았음, crawler_util.py 에 공식 도큐먼트 내용이 담겨있음
'''

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium_stealth import stealth
from time import sleep


from pathlib import Path

from fire import Fire
import pandas as pd
from tqdm import tqdm
from munch import Munch
from typing import Mapping, Sequence, Union

from ipdb import set_trace

from crawler_util import *



def strict_kw_click(keyword:str='',
                    driver:webdriver.chrome.webdriver.WebDriver=None)->None:
    raise NotImplementedError


def init_driver(
        use_stealth:bool=False,
        use_proxy:bool=False,
            ip:str='',
            port:int=8888, # for proxy
)->webdriver.chrome.webdriver.WebDriver:
    options = webdriver.ChromeOptions()
    if use_stealth: 
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
    else:
        options.add_argument("headless")
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
    
    
    if use_proxy:
        proxy = f"{ip}:{port}"
        options.add_argument(f'--proxy-server={proxy}')


    driver = webdriver.Chrome(options = options)

    if use_stealth: # https://2bmw3.tistory.com/31
        stealth(driver,
            languages=["ko-KR", "ko"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            # fix_hairline=True,
            )


    return driver


def get_post_url(
        keyword:str,
        topk:int=10,
        csvname:str='',
        root:str='results/',
        strict_kw:bool=False,
            use_stealth:bool=False,
            use_proxy:bool=False,
                ip:str='',
                port:int=8888,
)->Mapping:
    driver = init_driver(use_stealth=use_stealth, use_proxy=use_proxy, ip=ip, port=port)
    driver.get("http://www.naver.com")

    # 검색창에 '검색어' 검색
    element = driver.find_element(By.ID, 'query')
    element.send_keys(keyword)
    element.send_keys(Keys.RETURN )

    if strict_kw:
        # {keyword} 대신 {KW}를 검색했습니다. {keyword} 로 검색하기 <- 클릭
        strict_kw_click(keyword=keyword, driver=driver)

    b_view = driver.find_element(By.LINK_TEXT, 'VIEW')
    wait_n_click(b_view, driver=driver, timeout=10)
    b_blog = driver.find_element(By.LINK_TEXT, '블로그')
    wait_n_click(b_blog, driver=driver, timeout=10)
    b_opt = driver.find_element(By.LINK_TEXT, '옵션')
    wait_n_click(b_opt, driver=driver, timeout=10)
    b_3mo = driver.find_element(By.LINK_TEXT, '3개월')
    wait_n_click(b_3mo, driver=driver, timeout=10)


    article_raw = driver.find_elements(By.CSS_SELECTOR, ".api_txt_lines.total_tit")
    while len(article_raw) < topk:
        print(f"블로그 포스트 {topk}개 되도록 스크롤 중")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, timeout=10).until(condition_document_ready)
        article_raw = driver.find_elements(By.CSS_SELECTOR, ".api_txt_lines.total_tit")

    article_raw_ = article_raw[:topk]
    urls = [art.get_attribute('href') for art in article_raw_]
    titles = [art.text for art in article_raw_]
    dates_authors = driver.find_elements(By.CSS_SELECTOR, ".sp_nblog .total_sub")[:topk]
    dates = [a.text.split("\n")[0] for a in dates_authors]
    authors = [a.text.split("\n")[1] for a in dates_authors]

    data = dict(url= urls, title=titles, date=dates, author=authors, keyword=[keyword]*len(titles))


    df = pd.DataFrame(data)
    if not csvname: # default ''
        csvname = f"{root}/{keyword.replace(' ', '_')}_{topk}_naverblog.urls.csv"
    df.to_csv(csvname)
    print(f'saved to \n\t{csvname}')
    print(df)
    return pd.DataFrame(data)


def crawl_post( blog_df:pd.DataFrame,
                dbg:bool=False,
                root:str='results/',
                    use_stealth:bool=False,
                    use_proxy:bool=False,
                        ip:str='',
                        port:int=8888,
                ):
    '''
    contents including iframe extraction:
        keyword/author_id/postno.html
        keyword/author_id/postno.txt # author_id/postno == tail of blog url
    '''
    results = dict(
        urls = blog_df.url,
        titles = blog_df.title,
        authors = blog_df.author,
        dates = blog_df.date,
        keywords = blog_df.keyword,
    )
    results = Munch(results)

    driver = init_driver(use_stealth=use_stealth, use_proxy=use_proxy, ip=ip, port=port)

    for url, kw in tqdm(zip(results.urls, results.keywords), total=len(results.urls), desc='crawling over urls'):
        if dbg:
            root = 'dbg/'
            url = 'https://blog.naver.com/simonson92/222961306602' # 테스트블로그 (모든 유형을 담으려 노력)
        print(url)
        if not url.startswith('https://blog.naver.com/'):
            print("skip: 이 url은 네이버 블로그는 아닌듯 해")
            continue
        driver.get(url)

        fpref = url.replace('https://blog.naver.com/','')
        htmlf, txtf = f"{root}/{kw}/{fpref}.html", f"{root}/{kw}/{fpref}.txt"
        if not Path(htmlf).parent.is_dir():
            Path(htmlf).parent.mkdir(parents=True)

        wait_n_switch2frame('mainFrame', driver=driver, timeout=10)
        content = driver.find_element(By.CLASS_NAME, 'se-main-container')
        textonly = content.text  # 텍스트만 뽑아오기
        outerhtml = content.get_attribute('outerHTML') # frame에 해당하는 html. 로딩 완료 후에 생기는 정적인 소스
        with open(htmlf, 'w') as hf_, open(txtf, 'w') as tf_:
            hf_.write(outerhtml)
            tf_.write(textonly)
        print(f'wrote:\n\t{htmlf}\n\t{txtf}')
        if dbg:
            break






def csv_crawl(
        keyword:str,
        topk:int=10,
        csvname:str='',
        strict_kw:bool=False,
        root:str='results/',
                    use_stealth:bool=False,
                    use_proxy:bool=False,
                        ip:str='',
                        port:int=8888,
):
    if not Path(root).is_dir():
        Path(root).mkdir()
    driver = init_driver(use_stealth=use_stealth, use_proxy=use_proxy, ip=ip, port=port)
    blog_df = get_post_url(keyword=keyword,
                           topk=topk,
                           csvname=csvname,
                           strict_kw=strict_kw,
                        use_stealth=use_stealth,
                        use_proxy=use_proxy,
                        ip=ip,
                        port=port
                           )
    print(blog_df)

def post_crawl(
        root:str='results/',
        dbg:bool=False,
                    use_stealth:bool=False,
                    use_proxy:bool=False,
                        ip:str='',
                        port:int=8888,
):

    # 실질적으로는 위의 코드와 아래 코드는 분리되어야한다.
    # 아래는 url 모음 파일을 읽어서 크롤링하게 되는게 맞음

    csvs = Path(root).glob("**/*.csv")

    for csvf in csvs:
        print(f"읽는 중: {csvf}")
        blog_df = pd.read_csv(csvf)
        crawl_post(blog_df, dbg=dbg,
                        use_stealth=use_stealth,
                        use_proxy=use_proxy,
                        ip=ip,
                        port=port)




if __name__ == '__main__':
    Fire()

    '''usage
    
    python -m ipdb blog_crawler.py csv_crawl --keyword '맛집' --topk 10 --use_stealth
    python -m ipdb blog_crawler.py post_crawl --use_stealth
    '''
