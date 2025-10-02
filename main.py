'''
Author: LetMeFly
Date: 2023-09-12 20:49:21
LastEditors: BS_YQY, Gemini (Updated for robust WebDriver launch)
LastEditTime: 2025-10-02 11:14:00
Description: 开源于https://github.com/LetMeFly666/YuketangAutoPlayer 欢迎issue、PR
'''
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
# 导入 Service 类以指定 ChromeDriver 路径
from selenium.webdriver.chrome.service import Service 
from typing import List
from time import sleep
import random


# ================================== 配置项 ==================================

# 您的 ChromeDriver 路径
DRIVER_PATH = r'D:\Tests\chromedriver-win64\chromedriver.exe' #替换成自己的GoogleDriver文件地址

IF_HEADLESS = False  # 是否以无窗口模式运行（首次运行建议使用有窗口模式以观察是否符合预期）
COURSE_URL = 'https://**********************'  # 替换成要刷的课的地址（获取方式见README）
COOKIE = '*********************'  # 替换成自己的打死也不要告诉别人哦（获取方式见README）

# ============================================================================


option = webdriver.ChromeOptions()

if IF_HEADLESS:
    option.add_argument('--headless')

# 使用 Service 指定 ChromeDriver 路径
try:
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=option)
except Exception as e:
    print(f"无法启动 Chrome 驱动。请检查路径是否正确，以及 ChromeDriver 版本是否与您的 Chrome 浏览器匹配。")
    print(f"错误信息: {e}")
    exit()

driver.maximize_window()
IMPLICITLY_WAIT = 10
driver.implicitly_wait(IMPLICITLY_WAIT)
IS_COMMONUI = False

def str2dic(s):
    d = dict()
    for i in s.split('; '):
        temp = i.split('=')
        d[temp[0]] = temp[1]
    return d


def setCookie(cookies):
    driver.delete_all_cookies()
    for name, value in cookies.items():
        driver.add_cookie({'name': name, 'value': value, 'path': '/'})


def ifVideo(div: WebElement):
    """判断一个元素是否是未锁定的视频单元"""
    for i in div.find_elements(By.TAG_NAME, 'i'):
        i_class = i.get_attribute('class')
        if 'icon--suo' in i_class:  # 锁的图标，表明视频未开放
            return False
    
    if IS_COMMONUI:  # www.yuketang.cn，新版ui
        try:
            span = div.find_element(By.CSS_SELECTOR, 'span.leaf-flag')
        except:
            return False
        return '视频' in span.text.strip()
    
    try:
        i = div.find_element(By.TAG_NAME, 'i')
    except:
        return False  # 每个小结后面都存在空行<li>
    i_class = i.get_attribute('class')
    return 'icon--shipin' in i_class


def getAllvideos_notFinished(allClasses: List[WebElement]):
    """获取所有未完成的视频单元"""
    driver.implicitly_wait(0.1)  # 临时缩短等待时间
    allVideos = []
    for thisClass in allClasses:
        # 仅查找视频且未包含“已完成”的单元
        if ifVideo(thisClass) and '已完成' not in thisClass.text:
            print(f'找到未完成的视频: {thisClass.text.strip()}')
            allVideos.append(thisClass)
    driver.implicitly_wait(IMPLICITLY_WAIT) # 恢复默认等待时间
    return allVideos


# 初始化
homePageURL = 'https://' + COURSE_URL.split('https://')[1].split('/')[0] + '/'
if 'www.yuketang.cn' in homePageURL:
    IS_COMMONUI = True

driver.get(homePageURL)
# 设置 Cookie 登录
setCookie({'sessionid': COOKIE})
driver.get(COURSE_URL)
sleep(3)

# 登录检查逻辑
if 'pro/portal/home' in driver.current_url:
    print('cookie失效或设置有误，请重设cookie或选择每次扫码登录')
    driver.get(homePageURL)
    driver.find_element(By.CLASS_NAME, 'login-btn').click()
    print("请扫码登录")
    while 'courselist' not in driver.current_url:  # 判断是否已经登录成功
        sleep(0.5)
    print('登录成功')
    driver.get(COURSE_URL)


