from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import requests
import time
import json
import threading
import random
import datetime
import pyperclip
from message_config import *
import sys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


broadcast_id = []               # 방송 ID
broadcast_url = []              # 방송 URL
broadcast_starttime = []        # 방송 시작시간
broadcast_fulltime = []
bool_onair = []                 # 방송시청 판단 여부, True/False
broadcast_count = 0             # 방송 개수
tabs_num = []                   # Chrome Browser 관리
bool_reward = []                # 포인트 보상여부

def copy_input(xpath, input):
    pyperclip.copy(input)
    driver.find_element_by_xpath(xpath).click()
    ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
    time.sleep(1)

# 방송 정보 업데이트
def load_broadcast_info():
    global broadcast_id
    global broadcast_url
    global broadcast_starttime
    global broadcast_fulltime
    global bool_onair
    global broadcast_count
    global bool_reward
    
    broadcast_id = []
    broadcast_url = []
    broadcast_starttime = []
    broadcast_fulltime = []
    bool_onair = []
    broadcast_count = 0
    broadcast_timestamp = 0
    
    # 오늘의 날짜, Day
    todays_date = datetime.datetime.today().strftime('%d')

    response_milestone = requests.get('https://apis.naver.com/selectiveweb/live_commerce_web/v2/broadcast/milestones')
    dict_milestone = json.loads(response_milestone.text)


    for _milestone in dict_milestone:
        if int(todays_date) == _milestone['milestone']['date']:
            broadcast_timestamp = _milestone['milestone']['timestamp']  # 해당 날짜 타임스템프
            broadcast_count = _milestone['broadcastCount']
    
    # 구버전
    #response_dailyshow = requests.get(f'https://apis.naver.com/selectiveweb/selectiveweb/v1/lives/timeline/daily?next={broadcast_timestamp}&size=100')
    # 신버전
    response_dailyshow = requests.get(f'https://apis.naver.com/selectiveweb/live_commerce_web/v1/broadcast/timeline/now?size=100&timestamp={broadcast_timestamp}')
    dict_dailyshow = json.loads(response_dailyshow.text)
    
    # 현재방송
    broadcast_id.append(dict_dailyshow['currentData']['broadcast']['id'])
    broadcast_url.append(dict_dailyshow['currentData']['broadcast']['broadcastEndUrl'])
    broadcast_starttime.append(int(dict_dailyshow['currentData']['broadcast']['expectedStartDate'][11:13] + dict_dailyshow['currentData']['broadcast']['expectedStartDate'][14:16]))
    broadcast_fulltime.append(dict_dailyshow['currentData']['broadcast']['expectedStartDate'])
    
    # 이전방송
    if not dict_dailyshow['prevData']['list'] == None:
        for _idx, _dailyshow in enumerate(dict_dailyshow['prevData']['list']):
            broadcast_id.append(_dailyshow['broadcast']['id'])
            broadcast_url.append(_dailyshow['broadcast']['broadcastEndUrl'])
            broadcast_starttime.append(_dailyshow['broadcast']['expectedStartDate'][11:13] + _dailyshow['broadcast']['expectedStartDate'][14:16])
            broadcast_fulltime.append(_dailyshow['broadcast']['expectedStartDate'])
        
    # 다음방송
    if not dict_dailyshow['nextData']['list'] == None:
        for _idx, _dailyshow in enumerate(dict_dailyshow['nextData']['list']):
            broadcast_id.append(_dailyshow['broadcast']['id'])
            broadcast_url.append(_dailyshow['broadcast']['broadcastEndUrl'])
            broadcast_starttime.append(_dailyshow['broadcast']['expectedStartDate'][11:13] + _dailyshow['broadcast']['expectedStartDate'][14:16])
            broadcast_fulltime.append(_dailyshow['broadcast']['expectedStartDate'])
        
    # 구버전
    # for _idx, _dailyshow in enumerate(dict_dailyshow['list']):
    #     broadcast_id.append(_dailyshow['broadcastId'])
    #     broadcast_url.append(_dailyshow['broadcastEndUrl'])
    #     broadcast_starttime.append(int(_dailyshow['expectedStartDate'][11:13] + _dailyshow['expectedStartDate'][14:16]))
    #     broadcast_fulltime.append(_dailyshow['expectedStartDate'])
    
    bool_onair = [False for _ in range(len(broadcast_id))]
    bool_reward = [0 for _ in range(len(broadcast_id))]
    
    broadcast_fulltime = [new_text.replace('T', ' ') for new_text in broadcast_fulltime]
    broadcast_fulltime = [datetime.datetime.strptime(new_type[0:19], '%Y-%m-%d %H:%M:%S') for new_type in broadcast_fulltime]
    
    info_nowtime = datetime.datetime.now()
    info_datetime = datetime.datetime.today().strftime(f'%Y-%m-%d')
    
    print(f"{info_nowtime.strftime(f'%H:%M:%S')} >> 방송정보 업데이트, 방송날짜: {info_datetime}, 방송갯수: {broadcast_count}")
    # print(f'방송 ID: {broadcast_id}')
    # print(f'방송 시간: {broadcast_starttime}')
    # print(f'방송 상태: {bool_onair}')


