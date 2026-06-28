import streamlit as st
import random
import time
import sqlite3
import os

# --- 页面配置 ---
st.set_page_config(page_title="校园情绪树洞", page_icon="🌱", layout="wide")

# --- 初始化全局数据（模拟数据库） ---
if "posts" not in st.session_state:
    st.session_state.posts = [
        {"id": 1, "tag": "学业压力", "content": "马上要期末考试了，好焦虑，感觉复习不完...", "time": "10分钟前", "replies": ["别慌！拆解成小目标，一步步来。加油！"]},
        {"id": 2, "tag": "人际关系", "content": "和室友因为作息问题有点小摩擦，不知道怎么开口沟通。", "time": "1小时前", "replies": ["可以试试写个便利贴，或者找个大家心情都不错的时候温和地聊聊。"]}
    ]

# --- 侧边栏导航 ---
st.sidebar.title("🌱 校园情绪树洞")
st.sidebar.write("这是一个安全的、匿名的心理互助空间。")
page = st.sidebar.radio("前往专区：", ["📬 匿名倾诉树洞", "🤝 志愿者互助站", "📝 心理趣味测试", "🎮 触觉解压小游戏"])

# ==================== 1. 匿名倾诉树洞 ====================
if page == "📬 匿名倾诉树洞":
    st.title("📬 匿名情绪树洞")
    st.caption("把烦恼留在这里，带走温暖和力量。你的身份将被完全保密。")
    
    # 发布新贴
    with st.form("new_post_form", clear_on_submit=True):
        tag = st.selectbox("选择情绪标签", ["学业压力", "人际关系", "情感困惑", "家庭烦恼", "日常碎碎念"])
        content = st.text_area("你想倾诉些什么？（请不要包含任何个人真实信息）", placeholder="今晚的月亮很美，但我的心情有点乌云密布...")
        submitted = st.form_submit_button("投递进树洞")
        
        if submitted and content.strip():
            new_post = {
                "id": len(st.session_state.posts) + 1,
                "tag": tag,
                "content": content,
                "time": "刚刚",
                "replies": []
            }
            st.session_state.posts.insert(0, new_post) # 新帖放在最前面
            st.success("倾诉成功，树洞已安全接收。")
            st.rerun()

    st.markdown("---")
    st.subheader("🍃 树洞里的呢喃")
    
    # 循环渲染帖子
    for post in st.session_state.posts:
        with st.container():
            st.markdown(f"**【{post['tag']}】** <span style='color:gray; font-size:12px;'>发布于 {post['time']}</span>", unsafe_allow_html=True)
            st.info(post['content'])
            
            # 显示回复
            if post['replies']:
                for reply in post['replies']:
                    st.markdown(f"💬 **志愿者/老师回复：** {reply}")
            else:
                st.caption("🌱 倾听中... 温暖的回复正在路上。")
            st.write("")

# ==================== 2. 志愿者互助站 ====================
elif page == "🤝 志愿者互助站":
    st.title("🤝 志愿者与心理老师互助端")
    st.caption("经培训的志愿者或心理老师可在此处查看同学们的匿名倾诉并提供支持。")
    
    if not st.session_state.posts:
        st.info("目前树洞里没有待处理的情绪哦，大家都很好！")
    else:
        for i, post in enumerate(st.session_state.posts):
            st.markdown(f"### 帖子 ID: #{post['id']} | 标签: `{post['tag']}`")
            st.warning(f"**同学倾诉：** {post['content']}")
            
            # 回复表单
            with st.form(f"reply_form_{post['id']}", clear_on_submit=True):
                reply_content = st.text_input("输入你的温暖回复：", placeholder="用温柔且坚定的语言给予力量...")
                submit_reply = st.form_submit_button("发送回复")
                
                if submit_reply and reply_content.strip():
                    post['replies'].append(reply_content)
                    st.success("回复已成功送达树洞！")
                    time.sleep(0.5)
                    st.rerun()
            st.markdown("---")

# ==================== 3. 心理趣味测试 ====================
elif page == "📝 心理趣味测试":
    st.title("📝 心理趣味测试")
    st.subheader("🔍 测测你今天的“精神内耗指数”")
    
    # 测试题目
    q1 = st.radio("1. 当别人没有及时回复你的微信时，你通常会：", 
                  ["A. 没想太多，可能他在忙", "B. 开始反思是不是自己上一句话说错了", "C. 感到焦虑或有些生气"])
    q2 = st.radio("2. 晚上躺在床上时，你脑海里经常会：", 
                  ["A. 很快入睡，不想太多", "B. 像放电影一样复盘今天尴尬或没做好的细节", "C. 焦虑明天还没发生的事情"])
    
    if st.button("查看测试结果"):
        # 简单计分逻辑
        score = 0
        for q in [q1, q2]:
            if "B" in q: score += 1
            elif "C" in q: score += 2
            
        st.markdown("### 📊 评估结果：")
        if score <= 1:
            st.success("🍃 **精神内耗指数：低。** 你拥有很棒的心理韧性，对生活中的小波折能够坦然面对，请继续保持这颗平常心！")
        elif score <= 3:
            st.warning("⛅ **精神内耗指数：中。** 你有时会陷入过度思考，试着在焦虑时做几次深呼吸，告诉自己‘过去的事情已经过去’。")
        else:
            st.error("🌪️ **精神内耗指数：高。** 你的大脑最近太累啦，装了太多的‘如果’和‘怎么办’。建议去操场走走，或者去【匿名树洞】把压力写出来吧。")

