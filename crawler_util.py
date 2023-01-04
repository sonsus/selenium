'''
아래의 패턴을 데코레이터 형식으로 훅을 걸어주던
아니면 일일히 싸주던지 해서
time.sleep() 부분 (implcit wait) 을
explicit wait 해주어야 나중에 성능 팩터링하기에 용이할 것 (으로 예상됨)

퍼포먼스를 위해서 혹은 스케일업을 위해서는 selenium-grid라는 라이브러리가 있는 듯
'''
from selenium.webdriver.support.wait import WebDriverWait
def document_initialised(driver):
    return driver.execute_script("return initialised")
# 내부 스크립트는 js만 된다.

driver.navigate("file:///race_condition.html")
WebDriverWait(driver, timeout=10).until(document_initialised)
el = driver.find_element(By.TAG_NAME, "p")
assert el.text == "Hello from JavaScript!"