# 방송 창 띄우기
def broadcast_connection(_idx, sleep_time):
    global tabs_num
    global driver, lock
    
    try:
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        driver.set_window_position(random.randrange(1000), random.randrange(900))
        driver.set_window_size(410, 800)
        driver.get(broadcast_url[_idx])
        driver.implicitly_wait(10)
    except:
        print(f">> ERROR: {_idx}, 방송연결")
    finally:
        lock.release()
        time.sleep(sleep_time)


# 방송 창 닫기
def close_browser(_idx):
    global tabs_num
    global broadcast_starttime
    global driver, lock
    
    try:
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        driver.close()
        tabs_num.remove(_idx)
        exit_time = datetime.datetime.now().strftime(f'%H:%M:%S')
    except:
        print(f">> ERROR: {_idx}, 창닫기")
    else:
        print(f"{exit_time} >> 방송종료 ({_idx}, {broadcast_starttime[_idx]})")    
    finally:
        lock.release()


# 방송화면 새로고침
def window_refresh(_idx, sleep_time):
    global tabs_num
    global broadcast_starttime
    global driver, lock

    try:
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        driver.refresh()
    except:
        print(f">> ERROR: {_idx}, 방송화면 새로고침")
    else:
        _nowtime = datetime.datetime.now().strftime(f'%H:%M:%S')
        print(f"{_nowtime} >> 방송화면 새로고침 ({_idx}, {broadcast_starttime[_idx]})")    
    finally:
        lock.release()
        time.sleep(sleep_time)
    

# 채팅 아이콘 클릭
def comment_button_click(_idx, sleep_time):
    global tabs_num
    global driver, lock
    bool_result = True
    
    try:
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        driver.find_element_by_class_name('CommentButton_icon_3iWZs').click()
    except:
        print(f"!! ERROR - Index:{idx}, Step:{_idx}, 채팅 아이콘 클릭")
        bool_result = False
    finally:
        lock.release()
        time.sleep(sleep_time)
        return bool_result

# 채팅 입력
def input_comment(_idx, sleep_time):
    global tabs_num
    global driver, lock
    bool_result = True
    
    try:
        input_comment = list_comments[random.randrange(len(list_comments))]
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        search_box = driver.find_element_by_id('wa_textarea')
        actions = webdriver.ActionChains(driver).send_keys_to_element(search_box, input_comment).send_keys(Keys.ENTER)
        actions.perform()
    except:
        print(f"!! ERROR - Index:{idx}, Step:{_idx}, 채팅 입력")
        bool_result = False
    finally:
        lock.release()
        time.sleep(sleep_time)
        return bool_result
    
    