def optimize_video_playback():
    """使用 JavaScript 直接设置视频播放速度和静音，提高稳定性"""
    # 1. 确保视频元素存在
    WebDriverWait(driver, 10).until(
        lambda x: driver.execute_script('return document.querySelector("video");')
    )
    
    # 2. 设置静音和 2x 速度 (更稳定)
    driver.execute_script('document.querySelector("video").muted = true;')
    driver.execute_script('document.querySelector("video").playbackRate = 2.0;')
    print("视频已设置为 2倍速 和 静音模式")
    
    # 3. 自动播放与防暂停逻辑
    driver.execute_script('video = document.querySelector("video");')
    driver.execute_script('videoPlay = setInterval(function() {if (video.paused) {video.play();}}, 200);')
    driver.execute_script('video.addEventListener("pause", () => {video.play()})')
    # 5秒后停止 setInterval，防止过度消耗资源（虽然视频暂停监听还在）
    driver.execute_script('setTimeout(() => clearInterval(videoPlay), 5000)')

    # 4. 注入完成检测标记函数
    driver.execute_script('addFinishMark = function() {finished = document.createElement("span"); finished.setAttribute("id", "LetMeFly_Finished"); document.body.appendChild(finished); console.log("Finished");}')
    
    # 5. 注入完成检测逻辑 (播放时间倒退即视为完成)
    driver.execute_script('lastDuration = 0; setInterval(() => {nowDuration = video.currentTime; if (nowDuration < lastDuration) {addFinishMark()}; lastDuration = nowDuration}, 200)')


def finish1video():
    """刷完一个视频，返回 True 表示成功刷完，False 表示没有未完成视频"""
    # 找到课程列表元素
    if IS_COMMONUI:
        # 新版 UI 需要点击到“学情报告”或类似 Tab 来暴露课程单元列表
        try:
            scoreList = driver.find_element(By.ID, 'tab-student_school_report')
            scoreList.click()
            sleep(1) # 等待列表加载
        except:
            print("未找到课程列表 Tab，尝试直接查找单元...")
        allClasses = driver.find_elements(By.CLASS_NAME, 'study-unit')
    else:
        allClasses = driver.find_elements(By.CLASS_NAME, 'leaf-detail')
        
    print('正在寻找未完成的视频，请耐心等待...')
    allVideos = getAllvideos_notFinished(allClasses)
    
    if not allVideos:
        print('✅ 所有视频已完成！')
        return False
        
    video = allVideos[0]
    
    # 滚动到视频单元并点击
    driver.execute_script('arguments[0].scrollIntoView(false);', video)
    if IS_COMMONUI:
        span = video.find_element(By.TAG_NAME, 'span')
        span.click()
    else:
        video.click()
        
    print(f'正在打开并播放: {video.text.strip()}')
    
    # 切换到新的视频播放窗口
    driver.switch_to.window(driver.window_handles[-1])
    
    # 优化视频播放和注入检测逻辑
    optimize_video_playback()
    
    print('视频开始播放，正在等待完成标记...')
    while True:
        # 检查是否已注入完成标记
        if driver.execute_script('return document.querySelector("#LetMeFly_Finished");'):
            print('✅ 视频播放完成标记出现，等待 5s 确保数据上传')
            sleep(5) 
            driver.close()
            driver.switch_to.window(driver.window_handles[-1]) # 切换回主窗口
            return True
        else:
            # 随机打印信息，表示正在运行
            print(f'正在播放视频 | 未完成 yet | 随机数: {random.random()}')
            sleep(120)


# ================================== 脚本主循环 ==================================

# 循环刷课，直到 finish1video 返回 False
while finish1video():
    driver.refresh() # 刷新主页面以获取最新的完成状态

# 退出浏览器
driver.quit()
print('🎉 恭喜你！全部视频播放完毕')
sleep(5)
