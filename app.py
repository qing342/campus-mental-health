import streamlit as st
import sqlite3
import hashlib
from enum import Enum
from datetime import datetime
from datetime import datetime, timedelta

# ==================== 枚举 ====================
class UserRole(Enum):
    STUDENT = "学生"
    VOLUNTEER = "志愿者"
    TEACHER = "心理老师"

# ==================== 数据库管理器 ====================
class DatabaseManager:
    @staticmethod
    @st.cache_resource
    def get_connection():
        conn = sqlite3.connect('emotional_tree.db')
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def init_db():
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 创建帖子表
        cursor.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        
        # 创建回复表
        cursor.execute('''CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        
        conn.commit()
        
        # 初始化演示用户
        DatabaseManager._init_demo_users()

    @staticmethod
    def _init_demo_users():
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        demo_users = [
            ("student1", "123456", UserRole.STUDENT.value),
            ("volunteer1", "123456", UserRole.VOLUNTEER.value),
            ("teacher1", "123456", UserRole.TEACHER.value)
        ]
        
        for username, password, role in demo_users:
            try:
                hashed_password = DatabaseManager.hash_password(password)
                cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                             (username, hashed_password, role))
            except sqlite3.IntegrityError:
                pass  # 用户已存在
        
        conn.commit()

    @staticmethod
    def authenticate_user(username, password):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        hashed_password = DatabaseManager.hash_password(password)
        
        cursor.execute('SELECT id, username, role FROM users WHERE username = ? AND password = ?',
                      (username, hashed_password))
        user = cursor.fetchone()
        
        if user:
            return dict(user)
        return None

    @staticmethod
    def register_user(username, password, role):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        hashed_password = DatabaseManager.hash_password(password)
        
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                         (username, hashed_password, role))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

# ==================== 帖子管理器 ====================
class PostManager:
    @staticmethod
    def get_posts(limit=50):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        cursor.execute('''SELECT posts.id, posts.user_id, posts.tag, posts.content, 
                         posts.created_at, users.role FROM posts 
                         JOIN users ON posts.user_id = users.id 
                         ORDER BY posts.created_at DESC LIMIT ?''', (limit,))
        return cursor.fetchall()

    @staticmethod
    def add_post(user_id, tag, content):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO posts (user_id, tag, content) VALUES (?, ?, ?)',
                      (user_id, tag, content))
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def get_post_replies(post_id):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        cursor.execute('''SELECT replies.content, users.role FROM replies 
                         JOIN users ON replies.user_id = users.id 
                         WHERE replies.post_id = ? ORDER BY replies.created_at''', (post_id,))
        return cursor.fetchall()

    @staticmethod
    def add_reply(post_id, user_id, content):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO replies (post_id, user_id, content) VALUES (?, ?, ?)',
                      (post_id, user_id, content))
        conn.commit()

# ==================== UI助手 ====================
class UIHelper:
    @staticmethod
    def get_time_display(created_at):
        try:
            post_time = datetime.fromisoformat(created_at)
            now = datetime.now()
            diff = now - post_time
            
            if diff.total_seconds() < 60:
                return "刚刚"
            elif diff.total_seconds() < 3600:
                return f"{int(diff.total_seconds() / 60)}分钟前"
            elif diff.total_seconds() < 86400:
                return f"{int(diff.total_seconds() / 3600)}小时前"
            else:
                return f"{int(diff.total_seconds() / 86400)}天前"
        except:
            return "未知时间"

# ==================== 初始化Session State ====================
if 'user' not in st.session_state:
    st.session_state.user = None
if 'bubbles' not in st.session_state:
    st.session_state.bubbles = [True] * 24
if 'merit' not in st.session_state:
    st.session_state.merit = 0
if 'wood_effect' not in st.session_state:
    st.session_state.wood_effect = ""
if 'soap_slices' not in st.session_state:
    st.session_state.soap_slices = 0

# 初始化数据库
DatabaseManager.init_db()

# ==================== 登录页面 ====================
def show_login_page():
    st.set_page_config(page_title="情绪树洞", layout="wide", initial_sidebar_state="collapsed")
    
    col1, col2, col3 = st.columns(3)
    with col2:
        st.title("🌿 校园情绪树洞")
        st.caption("安全倾诉 · 温暖互助 · 减压游戏")
        
        tab1, tab2 = st.tabs(["🔓 登录", "📝 注册"])
        
        # 登录选项卡
        with tab1:
            st.subheader("登录你的账号")
            with st.form("login_form"):
                username = st.text_input("用户名")
                password = st.text_input("密码", type="password")
                login_button = st.form_submit_button("登录")
            
            if login_button:
                if username and password:
                    user = DatabaseManager.authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.success(f"欢迎回来，{user['username']}！")
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
                else:
                    st.warning("请输入用户名和密码")
        
        # 注册选项卡
        with tab2:
            st.subheader("创建新账号")
            with st.form("register_form"):
                new_username = st.text_input("创建用户名", key="reg_username")
                new_password = st.text_input("创建密码", type="password", key="reg_password")
                confirm_password = st.text_input("确认密码", type="password")
                role = st.selectbox("选择身份", [UserRole.STUDENT.value, UserRole.VOLUNTEER.value, UserRole.TEACHER.value])
                register_button = st.form_submit_button("注册")
            
            if register_button:
                if not new_username or not new_password or not confirm_password:
                    st.warning("请填写所有字段")
                elif new_password != confirm_password:
                    st.error("两次密码输入不一致")
                elif len(new_password) < 6:
                    st.error("密码长度至少6位")
                else:
                    if DatabaseManager.register_user(new_username, new_password, role):
                        st.success(f"注册成功！请使用 {new_username} 登录")
                    else:
                        st.error("用户名已存在")
        
        st.divider()
        st.markdown("""
        **🎭 演示账号：**
        - 学生：student1 / 123456
        - 志愿者：volunteer1 / 123456
        - 心理老师：teacher1 / 123456
        """)

# ==================== 主应用页面 ====================
def show_main_app():
    st.set_page_config(page_title="情绪树洞", layout="wide")
    
    # 侧边栏
    with st.sidebar:
        st.title("🌿 情绪树洞")
        st.write(f"👤 已登录：**{st.session_state.user['username']}**")
        st.write(f"🎭 身份：{st.session_state.user['role']}")
        
        page = st.radio("选择功能", 
                       ["📬 匿名倾诉树洞", "🤝 志愿者互助站", "📝 心理趣味测试", "🎮 触觉解压小游戏"])
        
        if st.button("🚪 退出登录"):
            st.session_state.user = None
            st.rerun()
    
    # ==================== 1. 匿名倾诉树洞 ====================
    if page == "📬 匿名倾诉树洞":
        st.title("📬 匿名情绪树洞")
        st.caption("把烦恼留在这里，带走温暖和力量。你的身份将被完全保密。")
        
        # 发布新贴
        with st.form("new_post_form", clear_on_submit=True):
            tag = st.selectbox("选择情绪标签", ["学业压力", "人际关系", "情感困惑", "家庭烦恼", "日常碎碎念"])
            content = st.text_area("你想倾诉些什么？", placeholder="今晚的月亮很美，但我的心情有点乌云密布...")
            submitted = st.form_submit_button("投递进树洞")
        
        if submitted and content.strip():
            PostManager.add_post(st.session_state.user['id'], tag, content)
            st.success("倾诉成功，树洞已安全接收。")
            st.rerun()
        
        st.markdown("---")
        st.subheader("🍃 树洞里的呢喃")
        
        posts = PostManager.get_posts()
        if not posts:
            st.info("树洞里暂时很宁静，去分享你的故事吧。")
        else:
            for post in posts:
                with st.container():
                    time_display = UIHelper.get_time_display(post['created_at'])
                    st.markdown(f"**【{post['tag']}】** <span style='color:gray; font-size:12px;'>发布于 {time_display}</span>", 
                              unsafe_allow_html=True)
                    st.info(post['content'])
                    
                    replies = PostManager.get_post_replies(post['id'])
                    if replies:
                        for reply in replies:
                            st.markdown(f"💬 **[{reply['role']}] 回复：** {reply['content']}")
                    else:
                        st.caption("🌱 倾听中... 温暖的回复正在路上。")
                    st.write("")
    
    # ==================== 2. 志愿者互助站 ====================
    elif page == "🤝 志愿者互助站":
        if st.session_state.user['role'] not in [UserRole.VOLUNTEER.value, UserRole.TEACHER.value]:
            st.warning("⛔ 您需要志愿者或心理老师身份才能访问此功能")
            return
        
        st.title("🤝 志愿者与心理老师互助端")
        st.caption("经培训的志愿者或心理老师可在此处查看同学们的匿名倾诉并提供支持。")
        
        posts = PostManager.get_posts()
        if not posts:
            st.info("暂时没有新的倾诉")
        else:
            for post in posts:
                with st.container():
                    time_display = UIHelper.get_time_display(post['created_at'])
                    st.markdown(f"**【{post['tag']}】** <span style='color:gray; font-size:12px;'>发布于 {time_display}</span>", 
                              unsafe_allow_html=True)
                    st.info(post['content'])
                    
                    # 提交回复
                    with st.form(f"reply_form_{post['id']}"):
                        reply_content = st.text_area("写下你的温暖回复...", key=f"reply_{post['id']}", height=80)
                        submitted = st.form_submit_button("提交回复")
                    
                    if submitted and reply_content.strip():
                        PostManager.add_reply(post['id'], st.session_state.user['id'], reply_content)
                        st.success("回复已提交")
                        st.rerun()
                    
                    # 显示现有回复
                    replies = PostManager.get_post_replies(post['id'])
                    if replies:
                        st.markdown("**已有的回复：**")
                        for reply in replies:
                            st.markdown(f"💬 **[{reply['role']}]** {reply['content']}")
                    st.write("")
    
    # ==================== 3. 心理趣味测试 ====================
    elif page == "📝 心理趣味测试":
        st.title("📝 测测你的精神内耗指数")
        st.caption("这是一个简单的自测工具，可以帮助你了解自己的压力状态。结果仅供参考。")
        
        st.subheader("🔍 测测你今天的'精神内耗指数'")
        
        q1_score = st.radio("问题1️⃣ ：你今天觉得身体疲劳吗？", 
                          options=[("一点都不 (0分)", 0), ("有点疲劳 (1分)", 1), ("很疲劳 (2分)", 2)],
                          format_func=lambda x: x[0])
        
        q2_score = st.radio("问题2️⃣ ：你对今天的学习/工作产出满意吗？", 
                          options=[("非常满意 (0分)", 0), ("一般 (1分)", 1), ("不太满意 (2分)", 2)],
                          format_func=lambda x: x[0])
        
        if st.button("📊 查看测试结果"):
            total_score = q1_score + q2_score
            
            if total_score <= 1:
                st.success("💚 **精神内耗指数：低。** 你今天状态很棒，继续保持！")
            elif total_score <= 3:
                st.warning("⛅ **精神内耗指数：中。** 试着在焦虑时做几次深呼吸。")
            else:
                st.error("🌪️ **精神内耗指数：高。** 建议去操场走走，或去树洞倾诉。")
    
    # ==================== 4. 触觉解压小游戏 ====================
    elif page == "🎮 触觉解压小游戏":
        st.title("🎮 触觉解压小游戏")
        st.caption("在这里放松心情，用互动游戏释放压力。")
        
        game_tab1, game_tab2, game_tab3 = st.tabs(["🟢 气泡破裂", "🪵 木鱼点击", "🧼 肥皂切割"])
        
        # 气泡破裂游戏
        with game_tab1:
            st.subheader("🟢 气泡破裂游戏")
            st.caption("点击所有气泡，全部消灭！")
            
            cols = st.columns(6)
            for i in range(24):
                with cols[i % 6]:
                    if st.button("○", key=f"bubble_{i}", use_container_width=True):
                        st.session_state.bubbles[i] = False
            
            progress = (24 - sum(st.session_state.bubbles)) / 24
            st.progress(progress)
            st.caption(f"已破裂：{24 - sum(st.session_state.bubbles)}/24")
            
            if progress == 1.0:
                st.balloons()
                st.success("🎉 太棒了！所有气泡都破裂了！")
        
        # 木鱼点击
        with game_tab2:
            st.subheader("🪵 木鱼点击游戏")
            st.caption("点击木鱼，积累功德！")
            
            col1, col2, col3 = st.columns(3)
            with col2:
                if st.button("🪵", key="wood_fish", use_container_width=True):
                    st.session_state.merit += 1
                    st.session_state.wood_effect = ["功德+1", "阿弥陀佛", "南无阿弥陀佛", "善哉善哉"][st.session_state.merit % 4]
            
            st.metric("累积功德", st.session_state.merit)
            if st.session_state.wood_effect:
                st.markdown(f"<h1 style='text-align: center; color: gold;'>{st.session_state.wood_effect}</h1>", 
                          unsafe_allow_html=True)
        
        # 肥皂切割
        with game_tab3:
            st.subheader("🧼 肥皂切割游戏")
            st.caption("点击切割肥皂，完成10次切割！")
            
            if st.button("🔪 切一刀", key="soap_cut", use_container_width=True):
                st.session_state.soap_slices += 1
            
            soap_progress = min(st.session_state.soap_slices / 10, 1.0)
            st.progress(soap_progress)
            
            if st.session_state.soap_slices >= 10:
                st.markdown("### 🧼 肥皂状态：✨✨✨✨✨ (已切完)")
                st.success("🎉 肥皂已完全切碎！")
            else:
                slices_display = "✨" * st.session_state.soap_slices + "🧼" * (10 - st.session_state.soap_slices)
                st.markdown(f"### 🧼 肥皂状态：{slices_display} (已切{st.session_state.soap_slices}刀)")
            
            if st.button("🔄 重置肥皂", key="reset_soap"):
                st.session_state.soap_slices = 0
                st.rerun()

# ==================== 主入口 ====================
if st.session_state.user:
    show_main_app()
else:
    show_login_page()