# 채팅 엔터
def comment_enter(_idx, sleep_time):
    global tabs_num
    global driver, lock
    bool_result = True
    
    try:
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        driver.find_element_by_xpath('//*[@id="wa_textarea"]').send_keys(Keys.ENTER)
    except:
        print(f"!! ERROR - Index:{idx}, Step:{_idx}, 엔터")
        bool_result = False
    finally:
        lock.release()
        time.sleep(sleep_time)
        return bool_result
    
    
# 해상도 변경 -> 360p
def resolution_change_360p(_idx, sleep_time):
    global tabs_num
    global driver, lock
    bool_result = True
    
    try:
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        driver.find_element_by_class_name('MoreButton_icon_1Jtca').click()
        time.sleep(0.5)
        driver.find_element_by_class_name('OptionButton_detail_3QxTh').click()
        time.sleep(0.5)
        driver.find_element_by_xpath('//*[@id="root"]/div/div/div/div/div/div/div/div[2]/div[2]/div[4]').click()
        time.sleep(0.5)
    except:
        print(f"!! ERROR - Index:{idx}, Step:{_idx}, Msg: 해상도 변경")
        bool_result = False
    finally:
        lock.release()
        time.sleep(sleep_time)
        return bool_result
    
    
# 하트 버튼 클릭
def heart_click(_idx, sleep_time):
    global tabs_num
    global driver, lock
    bool_result = True
    
    try:
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        driver.find_element_by_class_name('LikeButton_inner_1uQHd').click()
        time.sleep(0.2)
    except:
        print(f"!! ERROR - Index:{idx}, Step:{_idx}, 하트 클릭")
        bool_result = False
    finally:
        lock.release()
        time.sleep(sleep_time)
        return bool_result
            
            
# 스크롤 조절
def bar_scrolling(_idx, sleep_time):
    global tabs_num
    global driver, lock
    bool_result = True
    
    try:
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        driver.find_element_by_tag_name('body').send_keys(Keys.HOME)
        time.sleep(0.2)
        driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
        time.sleep(0.2)
        # driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
        # time.sleep(0.2)
    except:
        print(f"!! ERROR - Index:{idx}, Step:{_idx}, 화면 스크롤")
        bool_result = False
    finally:
        lock.release()
        time.sleep(sleep_time)
        return bool_result


# 메인화면 클릭
def main_page_click(_idx, sleep_time):
    global tabs_num
    global driver, lock
    bool_result = True
    
    try:
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        driver.find_element_by_xpath('/html/body').click()
    except:
        print(f"!! ERROR - Index:{idx}, Step:{_idx}, 메인화면 클릭")
        bool_result = False
    finally:
        lock.release()
        time.sleep(sleep_time)
        return bool_result
        

# 창 크기 변경
def change_window_size(_idx, offset_x, offset_y, sleep_time):
    global tabs_num
    global driver, lock
    bool_result = True
    
    try:
        lock.acquire()
        tabs = driver.window_handles
        driver.switch_to.window(tabs[tabs_num.index(_idx)])
        driver.set_window_size(offset_x, offset_y)
    except:
        print(f"!! ERROR - Index:{_idx}, 창 크기 변경")
        bool_result = False
    finally:
        lock.release()
        time.sleep(sleep_time)
        return bool_result
    
  
