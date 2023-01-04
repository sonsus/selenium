'''
아래의 패턴을 데코레이터 형식으로 훅을 걸어주던
아니면 일일히 싸주던지 해서
time.sleep() 부분 (implcit wait) 을
explicit wait 해주어야 나중에 성능 팩터링하기에 용이할 것 (으로 예상됨)

퍼포먼스를 위해서 혹은 스케일업을 위해서는 selenium-grid라는 라이브러리가 있는 듯
'''
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def condition_document_ready(driver):
    return driver.execute_script("return document.readyState==='complete';")

def wait_n_click(webelem, driver=None, timeout=10):
    WebDriverWait(driver, timeout=timeout).until(EC.element_to_be_clickable(webelem))
    webelem.click()
    print(f"clicked {webelem}")

def wait_n_switch2frame(framename:str, driver=None, timeout=10):
    WebDriverWait(driver, timeout=timeout).until(EC.frame_to_be_available_and_switch_to_it(framename))
    print(f'driver.switch_to.frame({framename})')
