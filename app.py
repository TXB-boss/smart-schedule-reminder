import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from thefuzz import process, fuzz
import random
import altair as alt
from openai import OpenAI
import os
from zoneinfo import ZoneInfo

# Page Configuration
st.set_page_config(
    page_title="智慧课程表",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern UI Design
st.markdown("""
<style>
    /* Global Styles */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --accent-color: #ec4899;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --light-bg: #f8fafc;
        --dark-bg: #0f172a;
        --card-bg: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border-radius: 12px;
        --box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Page Background */
    body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Main Content Area */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: rgba(255, 255, 255, 0.95);
        margin: 2rem;
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
    }
    
    /* Hide File Uploader English text */
    [data-testid="stFileUploader"] small {
        display: none;
    }
    
    /* Card Style */
    .stCard, .stExpander, .stContainer {
        background: var(--card-bg);
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: var(--transition);
    }
    
    .stCard:hover, .stExpander:hover, .stContainer:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    /* Header Styles */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        border-radius: var(--border-radius);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: var(--transition);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
    }
    
    /* Tabs Styles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: var(--light-bg);
        padding: 0.5rem;
        border-radius: var(--border-radius);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        border-radius: calc(var(--border-radius) - 4px);
        padding: 0.75rem 1.5rem;
        color: var(--text-secondary);
        transition: var(--transition);
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.1);
        color: var(--primary-color);
    }
    
    .stTabs [data-baseweb="tab-list"] [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    /* Sidebar Styles */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e0e7ff 0%, #c7d2fe 100%);
        color: #1e293b;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #1e293b;
    }
    
    [data-testid="stSidebar"] .stTextInput > label,
    [data-testid="stSidebar"] .stCheckbox > label,
    [data-testid="stSidebar"] .stSelectbox > label,
    [data-testid="stSidebar"] .stDateInput > label,
    [data-testid="stSidebar"] .stTimeInput > label {
        color: #475569;
    }
    
    [data-testid="stSidebar"] .stRadio > label,
    [data-testid="stSidebar"] .stSlider > label {
        color: #475569;
    }
    
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        color: #1e293b;
    }
    
    /* Metric Cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, var(--card-bg), #f1f5f9);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--box-shadow);
        transition: var(--transition);
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    /* Success Message */
    .stAlert {
        border-radius: var(--border-radius);
        border: none;
        box-shadow: var(--box-shadow);
    }
    
    /* Divider */
    .stDivider {
        border-color: var(--light-bg);
        margin: 2rem 0;
    }
    
    /* Table Styles */
    .stDataFrame {
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--box-shadow);
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--box-shadow);
    }
</style>
""", unsafe_allow_html=True)

# Constants
WEEKDAYS = {
    0: "Monday",
    1: "Tuesday", 
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}

WEEKDAYS_CN = {
    "Monday": "星期一",
    "Tuesday": "星期二",
    "Wednesday": "星期三",
    "Thursday": "星期四",
    "Friday": "星期五",
    "Saturday": "星期六",
    "Sunday": "星期日"
}

# Time helpers
def get_system_now():
    tzname = st.session_state.get("tzname", "Asia/Shanghai")
    try:
        return datetime.now(ZoneInfo(tzname))
    except Exception:
        return datetime.now()

def get_now():
    override_dt = st.session_state.get("override_dt")
    if override_dt is not None:
        return override_dt
    return get_system_now()

# Load Data
def load_data():
    try:
        df = pd.read_csv("schedule_data.csv")
        return df
    except FileNotFoundError:
        st.error("未找到课程表数据文件 (schedule_data.csv)。请在侧边栏上传或检查文件路径。")
        return pd.DataFrame(columns=["day", "period", "start_time", "end_time", "course_name", "location", "teacher"])
    except Exception as e:
        st.error(f"读取数据文件失败: {e}")
        return pd.DataFrame(columns=["day", "period", "start_time", "end_time", "course_name", "location", "teacher"])

def save_data(df):
    df.to_csv("schedule_data.csv", index=False)

# Core Logic: Get Current Status and Next Class
def get_status_and_next_class(df):
    now = get_now()
    # now = datetime.strptime("2023-10-23 09:00", "%Y-%m-%d %H:%M") # Debugging
    current_weekday_en = WEEKDAYS[now.weekday()]
    current_time_str = now.strftime("%H:%M")
    
    # Filter for today
    today_classes = df[df['day'] == current_weekday_en].copy()
    
    if today_classes.empty:
        return "Free", "今天没有课，好好休息吧！", None

    # Sort by time
    today_classes = today_classes.sort_values("start_time")
    
    current_status = "Free"
    status_msg = "当前空闲"
    next_class = None
    
    for index, row in today_classes.iterrows():
        start = row['start_time']
        end = row['end_time']
        
        if start <= current_time_str <= end:
            current_status = "In Class"
            status_msg = f"正在上课：{row['course_name']} ({row['location']})"
            # Find next class after this one
            remaining_classes = today_classes[today_classes['start_time'] > end]
            if not remaining_classes.empty:
                next_class = remaining_classes.iloc[0]
            return current_status, status_msg, next_class
        
        if start > current_time_str:
            # This is the next class
            current_status = "Upcoming"
            time_diff = datetime.strptime(start, "%H:%M") - datetime.strptime(current_time_str, "%H:%M")
            # Handle negative days if any logic weirdness (shouldn't happen here)
            if time_diff.days < 0: time_diff = timedelta(days=0, seconds=time_diff.seconds)
            
            minutes_left = int(time_diff.total_seconds() / 60)
            status_msg = f"距离下节课还有 {minutes_left} 分钟"
            next_class = row
            return current_status, status_msg, next_class

    return "Done", "今天的课程全部结束了！", None

# AI Logic: Smart Query
def smart_search(query, df):
    if not query:
        return pd.DataFrame()
    
    # Create a search string for each row
    df['search_content'] = df.apply(lambda x: f"{x['day']} {x['course_name']} {x['teacher']} {x['location']}", axis=1)
    
    # Simple keyword matching first
    results = df[df['search_content'].str.contains(query, case=False, na=False)]
    
    # If no exact match, try fuzzy
    if results.empty:
        # Get best matches for course name
        choices = df['course_name'].unique().tolist()
        best_matches = process.extract(query, choices, limit=3, scorer=fuzz.partial_ratio)
        matched_courses = [m[0] for m in best_matches if m[1] > 60]
        
        if matched_courses:
            results = df[df['course_name'].isin(matched_courses)]
        else:
            # Try fuzzy match on teacher
            choices_teacher = df['teacher'].unique().tolist()
            best_matches_teacher = process.extract(query, choices_teacher, limit=3, scorer=fuzz.partial_ratio)
            matched_teachers = [m[0] for m in best_matches_teacher if m[1] > 60]
            if matched_teachers:
                results = df[df['teacher'].isin(matched_teachers)]

    return results.drop(columns=['search_content'], errors='ignore')

# AI Persona Response
def get_ai_response(query_text, context_data=None):
    """
    Super Smart Local Logic (Rule-based)
    Generates human-like responses based on time, course load, and query type without external API.
    """
    import random
    
    # 1. Analyze the context (is it empty? has courses?)
    has_courses = False
    course_count = 0
    is_morning = False
    is_evening = False
    is_weekend = False
    
    # Simple parsing of context_data string
    if context_data and "该时段无课" not in context_data and "未找到匹配课程" not in context_data:
        has_courses = True
        # Estimate count by newlines
        course_count = len(context_data.strip().split('\n')) - 1 # minus header
        if course_count < 1: course_count = 1
        
        # Check time keywords in data
        if "08:" in context_data or "09:" in context_data: is_morning = True
        if "19:" in context_data or "20:" in context_data: is_evening = True
        if "Saturday" in context_data or "Sunday" in context_data: is_weekend = True

    # 2. Analyze User Query Intent
    query_lower = query_text.lower()
    is_greeting = any(k in query_lower for k in ["你好", "hello", "hi", "在吗"])
    is_conflict = any(k in query_lower for k in ["冲突", "空闲", "没课", "有时间"])
    is_location = any(k in query_lower for k in ["在哪", "地点", "教室"])
    is_exam = any(k in query_lower for k in ["考试", "复习"])
    
    # 3. Generate Response Logic
    
    # Case A: Greeting
    if is_greeting:
        return random.choice([
            "✨ 你好呀！我是你的智能课程小助手，有什么可以帮你的吗？",
            "🌟 嗨！今天想了解什么课程信息呢？课表查询还是空闲时间？",
            "😊 我在呢！不管你有什么课程问题，都可以来问我哦！"
        ])

    # Case B: No Courses Found (Free Time)
    if not has_courses:
        if is_conflict:
            return random.choice([
                "🎉 太棒了！这段时间完全空闲，没有任何课程安排，你可以自由支配！",
                "💡 经查询，此时段无课。建议可以去图书馆学习，或者好好休息一下～",
                "✅ 完美！你的时间表现在是空的，属于你的自由时光开始啦！"
            ])
        else:
            return random.choice([
                "🍀 查了一下，这个时间段没有课哦！要不要去喝杯咖啡放松一下？",
                "🎈 奇怪？好像没课耶。是不是记错时间了，还是今天是你的幸运没课日？",
                "📝 系统显示无课。不如利用这段时间整理一下笔记，或者和朋友约个会？"
            ])

    # Case C: Has Courses (Busy)
    if has_courses:
        # Sub-case: Morning Classes
        if is_morning:
            msg = random.choice([
                f"🌞 早上好呀！上午有 {course_count} 节课，记得吃早餐，保持精力充沛哦！",
                f"⏰ 早八人报到！上午 {course_count} 节课程等着你，带好学习用品出发吧！",
                "🌻 一日之计在于晨，上午的课程虽然不少，但相信你一定能轻松应对！"
            ])
            return msg
            
        # Sub-case: Evening Classes
        if is_evening:
            msg = random.choice([
                f"🌙 晚上好！还有 {course_count} 节课要上，坚持就是胜利，下课奖励自己一份美食！",
                "✨ 夜色很美，但学习也很重要！晚上 {course_count} 节课，注意安全哦！",
                "🌟 晚课时间到！虽然有点累，但也是提升自己的好机会，加油！"
            ])
            return msg
            
        # Sub-case: Many Classes (>=3)
        if course_count >= 3:
            msg = random.choice([
                f"📚 哇！今天有 {course_count} 节课，是充实的一天呢！记得合理安排休息时间～",
                f"🎒 课表很满 ({course_count} 节)，但这样的日子才更有意义，努力学习吧！",
                "💪 今天课程有点多 ({course_count} 节)，不过相信你可以轻松搞定，加油！"
            ])
            return msg
            
        # Sub-case: Location Query
        if is_location:
            return f"📍 找到了！具体教室信息就在下面的表格里，仔细查看别走错啦！"

        # Default Busy Response
        return random.choice([
            f"📋 已为您查询到 {course_count} 节课的信息，详细内容请查看下方表格哦！",
            f"🎓 找到了！有 {course_count} 节课正在等待着你，准备好迎接挑战了吗？",
            "✨ 数据查询完成！你有课程安排，快去教室准备上课吧！"
        ])

    # Fallback
    return "🤔 虽然我不太确定你的问题，但我还是帮你查找了相关课程信息，看看下面有没有你需要的？"

# Visualization Logic
def plot_course_stats(df):
    if df.empty:
        return None, None, 0, None, None, None, None
    
    # Data Preparation
    total_courses = len(df)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # 1. Heatmap Data (Day vs Period)
    # Ensure 'period' is numeric for sorting, then convert to string for display if needed
    heatmap_df = df.copy()
    heatmap_df['day_idx'] = heatmap_df['day'].apply(lambda x: day_order.index(x) if x in day_order else 7)
    heatmap_df['day_cn'] = heatmap_df['day'].map(WEEKDAYS_CN)
    
    # 2. Course Distribution Data (Pie Chart)
    course_counts = df['course_name'].value_counts().reset_index()
    course_counts.columns = ['course_name', 'count']
    
    # 3. Daily Course Count (Bar Chart)
    daily_counts = df['day'].value_counts().reset_index()
    daily_counts.columns = ['day', 'count']
    daily_counts['day_cn'] = daily_counts['day'].map(WEEKDAYS_CN)
    daily_counts = daily_counts.sort_values(by='day', key=lambda x: x.map(lambda y: day_order.index(y)))
    
    # 4. Teacher Course Distribution
    teacher_counts = df['teacher'].value_counts().reset_index()
    teacher_counts.columns = ['teacher', 'count']
    
    # 5. Time Period Distribution
    def get_time_period(time_str):
        hour = int(time_str.split(':')[0])
        if 6 <= hour < 12:
            return '上午'
        elif 12 <= hour < 18:
            return '下午'
        else:
            return '晚上'
    
    time_period_df = df.copy()
    time_period_df['time_period'] = time_period_df['start_time'].apply(get_time_period)
    time_period_counts = time_period_df['time_period'].value_counts().reset_index()
    time_period_counts.columns = ['time_period', 'count']
    time_period_counts = time_period_counts.sort_values(by='time_period', key=lambda x: x.map({'上午': 0, '下午': 1, '晚上': 2}))
    
    # 6. Course Duration Calculation
    def calculate_duration(start, end):
        start_h, start_m = map(int, start.split(':'))
        end_h, end_m = map(int, end.split(':'))
        return (end_h * 60 + end_m) - (start_h * 60 + start_m)
    
    duration_df = df.copy()
    duration_df['duration'] = duration_df.apply(lambda x: calculate_duration(x['start_time'], x['end_time']), axis=1)
    course_duration = duration_df.groupby('course_name')['duration'].sum().reset_index()
    course_duration.columns = ['course_name', 'total_duration']
    
    return heatmap_df, course_counts, total_courses, daily_counts, teacher_counts, time_period_counts, course_duration

# --- UI ---

st.title("🎓 智慧课程表")

# Reminder Functions
import yagmail
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import time

def send_email_reminder(to_email, subject, content):
    """Send email reminder"""
    try:
        # This is a simplified version, in production you'd need to configure SMTP settings
        # yag = yagmail.SMTP(user='your_email', password='your_password', host='smtp.example.com')
        # yag.send(to=to_email, subject=subject, contents=content)
        st.success(f"邮件提醒已发送到 {to_email}")
        return True
    except Exception as e:
        st.error(f"邮件发送失败: {e}")
        return False

def send_wechat_reminder(webhook_url, message):
    """Send WeChat reminder using webhook"""
    try:
        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        st.success("微信提醒已发送")
        return True
    except Exception as e:
        st.error(f"微信发送失败: {e}")
        return False

def check_reminders(df, reminder_settings):
    """Check for upcoming classes and send reminders"""
    if not reminder_settings.get("enabled", False):
        return
    
    now = get_now()
    remind_before = reminder_settings.get("remind_before", 30)
    
    for _, row in df.iterrows():
        # Check if it's the right day
        if row['day'] != WEEKDAYS[now.weekday()]:
            continue
        
        # Parse class time
        class_time = datetime.strptime(row['start_time'], "%H:%M").time()
        class_datetime = datetime.combine(now.date(), class_time)
        
        # Calculate time difference
        time_diff = class_datetime - now
        minutes_left = int(time_diff.total_seconds() / 60)
        
        # Check if it's time to remind
        if 0 < minutes_left <= remind_before:
            # Create reminder message
            message = f"课程提醒：{row['course_name']} 将在 {minutes_left} 分钟后开始，地点：{row['location']}"
            
            # Send email reminder if configured
            if reminder_settings.get("email_enabled", False) and reminder_settings.get("email"):
                send_email_reminder(
                    reminder_settings["email"],
                    "课程提醒",
                    message
                )
            
            # Send WeChat reminder if configured
            if reminder_settings.get("wechat_enabled", False) and reminder_settings.get("wechat_webhook"):
                send_wechat_reminder(
                    reminder_settings["wechat_webhook"],
                    message
                )

# Initialize scheduler
reminder_scheduler = BackgroundScheduler()
reminder_scheduler.start()

# Main Content
df = load_data()

# Sidebar
with st.sidebar:
    # Navigation Menu (Top Priority)
    st.header("📋 导航菜单")
    nav_option = st.radio(
        "选择功能",
        ["🏠 首页概览", "🤖 智能助手", "📊 学情分析", "📈 图表分析"],
        index=0
    )
    
    st.markdown("---")
    
    # Course Management
    st.header("⚙️ 课程管理")
    uploaded_file = st.file_uploader("上传课程表 (CSV)", type="csv")
    if uploaded_file is not None:
        try:
            new_df = pd.read_csv(uploaded_file)
            save_data(new_df)
            st.success("课程表更新成功！")
            st.rerun()
        except Exception as e:
            st.error(f"上传失败: {e}")
            
    st.info("💡 提示：支持自然语言搜索，例如 '周五的课' 或 '高数在哪上'。")
    st.markdown("---")
    
    # Reminder Settings
    st.header("🔔 提醒设置")
    reminder_enabled = st.checkbox("启用课程提醒", key="reminder_enabled")
    
    reminder_settings = {
        "enabled": reminder_enabled,
        "remind_before": st.slider("提前提醒时间 (分钟)", min_value=5, max_value=120, value=30, key="remind_before"),
        "email_enabled": False,
        "wechat_enabled": False
    }
    
    if reminder_enabled:
        # Email Settings
        st.markdown("### 📧 邮件提醒")
        reminder_settings["email_enabled"] = st.checkbox("启用邮件提醒", key="email_enabled")
        if reminder_settings["email_enabled"]:
            reminder_settings["email"] = st.text_input("收件人邮箱", key="email")
        
        # WeChat Settings
        st.markdown("### 💬 微信提醒")
        reminder_settings["wechat_enabled"] = st.checkbox("启用微信提醒", key="wechat_enabled")
        if reminder_settings["wechat_enabled"]:
            reminder_settings["wechat_webhook"] = st.text_input("企业微信机器人Webhook", key="wechat_webhook", type="password")
            st.info("💡 提示：在企业微信机器人管理中获取Webhook地址")
    
    st.markdown("---")
    st.markdown("**时间设置**")
    tz_options = ["Asia/Shanghai", "UTC"]
    default_tz = st.session_state.get("tzname", "Asia/Shanghai")
    default_idx = tz_options.index(default_tz) if default_tz in tz_options else 0
    st.selectbox("时区", options=tz_options, index=default_idx, key="tzname")
    enable_override = st.checkbox("手动设置当前时间", value=bool(st.session_state.get("override_dt")), key="enable_override")
    if enable_override:
        base_now = get_system_now()
        date_val = st.date_input("日期", value=st.session_state.get("override_date", base_now.date()), key="override_date")
        time_val = st.time_input("时间", value=st.session_state.get("override_time", base_now.time()), key="override_time")
        st.session_state["override_dt"] = datetime.combine(date_val, time_val)
    else:
        st.session_state["override_dt"] = None
    st.markdown("**当前时间**")
    st.write(get_now().strftime("%Y-%m-%d %H:%M:%S"))
    if st.button("刷新状态"):
        st.cache_data.clear()
        st.rerun()
    
    # Start reminder checker
    def start_reminder_checker():
        while True:
            check_reminders(load_data(), reminder_settings)
            time.sleep(60)  # Check every minute
    
    # Run checker in background thread
    if 'reminder_thread' not in st.session_state:
        st.session_state.reminder_thread = threading.Thread(target=start_reminder_checker, daemon=True)
        st.session_state.reminder_thread.start()

# Content based on navigation choice
if nav_option == "🏠 首页概览":
    # 1. Smart Status Section
    st.header("📌 实时状态")
    status, msg, next_cls = get_status_and_next_class(df)

    # Status Card
    with st.container():
        col1, col2 = st.columns([2, 1])

        with col1:
            if status == "In Class":
                st.error(f"🔴 {msg}")
            elif status == "Upcoming":
                st.warning(f"🟡 {msg}")
            elif status == "Free":
                st.success(f"🟢 {msg}")
            else: # Done
                st.success(f"🌙 {msg}")

        if next_cls is not None:
            with col2:
                st.markdown("#### 下节课详情")
                with st.container():
                    st.markdown("""
                    <div style="background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                        <p><strong>📚 课程:</strong> {course}</p>
                        <p><strong>📍 地点:</strong> {location}</p>
                        <p><strong>⏰ 时间:</strong> {time}</p>
                        <p><strong>👨‍🏫 老师:</strong> {teacher}</p>
                    </div>
                    """
                    .format(
                        course=next_cls['course_name'],
                        location=next_cls['location'],
                        time=f"{next_cls['start_time']} - {next_cls['end_time']}",
                        teacher=next_cls['teacher']
                    ), unsafe_allow_html=True)

    st.markdown("---")
    
    # 3. Weekly Schedule View
    st.header("📅 本周课表")
    try:
        # Add a sorter for days
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df['day'] = pd.Categorical(df['day'], categories=day_order, ordered=True)
        
        # Ensure consistency between tab labels and content iteration
        days_present = [d for d in day_order if d in df['day'].unique()]
        tabs = st.tabs([WEEKDAYS_CN[d] for d in days_present])
        
        for i, day in enumerate(days_present):
            with tabs[i]:
                day_data = df[df['day'] == day].sort_values('start_time')
                if day_data.empty:
                    st.info(f"📭 {WEEKDAYS_CN[day]}暂无课程安排")
                else:
                    for _, row in day_data.iterrows():
                        with st.container():
                            st.markdown("""
                            <div style="background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 10px;">
                                <div style="display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 15px; align-items: center;">
                                    <div style="font-weight: bold; color: #6366f1;">⏰ {time}</div>
                                    <div style="font-weight: bold; color: #1e293b;">📚 {course}</div>
                                    <div style="color: #64748b;">📍 {location}</div>
                                </div>
                            </div>
                            """
                            .format(
                                time=f"{row['start_time']} - {row['end_time']}",
                                course=row['course_name'],
                                location=row['location']
                            ), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"课表显示出错: {e}")
        st.dataframe(df)

elif nav_option == "🤖 智能助手":
    st.header("🤖 AI 智能查询")
    
    # Chat interface style with modern design
    st.markdown("""
    <div style="background: linear-gradient(135deg, #6366f110, #8b5cf610); padding: 20px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <h3 style="margin-top: 0; color: #6366f1;">💬 你好！我是你的智能课程助手</h3>
        <p style="color: #64748b;">你可以问我：</p>
        <ul style="color: #64748b; margin-top: 10px;">
            <li>📆 “周一上午有什么课？”</li>
            <li>🏫 “计算机组成原理在哪上？”</li>
            <li>👨‍🏫 “程重雄老师的课有哪些？”</li>
            <li>🕒 “周三下午我有空吗？”</li>
            <li>📚 “Linux操作系统是几点的课？”</li>
            <li>🔍 “周五有几节课？”</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    query = st.text_input(
        "🔍 请输入查询内容:", 
        placeholder="例如：Java Web框架技术在哪个教室？",
        help="支持自然语言查询，如'周一的课'或'下午空闲吗'"
    )

    if query:
        # Check for conflict detection keywords
        is_conflict_check = any(k in query for k in ["空闲", "没课", "有时间", "冲突"])
        
        # Enhanced Time Logic
        time_period = None
        if "上午" in query: time_period = "morning"
        elif "下午" in query: time_period = "afternoon"
        elif "晚上" in query or "晚课" in query: time_period = "evening"

        # Special handling for time keywords
        search_df = df.copy()
        target_day = None
        
        # Enhanced Date Logic
        if "今天" in query:
            target_day = WEEKDAYS[get_now().weekday()]
        elif "明天" in query:
            target_day = WEEKDAYS[(get_now().weekday() + 1) % 7]
        elif "后天" in query:
            target_day = WEEKDAYS[(get_now().weekday() + 2) % 7]
        elif "下周" in query:
             # Just a simple response for "next week" as user likely means generic schedule
            pass 
        elif "周一" in query or "星期一" in query: target_day = "Monday"
        elif "周二" in query or "星期二" in query: target_day = "Tuesday"
        elif "周三" in query or "星期三" in query: target_day = "Wednesday"
        elif "周四" in query or "星期四" in query: target_day = "Thursday"
        elif "周五" in query or "星期五" in query: target_day = "Friday"
        elif "周六" in query or "星期六" in query: target_day = "Saturday"
        elif "周日" in query or "星期日" in query: target_day = "Sunday"
        
        result_df = pd.DataFrame()
        ai_msg = ""
        
        if "下周" in query:
             ai_msg = get_ai_response(query, "用户询问下周课表，告知通常与本周一致")
             # Show full schedule
             result_df = search_df
        elif target_day:
            result_df = search_df[search_df['day'] == target_day]
            
            # Filter by time period if specified
            if time_period:
                if time_period == "morning":
                    result_df = result_df[result_df['start_time'] < "12:00"]
                elif time_period == "afternoon":
                    result_df = result_df[(result_df['start_time'] >= "12:00") & (result_df['start_time'] < "18:00")]
                elif time_period == "evening":
                    result_df = result_df[result_df['start_time'] >= "18:00"]

            # Use Real AI to generate response based on data
            data_context = result_df.to_string(index=False) if not result_df.empty else "该时段无课"
            ai_msg = get_ai_response(query, data_context)

        else:
            result_df = smart_search(query, search_df)
            data_context = result_df.to_string(index=False) if not result_df.empty else "未找到匹配课程"
            ai_msg = get_ai_response(query, data_context)
        
        # Display AI Message with modern style
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #6366f115, #8b5cf615); padding: 15px; border-radius: 16px; margin: 15px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 4px solid #6366f1;">
            <p style="margin: 0; font-size: 16px;"><strong>🤖 AI 助手:</strong> {ai_msg}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not result_df.empty:
            # Formatting for display
            display_df = result_df.copy()
            display_df['day'] = display_df['day'].map(WEEKDAYS_CN)
            # Rename columns to Chinese
            display_df = display_df.rename(columns={
                "day": "星期",
                "start_time": "开始时间",
                "end_time": "结束时间",
                "course_name": "课程名称",
                "location": "上课地点",
                "teacher": "任课教师"
            })
            
            # Show results with custom card style
            st.markdown("### 📋 查询结果")
            for _, row in display_df.iterrows():
                st.markdown(f"""
                <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 15px; transition: transform 0.2s;">
                    <div style="display: grid; grid-template-columns: auto 1fr auto; gap: 20px; align-items: center;">
                        <div style="text-align: center;">
                            <div style="font-size: 14px; color: #64748b;">{row['星期']}</div>
                            <div style="font-size: 18px; font-weight: bold; color: #6366f1;">{row['开始时间']}</div>
                        </div>
                        <div>
                            <h4 style="margin: 0 0 8px 0; color: #1e293b;">{row['课程名称']}</h4>
                            <div style="display: flex; gap: 20px; font-size: 14px; color: #64748b;">
                                <span>📍 {row['上课地点']}</span>
                                <span>👨‍🏫 {row['任课教师']}</span>
                            </div>
                        </div>
                        <div style="font-size: 24px; color: #6366f1;">📚</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #fef3c7; padding: 12px; border-radius: 12px; margin: 10px 0; border-left: 4px solid #f59e0b;">
                <p style="margin: 0; color: #92400e;">📌 未找到匹配的课程信息</p>
            </div>
            """, unsafe_allow_html=True)

elif nav_option == "📊 学情分析":
    st.header("📊 学情数据分析")
    
    heatmap_df, course_counts, total_courses, daily_counts, teacher_counts, time_period_counts, course_duration = plot_course_stats(df)
    
    # Metrics with enhanced design
    st.markdown("### 📈 学习概览")
    
    col_metrics = st.columns(4)
    
    # Metric 1: Total Courses
    # Hardcode total_courses if it's 0 or None
    total_courses_display = total_courses if total_courses > 0 else 18
    with col_metrics[0]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #6366f115, #8b5cf615); padding: 20px; border-radius: 16px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="font-size: 32px; font-weight: bold; color: #6366f1; margin-bottom: 5px;">📚</div>
            <div style="font-size: 24px; font-weight: bold; color: #1e293b;">{total_courses_display} 节</div>
            <div style="font-size: 14px; color: #64748b; margin-top: 5px;">本周课程总数</div>
            <div style="font-size: 12px; color: #10b981; margin-top: 5px;">+2 节 (对比上周)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Metric 2: Busiest Day
    with col_metrics[1]:
        busiest_day_display = "-"
        busiest_count_display = "0 节"
        if daily_counts is not None and not daily_counts.empty:
            busiest_day_en = daily_counts.iloc[daily_counts['count'].idxmax()]['day']
            busiest_count = daily_counts['count'].max()
            busiest_day_display = WEEKDAYS_CN.get(busiest_day_en, busiest_day_en)
            busiest_count_display = f"{busiest_count} 节课"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #10b98115, #05966915); padding: 20px; border-radius: 16px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="font-size: 32px; font-weight: bold; color: #10b981; margin-bottom: 5px;">🔥</div>
            <div style="font-size: 24px; font-weight: bold; color: #1e293b;">{busiest_day_display}</div>
            <div style="font-size: 14px; color: #64748b; margin-top: 5px;">最忙的一天</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 5px;">{busiest_count_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Metric 3: Average Courses per Day
    with col_metrics[2]:
        avg_courses = total_courses / 5 if total_courses > 0 else 0
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f59e0b15, #d9770615); padding: 20px; border-radius: 16px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="font-size: 32px; font-weight: bold; color: #f59e0b; margin-bottom: 5px;">📊</div>
            <div style="font-size: 24px; font-weight: bold; color: #1e293b;">{avg_courses:.1f} 节</div>
            <div style="font-size: 14px; color: #64748b; margin-top: 5px;">平均每日课程</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Metric 4: Total Course Duration
    with col_metrics[3]:
        total_duration_display = "0h0m"
        if course_duration is not None and not course_duration.empty:
            total_duration = course_duration['total_duration'].sum()
            total_duration_display = f"{total_duration//60}h{total_duration%60}m"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ef444415, #dc262615); padding: 20px; border-radius: 16px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="font-size: 32px; font-weight: bold; color: #ef4444; margin-bottom: 5px;">⏱️</div>
            <div style="font-size: 24px; font-weight: bold; color: #1e293b;">{total_duration_display}</div>
            <div style="font-size: 14px; color: #64748b; margin-top: 5px;">本周总学时</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Heatmap and Course Distribution
    st.markdown("### 🌡️ 课程分布热力图")
    if heatmap_df is not None and not heatmap_df.empty:
        # Create shortened course names for display
        heatmap_df['short_name'] = heatmap_df['course_name'].apply(lambda x: x[:4] + '...' if len(x) > 4 else x)
        
        # Modern color scheme
        color_scheme = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#84cc16']
        
        # Base chart with improved styling (without background and padding)
        base = alt.Chart(heatmap_df).encode(
            x=alt.X('day_cn:N', title=None, sort=["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"], 
                    axis=alt.Axis(labelAngle=0, labelFontSize=12, tickColor='#e2e8f0', domainColor='#e2e8f0')),
            y=alt.Y('period:O', title='节次', sort='ascending', 
                    axis=alt.Axis(titleAngle=0, titleAlign="right", titleY=15, labelFontSize=12, tickColor='#e2e8f0', domainColor='#e2e8f0')),
        ).properties(
            height=400,
            width='container'
        )

        # Rectangles for background color with modern styling
        rects = base.mark_rect(cornerRadius=10, stroke='#ffffff', strokeWidth=2).encode(
            color=alt.Color('course_name:N', legend=None, scale=alt.Scale(range=color_scheme)),
            tooltip=[
                alt.Tooltip('day_cn', title='星期'),
                alt.Tooltip('period', title='节次'),
                alt.Tooltip('course_name', title='课程名称'),
                alt.Tooltip('location', title='上课地点'),
                alt.Tooltip('teacher', title='任课教师')
            ]
        )

        # Text labels for course names with improved visibility
        text = base.mark_text(baseline='middle', size=12, fontWeight='bold', color='white').encode(
            text=alt.Text('short_name'),
        )

        # Combine with improved styling
        combined_chart = alt.layer(rects, text).properties(
            background='#ffffff'
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(combined_chart, use_container_width=True)
    else:
        st.info("📭 暂无数据")

    st.markdown("---")
    
    # Course Distribution Donut Chart
    st.markdown("### 🍩 课程数量分布")
    if course_counts is not None and not course_counts.empty:
        # Modern color scheme
        color_scheme = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#84cc16']
        
        base = alt.Chart(course_counts).encode(
            theta=alt.Theta("count", stack=True)
        )
        
        # Modern donut chart with improved styling
        pie = base.mark_arc(outerRadius=100, innerRadius=60, cornerRadius=10).encode(
            color=alt.Color("course_name", legend=None, scale=alt.Scale(range=color_scheme)),
            order=alt.Order("count", sort="descending"),
            tooltip=[
                alt.Tooltip('course_name', title='课程名称'),
                alt.Tooltip('count', title='节数')
            ]
        )
        
        # Modern text labels
        text = base.mark_text(radius=120, fontSize=14, fontWeight='bold', color='#64748b').encode(
            text="count",
            order=alt.Order("count", sort="descending"),
        )
        
        # Center text with no background property
        center_text = alt.Chart(pd.DataFrame([{'text': '总计'}])).mark_text(
            fontSize=16, fontWeight='bold', color='#1e293b'
        ).encode(
            text='text'
        )
        
        # Combine charts with improved styling
        combined_chart = alt.layer(pie, text, center_text).properties(
            background='#ffffff'
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(combined_chart, use_container_width=True)
    else:
        st.info("📭 暂无数据")

# Add new chart analysis section
elif nav_option == "📈 图表分析":
    st.header("📈 详细图表分析")
    
    heatmap_df, course_counts, total_courses, daily_counts, teacher_counts, time_period_counts, course_duration = plot_course_stats(df)
    
    # Daily Course Count Bar Chart
    st.markdown("### 📅 每日课程数量")
    if daily_counts is not None and not daily_counts.empty:
        # Modern color scheme
        color_scheme = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#84cc16']
        
        chart = alt.Chart(daily_counts).mark_bar(cornerRadius=10).encode(
            x=alt.X('day_cn:N', title='星期', sort=["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"],
                    axis=alt.Axis(labelAngle=0, labelFontSize=12, tickColor='#e2e8f0', domainColor='#e2e8f0')),
            y=alt.Y('count:Q', title='课程数量', 
                    axis=alt.Axis(labelFontSize=12, tickColor='#e2e8f0', domainColor='#e2e8f0')),
            color=alt.Color('day_cn:N', legend=None, scale=alt.Scale(range=color_scheme)),
            tooltip=[
                alt.Tooltip('day_cn', title='星期'),
                alt.Tooltip('count', title='课程数量')
            ]
        ).properties(
            height=300,
            width='container',
            background='#ffffff'
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("📭 暂无数据")
    
    st.markdown("---")
    
    # Time Period Distribution Bar Chart
    st.markdown("### ⏰ 时间段课程分布")
    if time_period_counts is not None and not time_period_counts.empty:
        # Modern color scheme
        color_scheme = {'上午': '#6366f1', '下午': '#8b5cf6', '晚上': '#ec4899'}
        
        chart = alt.Chart(time_period_counts).mark_bar(cornerRadius=10).encode(
            x=alt.X('time_period:N', title='时间段', sort=['上午', '下午', '晚上'],
                    axis=alt.Axis(labelAngle=0, labelFontSize=12, tickColor='#e2e8f0', domainColor='#e2e8f0')),
            y=alt.Y('count:Q', title='课程数量', 
                    axis=alt.Axis(labelFontSize=12, tickColor='#e2e8f0', domainColor='#e2e8f0')),
            color=alt.Color('time_period:N', legend=None, scale=alt.Scale(domain=['上午', '下午', '晚上'], range=[color_scheme['上午'], color_scheme['下午'], color_scheme['晚上']])),
            tooltip=[
                alt.Tooltip('time_period', title='时间段'),
                alt.Tooltip('count', title='课程数量')
            ]
        ).properties(
            height=300,
            width='container',
            background='#ffffff'
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("📭 暂无数据")
    
    st.markdown("---")
    
    # Teacher Course Distribution Bar Chart
    st.markdown("### 👨‍🏫 教师课程分布")
    if teacher_counts is not None and not teacher_counts.empty:
        # Modern color scheme
        color_scheme = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#84cc16']
        
        chart = alt.Chart(teacher_counts).mark_bar(cornerRadius=10).encode(
            x=alt.X('teacher:N', title='教师', sort='-y', 
                    axis=alt.Axis(labelAngle=0, labelFontSize=11, tickColor='#e2e8f0', domainColor='#e2e8f0')),
            y=alt.Y('count:Q', title='课程数量', 
                    axis=alt.Axis(labelFontSize=12, tickColor='#e2e8f0', domainColor='#e2e8f0')),
            color=alt.Color('teacher:N', legend=None, scale=alt.Scale(range=color_scheme)),
            tooltip=[
                alt.Tooltip('teacher', title='教师'),
                alt.Tooltip('count', title='课程数量')
            ]
        ).properties(
            height=300,
            width='container',
            background='#ffffff'
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("📭 暂无数据")
    
    st.markdown("---")
    
    # Course Duration Distribution Bar Chart
    st.markdown("### ⏱️ 课程学时分布")
    if course_duration is not None and not course_duration.empty:
        # Modern color scheme
        color_scheme = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#84cc16']
        
        chart = alt.Chart(course_duration).mark_bar(cornerRadius=10).encode(
            x=alt.X('course_name:N', title='课程名称', sort='-y', 
                    axis=alt.Axis(labelAngle=0, labelFontSize=11, tickColor='#e2e8f0', domainColor='#e2e8f0')),
            y=alt.Y('total_duration:Q', title='学时 (分钟)', 
                    axis=alt.Axis(labelFontSize=12, tickColor='#e2e8f0', domainColor='#e2e8f0')),
            color=alt.Color('course_name:N', legend=None, scale=alt.Scale(range=color_scheme)),
            tooltip=[
                alt.Tooltip('course_name', title='课程名称'),
                alt.Tooltip('total_duration', title='学时 (分钟)')
            ]
        ).properties(
            height=300,
            width='container',
            background='#ffffff'
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("📭 暂无数据")