def comment_sequence(idx):
    
    while(1):
        bool_run = True
        
        if bool_run:
            bool_run = change_window_size(idx, 410, 800, 0.5)        # 창 크기 늘리기
        
        if bool_run:
            bool_run = main_page_click(idx, 0.5)                     # 메인화면 클릭
            
        if bool_run:
            bool_run = resolution_change_360p(idx, 1)                # 영상 프레임 360p 변경
        
        if bool_run:
            bool_run = comment_button_click(idx, 0.5)                # 채팅 아이콘 클릭
    
        if bool_run:
            bool_run = input_comment(idx, random.randrange(1,5))     # 채팅 입력 & 엔터
        
        if bool_run:
            bool_run = main_page_click(idx, 0.5)                     # 메인화면 클릭

        if bool_run:
            bool_run = main_page_click(idx, 0.5)                     # 메인화면 클릭

        if bool_run:
            bool_run = change_window_size(idx, 140, 150, 0.5)        # 창 크기 줄이기
        
        if bool_run:
            break

        if not bool_run:
            window_refresh(idx, 10)                     # 새로고침  
    
# def comment_sequence(idx):
    
#     while(1):
#         bool_run = True
        
#         if bool_run:
#             bool_run = resolution_change_360p(idx, 1)                # 영상 프레임 360p 변경
        
#         if bool_run:
#             bool_run = comment_button_click(idx, 0.5)                # 채팅 아이콘 클릭
    
#         if bool_run:
#             bool_run = input_comment(idx, random.randrange(1,5))     # 채팅 입력
        
#         if bool_run:
#             bool_run = comment_enter(idx, 0.5)                       # 엔터
        
#         if bool_run:
#             bool_run = main_page_click(idx, 0.5)                     # 메인화면 클릭
        
#         if bool_run:
#             bool_run = heart_click(idx, 0.5)                         # 하트 클릭
        
#         if bool_run:
#             bool_run = bar_scrolling(idx, 1)                         # 바 스크롤 조정
        
#         if bool_run:
#             bool_run = main_page_click(idx, 0.5)                     # 메인화면 클릭
        
#         if bool_run:
#             break

#         if not bool_run:
#             window_refresh(idx, 10)                     # 새로고침
            
            


# ==================================================================================
#                                    Thread Start
# ==================================================================================

def thread_onair(idx, start_time):
    global tabs_num
    global driver, lock
    
    tabs = driver.window_handles
    if len(tabs) == 1:
        driver.switch_to.window(tabs[0])
    driver.execute_script('window.open("/", "", "_blank");')


    
    broadcast_connection(idx, 0.5)              # 방송 연결
    main_page_click(idx, 0.5)                   # 메인화면 클릭
    change_window_size(idx, 140, 150, 0.5)      # 창 크기 줄이기
    
    time_chatting = 60 * random.randrange(8,12)   # 창 켜지고 n분 후
    time_close    = 60 * random.randrange(65, 70)   # 창 켜지고 n분 후

    while(1):
        nowtime = datetime.datetime.now()
        gap_time = (nowtime - start_time).seconds

        # 채팅 작성
        if gap_time == time_chatting:
            comment_sequence(idx)
            
        # 방송 종료           
        if gap_time > time_close:
            close_browser(idx)
            break

        time.sleep(0.4)


# ===========================================================================================================
# ===========================================================================================================
# ===========================================================================================================
# ===========================================================================================================
# ===========================================================================================================
# ===========================================================================================================
# ===========================================================================================================
# ===========================================================================================================
# ===========================================================================================================
# ===========================================================================================================
# ===========================================================================================================



# ==================================================================================
#                                   Main function
# ==================================================================================