# ==================== 4. 🚀 多功能解压游戏厅 ====================
elif page == "🎮 触觉解压小游戏":
    st.title("🎮 校园专属解压游戏厅")
    st.caption("挑选一个你喜欢的方式，把积攒的压力全部释放掉吧！")
    
    # 在游戏页面内做个小标签页切换
    game_choice = st.tabs(["🟢 电子气泡膜", "🪵 赛博敲木鱼", "🧼 强迫症切肥皂"])
    
    # ---- 游戏一：电子气泡膜 ----
    with game_choice[0]:
        st.subheader("🟢 电子气泡膜")
        st.caption("生活太累？来捏碎这些电子气泡，捏成全黑就很治愈！")
        
        if "bubbles" not in st.session_state:
            st.session_state.bubbles = [True] * 24
            
        if st.button("🔄 刷新一整板新气泡", key="reset_bubbles"):
            st.session_state.bubbles = [True] * 24
            st.rerun()
            
        cols = st.columns(6)
        for idx, status in enumerate(st.session_state.bubbles):
            col = cols[idx % 6]
            if status:
                if col.button("🟢", key=f"bubble_{idx}"):
                    st.session_state.bubbles[idx] = False
                    st.rerun()
            else:
                col.button("⚫", key=f"bubble_{idx}", disabled=True)
                
        popped = st.session_state.bubbles.count(False)
        st.progress(popped / 24)
        st.write(f"你已经捏碎了 {popped} / 24 个气泡。")

    # ---- 游戏二：赛博敲木鱼 ----
    with game_choice[1]:
        st.subheader("🪵 赛博敲木鱼")
        st.caption("考试保过、告别焦虑、积攒功德。请戴上耳机，静心轻点。")
        
        # 初始化功德计数和动画文字
        if "merit" not in st.session_state:
            st.session_state.merit = 0
        if "wood_effect" not in st.session_state:
            st.session_state.wood_effect = ""
            
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # 模拟大木鱼按钮
            st.write("")
            if st.button("🔴\n\n  🪵  \n\n🔴", key="hit_wood", use_container_width=True):
                st.session_state.merit += 1
                # 随机飘出治愈文案
                blessings = ["功德 +1", "焦虑 -1", "好运 +1", "期末保过 +1", "水逆退散 +1"]
                st.session_state.wood_effect = random.choice(blessings)
                st.rerun()
                
        with col2:
            st.metric(label="🔮 当前累计功德/好运值", value=st.session_state.merit)
            if st.session_state.wood_effect:
                # 展现动态漂浮文字的效果
                st.markdown(f"### <span style='color:#FF4B4B; animation: pulse 0.5s;'>{st.session_state.wood_effect}</span>", unsafe_allow_html=True)
            else:
                st.write("点击左侧木鱼，开始静心...")
                
        if st.button("🔄 重置功德", key="reset_merit"):
            st.session_state.merit = 0
            st.session_state.wood_effect = ""
            st.rerun()

    # ---- 游戏三：强迫症切肥皂 ----
    with game_choice[2]:
        st.subheader("🧼 强迫症切肥皂")
        st.caption("咔嚓、咔嚓... 把肥皂均匀地切成薄片，强迫症的极致享受。")
        
        if "soap_slices" not in st.session_state:
            st.session_state.soap_slices = 0
            
        max_slices = 10 # 总共需要切10刀
        
        if st.session_state.soap_slices < max_slices:
            # 用彩色方块进度条模拟一块未切完的肥皂
            soap_visual = "🟩" * (max_slices - st.session_state.soap_slices) + "⬜" * st.session_state.soap_slices
            st.markdown(f"### 肥皂状态：{soap_visual}")
            
            if st.button("🔪 切下一片！", key="cut_soap", use_container_width=True):
                st.session_state.soap_slices += 1
                st.rerun()
        else:
            st.success("🎉 太爽快了！整块肥皂已被完美切片！")
            st.markdown("### 肥皂状态：⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ (已切完)")
            
        if st.button("🔄 拿出一块新肥皂", key="reset_soap"):
            st.session_state.soap_slices = 0
            st.rerun()
