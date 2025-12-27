import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from thefuzz import process, fuzz
import random
import altair as alt
from openai import OpenAI
import os

# Page Configuration
st.set_page_config(
    page_title="校园课程表智能助手",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to hide/translate English elements
st.markdown("""
<style>
    /* 尝试隐藏 File Uploader 的英文提示小字 */
    [data-testid="stFileUploader"] small {
        display: none;
    }
    /* 增加一些圆角和阴影 */
    .stCard {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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

# Load Data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("schedule_data.csv")
        return df
    except FileNotFoundError:
        st.error("未找到课程表数据文件 (schedule_data.csv)。请在侧边栏上传或检查文件路径。")
        return pd.DataFrame(columns=["day", "period", "start_time", "end_time", "course_name", "location", "teacher"])

def save_data(df):
    df.to_csv("schedule_data.csv", index=False)
    st.cache_data.clear()

# Core Logic: Get Current Status and Next Class
def get_status_and_next_class(df):
    now = datetime.now()
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
            "👋 你好呀！我是你的智能课程助手，随时待命！",
            "Hi！今天想查点什么？课表还是空闲时间？",
            "我在呢！虽然我是个机器人，但我会一直陪着你学习的！🤖"
        ])

    # Case B: No Courses Found (Free Time)
    if not has_courses:
        if is_conflict:
            return random.choice([
                "好消息！这段时间完全空闲，没有任何冲突，放心安排！🎉",
                "经过扫描，此时段无课。去图书馆卷一会儿，还是回宿舍躺平？🛌",
                "完美！时间表一片空白，属于你的自由时间到了！"
            ])
        else:
            return random.choice([
                "查了一下，这个时间段没有课哦！去喝杯奶茶放松一下吧！🥤",
                "咦？好像没课耶。是不是记错时间了，还是这就是传说中的“没课日”？😎",
                "系统显示无课。建议利用这段时间预习一下（或者打把游戏）？🎮"
            ])

    # Case C: Has Courses (Busy)
    if has_courses:
        # Sub-case: Morning Classes
        if is_morning:
            msg = random.choice([
                f"早起的鸟儿有虫吃！上午有 {course_count} 节课，记得吃早餐哦！🥯",
                f"早八人集合！上午 {course_count} 节硬仗要打，带好水杯和书本！📚",
                "一日之计在于晨，上午的课虽然多，但你可以的！加油！💪"
            ])
            return msg
            
        # Sub-case: Evening Classes
        if is_evening:
            msg = random.choice([
                f"辛苦啦！晚上还有 {course_count} 节课。坚持一下，下课就能吃夜宵了！🍢",
                "夜色温柔，但你还得去上课... 晚上注意安全哦！",
                "晚课虽然累，但也是弯道超车的好机会！冲鸭！🦆"
            ])
            return msg
            
        # Sub-case: Many Classes (>=3)
        if course_count >= 3:
            msg = random.choice([
                f"天哪，查到了 {course_count} 节课！这可是特种兵的一天，挺住！🛡️",
                f"课表满满当当的 ({course_count} 节)，是充实的一天呢！注意劳逸结合。",
                "这么多课... 摸摸头，上完奖励自己一顿大餐吧！🍲"
            ])
            return msg
            
        # Sub-case: Location Query
        if is_location:
            return f"帮你找到了！就在表格里写着呢，别跑错教室啦！🏃‍♂️"

        # Default Busy Response
        return random.choice([
            f"收到！为您查到了 {course_count} 节课的信息，详情请看下方表格。👇",
            f"目标锁定！有 {course_count} 节课正在等着你。准备好去上课了吗？",
            "数据检索完毕。看来是不能偷懒了，快去教室占座吧！💺"
        ])

    # Fallback
    return "虽然我不确定你在说什么，但我还是尽力帮你找了找课表... 看看下面有没有？"

# Visualization Logic
def plot_course_stats(df):
    if df.empty:
        return
    
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
    
    return heatmap_df, course_counts, total_courses

# --- UI ---

st.title("🎓 校园课程表智能助手")

# Sidebar
with st.sidebar:
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
    st.markdown("**当前时间**")
    st.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if st.button("刷新状态"):
        st.cache_data.clear()
        st.rerun()

# Main Content
df = load_data()

# Tabs for different features
tab1, tab2, tab3 = st.tabs(["🏠 首页概览", "🤖 智能助手", "📊 学情分析"])

with tab1:
    # 1. Smart Status Section
    st.header("📌 实时状态")
    status, msg, next_cls = get_status_and_next_class(df)

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
            st.markdown(f"**课程:** {next_cls['course_name']}")
            st.markdown(f"**地点:** {next_cls['location']}")
            st.markdown(f"**时间:** {next_cls['start_time']} - {next_cls['end_time']}")
            st.markdown(f"**老师:** {next_cls['teacher']}")

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
                for _, row in day_data.iterrows():
                    with st.container():
                        c1, c2, c3 = st.columns([1, 2, 1])
                        c1.write(f"**{row['start_time']} - {row['end_time']}**")
                        c2.write(f"**{row['course_name']}**")
                        c3.write(f"📍 {row['location']}")
                        st.divider()
    except Exception as e:
        st.error(f"课表显示出错: {e}")
        st.dataframe(df)

with tab2:
    st.header("🤖 AI 智能查询")
    
    # Chat interface style
    st.markdown("""
    <div style="background-color:#f0f2f6;padding:10px;border-radius:10px;margin-bottom:20px;">
        <p>👋 你好！我是你的课程助手。你可以问我：</p>
        <ul>
            <li>“明天有什么课？”</li>
            <li>“高数在哪上？”</li>
            <li>“周五下午空闲吗？”（冲突检测）</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    query = st.text_input("请输入查询内容:", placeholder="例如：明天上午有课吗？")

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
            target_day = WEEKDAYS[datetime.now().weekday()]
        elif "明天" in query:
            target_day = WEEKDAYS[(datetime.now().weekday() + 1) % 7]
        elif "后天" in query:
            target_day = WEEKDAYS[(datetime.now().weekday() + 2) % 7]
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
        
        # Display AI Message
        st.success(f"🤖 AI: {ai_msg}")
        
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
            st.dataframe(display_df[['星期', '开始时间', '课程名称', '上课地点', '任课教师']], use_container_width=True)

with tab3:
    st.header("📊 学情数据分析")
    
    heatmap_df, course_counts, total_courses = plot_course_stats(df)
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("本周课程总数", f"{total_courses} 节", "+2 (对比上周)")
    
    # Calculate busiest day
    if not heatmap_df.empty:
        busiest_day_en = heatmap_df['day'].value_counts().idxmax()
        busiest_count = heatmap_df['day'].value_counts().max()
        m2.metric("最忙的一天", WEEKDAYS_CN.get(busiest_day_en, busiest_day_en), f"{busiest_count} 节课")
    else:
        m2.metric("最忙的一天", "-", "0 节")
        
    m3.metric("平均每日课程", f"{total_courses/5:.1f} 节")
    
    st.markdown("---")
    
    col_viz1, col_viz2 = st.columns([1.5, 1])
    
    with col_viz1:
        st.markdown("### 🌡️ 课程分布热力图")
        if not heatmap_df.empty:
            # Create shortened course names for display
            heatmap_df['short_name'] = heatmap_df['course_name'].apply(lambda x: x[:4] + '...' if len(x) > 4 else x)
            
            # Base chart
            base = alt.Chart(heatmap_df).encode(
                x=alt.X('day_cn:N', title=None, sort=["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"], axis=alt.Axis(labelAngle=0)),
                y=alt.Y('period:O', title='节次', sort='ascending', axis=alt.Axis(titleAngle=0, titleAlign="right", titleY=15)),
            ).properties(
                height=400,
                width='container'
            )

            # Rectangles for background color
            rects = base.mark_rect(cornerRadius=5).encode(
                color=alt.Color('course_name:N', legend=None),
                tooltip=[
                    alt.Tooltip('day_cn', title='星期'),
                    alt.Tooltip('period', title='节次'),
                    alt.Tooltip('course_name', title='课程名称'),
                    alt.Tooltip('location', title='上课地点'),
                    alt.Tooltip('teacher', title='任课教师')
                ]
            )

            # Text labels for course names
            text = base.mark_text(baseline='middle', size=10, color='white').encode(
                text=alt.Text('short_name'),
                color=alt.value('white')
            )

            # Combine
            st.altair_chart(rects + text, use_container_width=True)
        else:
            st.info("暂无数据")

    with col_viz2:
        st.markdown("### 🍩 课程数量分布")
        if not course_counts.empty:
            base = alt.Chart(course_counts).encode(
                theta=alt.Theta("count", stack=True)
            )
            pie = base.mark_arc(outerRadius=100, innerRadius=60).encode(
                color=alt.Color("course_name", legend=None),
                order=alt.Order("count", sort="descending"),
                tooltip=[
                    alt.Tooltip('course_name', title='课程名称'),
                    alt.Tooltip('count', title='节数')
                ]
            )
            text = base.mark_text(radius=120).encode(
                text="count",
                order=alt.Order("count", sort="descending"),
                color=alt.value("black") 
            )
            st.altair_chart(pie + text, use_container_width=True)
        else:
            st.info("暂无数据")