if __name__ == "__main__":
    
    # 디버깅용 if문 switch
    bool_main_refresh = True    # 메인 브라우저 새로고침
    bool_info_refresh = True    # 방송 정보 업데이트
    bool_run_reward = True       # 리워드 방송만 실행
    bool_debug_mode = False       # True: ID/PW 강제입력
    maximum_broadcast = 10       # 최대 방송 실행 갯수
    
    # 초기 정보 세팅
    load_broadcast_info()
    random.shuffle(list_comments)
    tabs_num.append(9999)           # 크롬 브라우저 쓰레기값 입력
    update_gap_time = datetime.datetime.now()   # 방송정보 업데이트
    refresh_gap_time = datetime.datetime.now()  # 메인 브라우저 새로고침

    # 셀레니움 설정
    DRIVER_PATH = './chromedriver'
    CHROME_OPTIONS = Options()
    CHROME_OPTIONS.add_argument("--window-size=200,150")
    CHROME_OPTIONS.add_experimental_option("excludeSwitches", ["enable-logging"])
    CHROME_OPTIONS.add_argument("disable-infobars")
    CHROME_OPTIONS.add_argument("disable-gpu") 

    driver = webdriver.Chrome(executable_path=DRIVER_PATH, options=CHROME_OPTIONS)
 
 
 
    # 로그인
    argument = sys.argv
    del argument[0]
    tabs = driver.window_handles
    driver.switch_to.window(tabs[0])
    driver.get('https://nid.naver.com/nidlogin.login?mode=form&url=https%3A%2F%2Fwww.naver.com')
    if bool_debug_mode:
        copy_input('//*[@id="id"]', "id")
        copy_input('//*[@id="pw"]', "pw")
    else:
        copy_input('//*[@id="id"]', argument[0])
        copy_input('//*[@id="pw"]', argument[1])
    driver.find_element_by_xpath('//*[@id="login_keep_wrap"]/div[1]/label').click()
    time.sleep(0.5)
    driver.find_element_by_xpath('//*[@id="log.login"]/span').click()
    
    time.sleep(5)
    lock = threading.Lock()


    while(1):
        #nowtime = datetime.datetime(2022, 3, 24, 19, 59, 37, 20143)
        nowtime = datetime.datetime.now()

        # ----------------------------------------------
        #        메인 브라우저 새로고침 (간격 40분)
        # ----------------------------------------------
        if (nowtime - refresh_gap_time).seconds > 2400 and bool_main_refresh:

            lock.acquire()
            tabs = driver.window_handles
            driver.switch_to.window(tabs[0])
            driver.refresh()
            lock.release()

            refresh_gap_time = datetime.datetime.now()
            print(f"{nowtime.strftime(f'%H:%M:%S')} >> 메인 브라우저 새로고침")


        # ----------------------------------------------
        #           방송정보 업데이트 (간격 35분)
        # ----------------------------------------------
        if (nowtime - update_gap_time).seconds > 2100 and len(tabs_num) == 1 and bool_info_refresh:
            load_broadcast_info()
            update_gap_time = datetime.datetime.now()


        # -----------------------------------
        #         최대 방송 실행 갯수
        # -----------------------------------
        if maximum_broadcast < len(tabs_num):
            time.sleep(0.5)
            continue
        
        # -----------------------------------
        #            생방송 스레드
        # -----------------------------------
        for idx, _fulltime in enumerate(broadcast_fulltime):
            
            if (_fulltime - nowtime).seconds < 120 and not bool_onair[idx]:     # 2분전 실행, 실행한적 없을때               
                
                # 방송 리워드 체크
                if bool_reward[idx] == 0:
                    outerHTML = requests.get('https://view.shoppinglive.naver.com/lives/{}'.format(broadcast_id[idx]))
                    useReward = 'useReward\\":true'
                    bool_reward[idx] = outerHTML.text.find(useReward)
                    
                    if not bool_run_reward:
                        bool_reward[idx] = 1
                    
                    # 리워드 방송일때 실행
                    if bool_reward[idx] > 0:
                        bool_onair[idx] = True
                        print(f"{nowtime.strftime(f'%H:%M:%S')} >> 방송시작 ({idx}, {broadcast_id[idx]}, {broadcast_starttime[idx]})")
                        lock.acquire()
                        tabs_num.append(idx)
                        lock.release()
                        onair_thread = threading.Thread(target=thread_onair, args=(idx, nowtime))  # broadcast_starttime[idx]
                        onair_thread.start()
                        time.sleep(1)
                        break
        
        time.sleep(0.5)

# 스레드를 줄여야하나...
