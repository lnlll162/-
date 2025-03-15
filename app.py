import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import hashlib
import json
import os
import time
from io import BytesIO
from dotenv import load_dotenv
import secrets
import logging
import requests
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional

# 国际化支持
LANGUAGES = {
    "中文": {
        "title": "5A智慧学习空间数据大屏",
        "login": "登录",
        "username": "用户名",
        "password": "密码",
        "logout": "注销",
        "register": "注册",
        "reset_password": "重置密码",
        "dashboard": "数据大屏",
        "data_analysis": "数据分析",
        "settings": "设置"
    },
    "English": {
        "title": "5A Smart Learning Space Dashboard",
        "login": "Login",
        "username": "Username",
        "password": "Password",
        "logout": "Logout",
        "register": "Register",
        "reset_password": "Reset Password",
        "dashboard": "Dashboard",
        "data_analysis": "Analysis",
        "settings": "Settings"
    }
}

def get_text(key):
    lang = st.session_state.get("language", "中文")
    return LANGUAGES[lang][key]

# 页面配置
st.set_page_config(
    page_title="5A智慧学习空间数据大屏",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://your-help-url',
        'Report a bug': "https://your-bug-report-url",
        'About': "# 5A智慧学习空间数据大屏\n 基于'5A'智慧学习范式的未来学习空间分析与可视化平台"
    }
)

# 添加环境变量支持
load_dotenv()

# 数据库配置（替换本地JSON文件）
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data.db')

# 自定义CSS样式
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: rgba(28, 131, 225, 0.1);
        border-radius: 10px;
        padding: 1rem;
    }
    .stMetric:hover {
        background-color: rgba(28, 131, 225, 0.2);
        transition: all 0.3s ease;
    }
    .st-emotion-cache-1wivap2 {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    h1, h2, h3 {
        color: #1E88E5;
        padding-top: 1rem;
    }
    .stProgress .st-emotion-cache-1c7u2d8 {
        background-color: #1E88E5;
    }
    .title {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
        font-weight: bold;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# 添加主标题和副标题
st.markdown("""
<div class="title">5A智慧学习空间数据大屏</div>
<div class="subtitle">基于"5A"智慧学习范式的未来学习空间分析与可视化</div>
""", unsafe_allow_html=True)

# 配置日志
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def log_activity(user_id, action, details=None):
    """记录用户活动"""
    logging.info(f"User {user_id} - {action} - {details}")

# 用户认证配置
class AuthConfig:
    def __init__(self):
        self.users_file = "users.json"
        self.init_users()
        self.max_login_attempts = 5
        self.lockout_time = 30  # 锁定时间（分钟）
    
    def init_users(self):
        # 如果用户文件不存在，创建默认用户
        if not os.path.exists(self.users_file):
            default_users = {
                "admin": self.hash_password("admin123"),
                "user": self.hash_password("user123")
            }
            with open(self.users_file, "w") as f:
                json.dump(default_users, f)
    
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, username, password):
        try:
            with open(self.users_file, "r") as f:
                users = json.load(f)
            return username in users and users[username] == self.hash_password(password)
        except:
            return False
    
    def add_user(self, username, password):
        """添加新用户"""
        try:
            with open(self.users_file, "r") as f:
                users = json.load(f)
            if username in users:
                return False, "用户名已存在"
            users[username] = self.hash_password(password)
            with open(self.users_file, "w") as f:
                json.dump(users, f)
            return True, "注册成功"
        except:
            return False, "系统错误"
    
    def change_password(self, username, old_password, new_password):
        """修改用户密码"""
        try:
            if not self.verify_user(username, old_password):
                return False, "原密码错误"
            with open(self.users_file, "r") as f:
                users = json.load(f)
            users[username] = self.hash_password(new_password)
            with open(self.users_file, "w") as f:
                json.dump(users, f)
            return True, "密码修改成功"
        except:
            return False, "系统错误"
    
    def reset_password(self, username, verification_code, new_password):
        """重置密码（示例实现，实际应该配合邮箱或手机验证）"""
        try:
            # 这里应该验证重置码，这里简化处理
            if verification_code != "123456":  # 示例验证码
                return False, "验证码错误"
            with open(self.users_file, "r") as f:
                users = json.load(f)
            if username not in users:
                return False, "用户不存在"
            users[username] = self.hash_password(new_password)
            with open(self.users_file, "w") as f:
                json.dump(users, f)
            return True, "密码重置成功"
        except:
            return False, "系统错误"

# 登录页面
def login_page():
    st.title("智慧学习空间数据大屏 - 登录")
    
    with st.form("login_form"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        col1, col2 = st.columns(2)
        submit = col1.form_submit_button("登录")
        
        if submit:
            auth_config = AuthConfig()
            if auth_config.verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("用户名或密码错误")
    
    # 添加注册和重置密码链接
    col1, col2 = st.columns(2)
    if col1.button("注册新用户"):
        st.session_state.page = "register"
        st.rerun()
    if col2.button("忘记密码"):
        st.session_state.page = "reset"
        st.rerun()

# 添加注销功能
def logout():
    if st.sidebar.button("注销"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# 增强的数据模拟类
class AdvancedDataSimulator:
    # 校内空间类型
    INDOOR_SPACES = {
        'traditional': '传统学习空间',
        'leisure': '休闲学习空间',
        'skill': '技能学习空间',
        'collaborative': '协作学习空间',
        'personal': '个性学习空间',
        'innovation': '创新学习空间',
        'exhibition': '展演学习空间'
    }
    
    # 校外空间类型
    OUTDOOR_SPACES = {
        'community': '社区学习空间',
        'family': '家庭学习空间',
        'park': '公园学习空间',
        'transportation': '交通枢纽学习空间',
        'enterprise': '企业实践空间',
        'museum': '博物馆学习空间'
    }
    
    @staticmethod
    def generate_space_usage():
        """生成空间使用数据"""
        all_spaces = {**AdvancedDataSimulator.INDOOR_SPACES, 
                     **AdvancedDataSimulator.OUTDOOR_SPACES}
        
        data = {
            'space_id': list(all_spaces.keys()),
            'space_name': list(all_spaces.values()),
            'space_type': ['校内' if k in AdvancedDataSimulator.INDOOR_SPACES else '校外' 
                          for k in all_spaces.keys()],
            'current_users': [random.randint(10, 100) for _ in all_spaces],
            'capacity': [random.randint(50, 200) for _ in all_spaces],
            'utilization': [random.uniform(0.3, 0.9) for _ in all_spaces],
            'satisfaction': [random.uniform(3.5, 5.0) for _ in all_spaces]
        }
        return pd.DataFrame(data)
    
    @staticmethod
    def generate_learning_activities():
        """生成学习活动数据"""
        activities = {
            '实践学习': random.uniform(0, 100),
            '团队协作': random.uniform(0, 100),
            '创新实验': random.uniform(0, 100),
            '技能培训': random.uniform(0, 100),
            '成果展示': random.uniform(0, 100),
            '社区互动': random.uniform(0, 100)
        }
        return activities

# 3D空间可视化
def render_3d_space():
    # 模拟3D空间数据
    x = np.linspace(-5, 5, 20)
    y = np.linspace(-5, 5, 20)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(np.sqrt(X**2 + Y**2))
    
    fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y)])
    fig.update_layout(
        title='空间数字孪生可视化',
        scene = dict(
            xaxis_title='X轴',
            yaxis_title='Y轴',
            zaxis_title='Z轴'
        ),
        height=400
    )
    return fig

# 热力图可视化
def render_heatmap():
    # 模拟人流热力图数据
    x = np.linspace(0, 10, 20)
    y = np.linspace(0, 10, 20)
    z = np.random.rand(20, 20)
    
    fig = go.Figure(data=go.Heatmap(z=z))
    fig.update_layout(
        title='人流热力图',
        height=300
    )
    return fig

# 实时监控面板
def render_monitoring_panel():
    env_data = AdvancedDataSimulator.generate_space_usage().iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("空间名称", env_data['space_name'])
    with col2:
        st.metric("空间类型", env_data['space_type'])
    with col3:
        st.metric("当前使用人数", f"{env_data['current_users']}人")
    with col4:
        st.metric("空间利用率", f"{env_data['utilization']:.1f}")

# 学习分析面板
def render_learning_analytics():
    """学习分析可视化"""
    # 创建学习分析数据
    analytics_data = {
        '认知负荷': [random.uniform(0.3, 0.8) for _ in range(24)],
        '学习投入度': [random.uniform(0.4, 0.9) for _ in range(24)],
        '知识掌握': [random.uniform(0.5, 0.95) for _ in range(24)],
        '时间': [f"{i:02d}:00" for i in range(24)]
    }
    df = pd.DataFrame(analytics_data)
    
    fig = go.Figure()
    
    # 添加多个指标线
    for col in ['认知负荷', '学习投入度', '知识掌握']:
        fig.add_trace(go.Scatter(
            x=df['时间'],
            y=df[col],
            name=col,
            mode='lines+markers'
        ))
    
    fig.update_layout(
        title='学习效果实时分析',
        xaxis_title='时间',
        yaxis_title='指标值',
        height=400,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig

# 智能预警系统
def render_alert_system():
    alerts = [
        {"type": "环境", "message": "空间利用率偏高", "level": "警告"},
        {"type": "设备", "message": "空间满意度偏低", "level": "警告"},
        {"type": "行为", "message": "学习疲劳预警", "level": "提示"}
    ]
    
    for alert in alerts:
        if alert["level"] == "错误":
            st.error(f"{alert['type']}: {alert['message']}")
        elif alert["level"] == "警告":
            st.warning(f"{alert['type']}: {alert['message']}")
        else:
            st.info(f"{alert['type']}: {alert['message']}")

# 趋势分析图表
def render_trend_analysis():
    """学习趋势分析"""
    # 生成趋势数据
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    trend_data = {
        '日期': dates,
        '物理空间使用率': [random.uniform(0.4, 0.9) for _ in range(30)],
        '虚拟空间活跃度': [random.uniform(0.5, 0.95) for _ in range(30)],
        '学习效果评分': [random.uniform(3.5, 4.8) for _ in range(30)]
    }
    df = pd.DataFrame(trend_data)
    
    # 创建多指标趋势图
    fig = go.Figure()
    
    # 添加物理空间使用率
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['物理空间使用率'],
        name='物理空间使用率',
        mode='lines+markers',
        line=dict(width=2, color='#1E88E5')
    ))
    
    # 添加虚拟空间活跃度
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['虚拟空间活跃度'],
        name='虚拟空间活跃度',
        mode='lines+markers',
        line=dict(width=2, color='#FFC107')
    ))
    
    # 添加学习效果评分
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['学习效果评分'],
        name='学习效果评分',
        mode='lines+markers',
        line=dict(width=2, color='#4CAF50'),
        yaxis='y2'
    ))
    
    # 更新布局
    fig.update_layout(
        title='学习空间使用趋势分析',
        xaxis=dict(title='日期'),
        yaxis=dict(
            title='使用率/活跃度',
            tickfont=dict(color='#1E88E5'),
            title_font=dict(color='#1E88E5'),
            range=[0, 1]
        ),
        yaxis2=dict(
            title='学习效果评分',
            tickfont=dict(color='#4CAF50'),
            title_font=dict(color='#4CAF50'),
            overlaying='y',
            side='right',
            range=[0, 5]
        ),
        height=400,
        margin=dict(t=50, l=25, r=25, b=25),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    return fig

# 注册页面
def register_page():
    st.title("用户注册")
    
    with st.form("register_form"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        confirm_password = st.text_input("确认密码", type="password")
        submit = st.form_submit_button("注册")
        
        if submit:
            if not username or not password:
                st.error("用户名和密码不能为空")
            elif password != confirm_password:
                st.error("两次输入的密码不一致")
            else:
                auth_config = AuthConfig()
                success, message = auth_config.add_user(username, password)
                if success:
                    st.success(message)
                    st.info("3秒后跳转到登录页面...")
                    time.sleep(3)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(message)

# 修改密码页面
def change_password_page():
    st.title("系统设置")
    
    # 使用更美观的标签页
    tabs = st.tabs(["👤 账户设置", "🔑 API配置", "📊 使用统计"])
    
    with tabs[0]:
        st.subheader("修改密码")
        with st.form("change_password_form"):
            old_password = st.text_input("原密码", type="password")
            new_password = st.text_input("新密码", type="password")
            confirm_password = st.text_input("确认新密码", type="password")
            submit = st.form_submit_button("修改密码", use_container_width=True)
            
            if submit:
                if new_password != confirm_password:
                    st.error("两次输入的新密码不一致")
                else:
                    auth_config = AuthConfig()
                    success, message = auth_config.change_password(
                        st.session_state.username, 
                        old_password, 
                        new_password
                    )
                    if success:
                        st.success(message)
                        st.info("3秒后需要重新登录...")
                        time.sleep(3)
                        for key in st.session_state.keys():
                            del st.session_state[key]
                        st.rerun()
                    else:
                        st.error(message)
    
    with tabs[1]:
        st.subheader("DeepSeek API配置")
        
        # 显示当前API状态
        current_api_key = os.getenv('DEEPSEEK_API_KEY', '')
        if not current_api_key and 'deepseek_api_key' in st.session_state:
            current_api_key = st.session_state.deepseek_api_key
            
        # 使用更美观的状态卡片
        if current_api_key:
            st.markdown("""
            <div style='background-color: #d4edda; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 5px solid #28a745;'>
                <h5 style='margin:0; color: #28a745;'>API状态: 已配置</h5>
            </div>
            """, unsafe_allow_html=True)
            
            # 显示密钥的部分内容
            masked_key = current_api_key[:4] + "*" * (len(current_api_key) - 8) + current_api_key[-4:]
            st.info(f"当前API密钥: {masked_key}")
        else:
            st.markdown("""
            <div style='background-color: #fff3cd; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 5px solid #ffc107;'>
                <h5 style='margin:0; color: #856404;'>API状态: 未配置</h5>
            </div>
            """, unsafe_allow_html=True)
        
        with st.form("api_settings_form"):
            deepseek_api_key = st.text_input(
                "DeepSeek API密钥", 
                value="",
                type="password",
                placeholder="请输入您的DeepSeek API密钥"
            )
            
            # 添加API基础URL配置
            deepseek_api_base = st.text_input(
                "API基础URL",
                value="https://api.deepseek.com",
                placeholder="例如: https://api.deepseek.com"
            )
            
            deepseek_model = st.selectbox(
                "DeepSeek模型",
                ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
                index=0
            )
            
            # 使用更美观的按钮布局
            col1, col2 = st.columns(2)
            with col1:
                submit_api = st.form_submit_button("保存API设置", use_container_width=True)
            with col2:
                test_api = st.form_submit_button("测试API连接", use_container_width=True)
            
            if submit_api and deepseek_api_key:
                # 保存到会话状态
                st.session_state.deepseek_api_key = deepseek_api_key
                st.session_state.deepseek_api_base = deepseek_api_base
                # 保存到环境变量
                os.environ['DEEPSEEK_API_KEY'] = deepseek_api_key
                os.environ['DEEPSEEK_API_BASE'] = deepseek_api_base
                os.environ['DEEPSEEK_MODEL'] = deepseek_model
                st.success("API设置已保存")
                
                # 测试API连接
                with st.spinner("正在测试API连接..."):
                    test_ai = DeepSeekAI()
                    test_response = test_ai.sync_generate_response(
                        [{"role": "user", "content": "Hello"}],
                        max_tokens=10
                    )
                    
                    if "error" in test_response:
                        st.error(f"API测试失败: {test_response['error']}")
                        st.error(f"详细信息: {test_response.get('details', '无详细信息')}")
                    else:
                        st.success("API连接测试成功!")
            
            if test_api:
                with st.spinner("正在测试API连接..."):
                    test_ai = DeepSeekAI()
                    test_response = test_ai.sync_generate_response(
                        [{"role": "user", "content": "Hello"}],
                        max_tokens=10
                    )
                    
                    if "error" in test_response:
                        st.error(f"API测试失败: {test_response['error']}")
                        st.error(f"详细信息: {test_response.get('details', '无详细信息')}")
                    else:
                        st.success("API连接测试成功!")
    
    with tabs[2]:
        st.subheader("API使用统计")
        
        # 显示API使用统计
        if 'api_usage' in st.session_state:
            usage = st.session_state.api_usage
            
            # 使用更美观的指标卡片
            cols = st.columns(3)
            with cols[0]:
                st.metric("API调用次数", usage['calls'])
            with cols[1]:
                st.metric("使用令牌数", usage['tokens'])
            with cols[2]:
                if usage['last_call']:
                    st.metric("上次调用时间", usage['last_call'].strftime('%H:%M:%S'))
            
            # 添加使用趋势图表
            if usage['calls'] > 0:
                # 这里可以添加一个使用趋势图表，如果有历史数据的话
                st.info("API使用趋势图将在未来版本中提供")
        else:
            st.info("暂无API使用记录")
        
        # 添加清除统计按钮
        if st.button("清除使用统计"):
            if 'api_usage' in st.session_state:
                del st.session_state.api_usage
                st.success("使用统计已清除")
                st.rerun()

# 重置密码页面
def reset_password_page():
    st.title("重置密码")
    
    with st.form("reset_password_form"):
        username = st.text_input("用户名")
        verification_code = st.text_input("验证码")
        st.info("演示版本：验证码为123456")
        new_password = st.text_input("新密码", type="password")
        confirm_password = st.text_input("确认新密码", type="password")
        submit = st.form_submit_button("重置")
        
        if submit:
            if new_password != confirm_password:
                st.error("两次输入的新密码不一致")
            else:
                auth_config = AuthConfig()
                success, message = auth_config.reset_password(
                    username,
                    verification_code,
                    new_password
                )
                if success:
                    st.success(message)
                    st.info("3秒后跳转到登录页面...")
                    time.sleep(3)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(message)

# 添加新的可视化函数
def render_learning_behavior_radar():
    """学习行为雷达图"""
    # 创建学习行为数据
    categories = ['知识获取', '技能训练', '互动交流', '实践应用', '评估反馈']
    values = [random.uniform(60, 100) for _ in range(5)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='学习行为分布'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        title='学习行为分析',
        height=400,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig

def render_device_status_table():
    """设备状态表格"""
    df = AdvancedDataSimulator.generate_space_usage()
    return df

def render_space_efficiency_heatmap():
    """空间效率热力图"""
    # 创建时间和空间类型数据
    hours = list(range(8, 22))  # 8:00 - 21:00
    space_types = ['传统学习', '休闲学习', '技能学习', '协作学习', 
                  '个性学习', '创新学习', '展演学习']
    
    # 生成使用率数据
    utilization_data = np.random.uniform(0.2, 0.9, size=(len(space_types), len(hours)))
    
    fig = go.Figure(data=go.Heatmap(
        z=utilization_data,
        x=[f"{hour}:00" for hour in hours],
        y=space_types,
        colorscale='RdYlGn',
        colorbar=dict(title='使用率')
    ))
    
    fig.update_layout(
        title='空间使用效率分析',
        xaxis_title='时间',
        yaxis_title='空间类型',
        height=400,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig

# 性能优化：添加缓存装饰器
@st.cache_data(ttl=300)  # 缓存5分钟
def cached_space_usage():
    """缓存空间使用数据"""
    return AdvancedDataSimulator.generate_space_usage()

@st.cache_data(ttl=60)  # 缓存1分钟
def cached_environment_data():
    return AdvancedDataSimulator.generate_space_usage().iloc[0]

# 错误处理装饰器
def safe_data_operation(func):
    def wrapper(*args, **kwargs):
        try:
            with st.spinner("处理中..."):
                return func(*args, **kwargs)
        except Exception as e:
            st.error(f"操作失败: {str(e)}")
            return None
    return wrapper

# 增强的数据导出功能
@safe_data_operation
def export_data():
    export_format = st.selectbox(
        "选择导出格式",
        ["CSV", "Excel", "JSON"]
    )
    
    data_types = st.multiselect(
        "选择要导出的数据",
        ["环境数据", "使用数据", "设备状态", "学习行为"],
        default=["环境数据"]
    )
    
    if st.button("导出数据"):
        data = {}
        if "环境数据" in data_types:
            data["环境数据"] = cached_environment_data()
        if "使用数据" in data_types:
            data["使用数据"] = cached_space_usage().to_dict()
        if "设备状态" in data_types:
            data["设备状态"] = AdvancedDataSimulator.generate_space_usage().iloc[0].to_dict()
        if "学习行为" in data_types:
            data["学习行为"] = AdvancedDataSimulator.generate_learning_activities()
        
        if export_format == "CSV":
            df = pd.DataFrame(data)
            csv = df.to_csv().encode('utf-8')
            st.download_button(
                label="下载CSV",
                data=csv,
                file_name=f"learning_space_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        elif export_format == "Excel":
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for sheet_name, sheet_data in data.items():
                    pd.DataFrame(sheet_data).to_excel(writer, sheet_name=sheet_name)
            st.download_button(
                label="下载Excel",
                data=output.getvalue(),
                file_name=f"learning_space_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.download_button(
                label="下载JSON",
                data=json.dumps(data, ensure_ascii=False, indent=2),
                file_name=f"learning_space_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# 学习空间数据模型
class LearningSpaceModel:
    # 物理学习空间
    PHYSICAL_SPACES = {
        'indoor': {  # 校内
            'traditional': {
                'name': '传统学习空间',
                'description': '标准教室、图书馆等传统学习场所'
            },
            'leisure': {
                'name': '休闲学习空间',
                'description': '激发学习兴趣的轻松环境'
            },
            'skill': {
                'name': '技能学习空间',
                'description': '实践试错、提升技能的专业场所'
            },
            'collaborative': {
                'name': '协作学习空间',
                'description': '培养团队协作精神的开放空间'
            },
            'personal': {
                'name': '个性学习空间',
                'description': '挖掘潜力特长的个性化空间'
            },
            'innovation': {
                'name': '创新学习空间',
                'description': '促进创新发展的实验空间'
            },
            'exhibition': {
                'name': '展演学习空间',
                'description': '展示成果、收获成就感的平台'
            }
        },
        'outdoor': {  # 校外
            'community': {
                'name': '社区学习空间',
                'description': '社区教育资源与设施'
            },
            'family': {
                'name': '家庭学习空间',
                'description': '家庭学习环境'
            },
            'enterprise': {
                'name': '企业实践空间',
                'description': '企业实习与培训场所'
            },
            'museum': {
                'name': '博物馆学习空间',
                'description': '博物馆教育资源'
            },
            'park': {
                'name': '公园学习空间',
                'description': '公共开放学习场所'
            }
        }
    }
    
    # 虚拟学习空间
    VIRTUAL_SPACES = {
        'data_layer': {  # 数据层
            'knowledge': {
                'name': '知识类数据',
                'content_count': random.randint(1000, 5000),
                'update_frequency': random.randint(1, 24)
            },
            'interaction': {
                'name': '交互数据',
                'active_users': random.randint(100, 1000),
                'avg_duration': random.uniform(0.5, 3.0)
            },
            'training': {
                'name': '训练数据',
                'completion_rate': random.uniform(60, 95),
                'satisfaction': random.uniform(4.0, 5.0)
            }
        },
        'application_layer': {  # 应用层
            'knowledge_present': {
                'name': '知识呈现',
                'features': ['宏观微观展示', '跨时空体验', '场景模拟']
            },
            'simulation': {
                'name': '模拟训练',
                'features': ['技能训练', '安全演练', '远程实验']
            },
            'experience': {
                'name': '环境体验',
                'features': ['3D场景', '交互体验', '多人协作']
            }
        }
    }
    
    # 泛在学习空间
    UBIQUITOUS_SPACES = {
        'data_layer': {  # 数据层
            'physical_data': {
                'name': '物理空间数据',
                'active_learners': random.randint(1000, 5000),
                'space_usage': random.uniform(0.4, 0.9)
            },
            'virtual_data': {
                'name': '虚拟空间数据',
                'qa_sessions': random.randint(100, 1000),
                'resource_usage': random.uniform(0.5, 0.95)
            },
            'learning_behavior': {
                'name': '学习行为数据',
                'personalized_paths': random.randint(20, 100),
                'engagement_rate': random.uniform(0.6, 0.9)
            },
            'interaction_data': {
                'name': '交互数据',
                'response_time': f"{random.uniform(0.1, 1.0):.2f}秒",
                'interaction_count': random.randint(500, 2000)
            }
        },
        'application_layer': {  # 应用层
            'ai_tutor': {
                'name': 'AI导师服务',
                'features': ['实时答疑', '学习指导', '个性化推荐']
            },
            'resource_access': {
                'name': '资源访问',
                'features': ['多终端访问', '资源推荐', '学习追踪']
            },
            'learning_analytics': {
                'name': '学习分析',
                'features': ['效果评估', '行为分析', '预警干预']
            },
            'interaction': {
                'name': '互动交流',
                'features': ['实时互动', '异步交流', '社区协作']
            }
        }
    }

# 修改主应用入口
def main():
    # 初始化session_state
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'language' not in st.session_state:
        st.session_state.language = "中文"
    if 'sidebar_option' not in st.session_state:
        st.session_state.sidebar_option = get_text("dashboard")
    
    # 添加语言选择
    st.sidebar.selectbox(
        "Language/语言",
        ["中文", "English"],
        key="language"
    )
    
    # 添加主题选择
    theme = st.sidebar.selectbox(
        "主题风格",
        ["Light", "Dark", "Custom"],
        key="theme"
    )
    apply_theme(theme)
    
    # 根据登录状态显示不同内容
    if not st.session_state.logged_in:
        if st.session_state.page == "register":
            register_page()
        elif st.session_state.page == "reset":
            reset_password_page()
        else:
            login_page()
    else:
        st.title(f"{get_text('title')} - {st.session_state.username}")
        
        # 添加侧边栏选项
        sidebar_option = st.sidebar.radio(
            "选择操作",
            [get_text("dashboard"), get_text("data_analysis"), "AI助手", "学习空间推荐", 
             "学习路径规划", "学习行为分析", "学习诊断", "帮助中心", get_text("settings"), get_text("logout")],
            key="sidebar_option"
        )
        
        if sidebar_option == get_text("settings"):
            change_password_page()
        elif sidebar_option == get_text("logout"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
        elif sidebar_option == get_text("data_analysis"):
            st.subheader(get_text("data_analysis"))
            analysis_type = st.selectbox(
                "选择分析类型",
                ["使用率趋势", "行为模式", "环境影响", "AI增强分析"]
            )
            if analysis_type == "使用率趋势":
                st.plotly_chart(render_trend_analysis(), use_container_width=True)
            elif analysis_type == "行为模式":
                st.plotly_chart(render_learning_behavior_radar(), use_container_width=True)
            elif analysis_type == "环境影响":
                st.plotly_chart(render_space_efficiency_heatmap(), use_container_width=True)
            else:
                render_space_analysis()
        elif sidebar_option == "AI助手":
            render_ai_assistant()
        elif sidebar_option == "学习空间推荐":
            render_space_recommendation()
        elif sidebar_option == "学习路径规划":
            render_learning_path_recommendation()
        elif sidebar_option == "学习行为分析":
            render_learning_behavior_analysis()
        elif sidebar_option == "学习诊断":
            render_learning_diagnosis()
        elif sidebar_option == "帮助中心":
            render_help_page()
        else:
            render_dashboard()

# 主题设置
def apply_theme(theme):
    if theme == "Dark":
        st.markdown("""
        <style>
        .stApp {
            background-color: #1E1E1E;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
    elif theme == "Custom":
        st.markdown("""
        <style>
        .stApp {
            background-color: #f0f2f6;
            color: #1E1E1E;
        }
        </style>
        """, unsafe_allow_html=True)

# 修改render_dashboard函数
def render_dashboard():
    """渲染主数据大屏"""
    # 添加页面标题和描述
    st.title("🎓 智慧学习空间数据大屏")
    
    # 使用更美观的系统概述卡片
    st.markdown("""
    <div style='background-color: rgba(28, 131, 225, 0.1); padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; border-left: 5px solid #1c83e1;'>
        <h4 style='margin:0; color: #1c83e1;'>系统概述</h4>
        <p style='margin:0.5rem 0 0 0; font-size: 1rem;'>
        整合物理、虚拟和泛在学习空间的实时监控与分析平台，基于"5A"智慧学习范式，提供全方位的学习空间数据可视化与智能分析。
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 添加自动刷新控制
    with st.sidebar:
        st.subheader("⚙️ 控制面板")
        auto_refresh = st.checkbox("自动刷新", value=st.session_state.get('auto_refresh', False))
        refresh_interval = st.slider("刷新间隔(秒)", 5, 300, 30)
        if auto_refresh:
            st.session_state.auto_refresh = True
            time.sleep(refresh_interval)
            st.rerun()
    
    # 使用tabs来组织不同空间的数据，添加图标
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📍 物理空间", 
        "💻 虚拟空间", 
        "🌐 泛在空间", 
        "📈 趋势分析", 
        "🤖 AI助手"
    ])
    
    with tab1:
        render_physical_space()
    
    with tab2:
        render_virtual_space()
    
    with tab3:
        render_ubiquitous_space()
    
    with tab4:
        st.plotly_chart(render_trend_analysis(), use_container_width=True)
    
    with tab5:
        render_ai_assistant()
    
    # 添加底部状态栏
    st.markdown("---")
    cols = st.columns([1, 1, 1])
    with cols[0]:
        st.markdown("**系统状态:** 🟢 正常运行中")
    with cols[1]:
        st.markdown(f"**最后更新:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with cols[2]:
        if 'api_usage' in st.session_state:
            st.markdown(f"**API调用次数:** {st.session_state.api_usage['calls']}")
        else:
            st.markdown("**API调用次数:** 0")

def render_space_distribution():
    """空间分布可视化"""
    df = AdvancedDataSimulator.generate_space_usage()
    
    # 创建树形图
    fig = px.treemap(
        df,
        path=['space_type', 'space_name'],
        values='current_users',
        color='utilization',
        color_continuous_scale='RdYlGn',
        title='学习空间分布与使用情况'
    )
    return fig

def render_space_comparison():
    """校内外空间对比"""
    df = AdvancedDataSimulator.generate_space_usage()
    
    # 计算校内外统计数据
    comparison = df.groupby('space_type').agg({
        'current_users': 'sum',
        'utilization': 'mean',
        'satisfaction': 'mean'
    }).round(2)
    
    return comparison

def render_activity_radar():
    """学习活动雷达图"""
    activities = AdvancedDataSimulator.generate_learning_activities()
    
    fig = go.Figure(data=go.Scatterpolar(
        r=list(activities.values()),
        theta=list(activities.keys()),
        fill='toself'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        title="学习活动分布"
    )
    return fig

def render_space_analysis():
    """空间分析页面"""
    st.subheader("空间使用分析")
    
    # 时间范围选择
    date_range = st.date_input(
        "选择分析时间范围",
        [datetime.now() - timedelta(days=30), datetime.now()]
    )
    
    # 分析维度选择
    analysis_dim = st.multiselect(
        "选择分析维度",
        ["使用率", "满意度", "活动类型", "人流量", "AI增强分析"],
        default=["使用率"]
    )
    
    # 生成分析图表
    if "使用率" in analysis_dim:
        st.plotly_chart(render_space_distribution(), use_container_width=True)
    if "满意度" in analysis_dim:
        st.plotly_chart(render_satisfaction_analysis(), use_container_width=True)
    if "活动类型" in analysis_dim:
        st.plotly_chart(render_activity_radar(), use_container_width=True)
    if "人流量" in analysis_dim:
        st.plotly_chart(render_traffic_analysis(), use_container_width=True)
    
    # 添加AI增强分析
    if "AI增强分析" in analysis_dim:
        with st.spinner("AI分析中..."):
            # 获取分析数据
            space_data = cached_space_usage().to_dict()
            
            # 调用DeepSeek进行分析
            deepseek_ai = DeepSeekAI()
            analysis_prompt = f"""
            请分析以下学习空间数据，重点关注:
            1. 空间使用效率和优化建议
            2. 学习行为模式和趋势
            3. 资源分配合理性评估
            4. 未来使用预测
            
            数据内容: {json.dumps(space_data, ensure_ascii=False)}
            
            请提供详细的分析报告，包括数据洞察、问题识别和改进建议。
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的教育数据分析专家，擅长分析学习空间数据并提供有价值的见解。"},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = deepseek_ai.sync_generate_response(messages)
            
            if "error" in response:
                st.error(f"AI分析过程中出现错误: {response.get('error', '未知错误')}")
            else:
                try:
                    analysis_content = response["choices"][0]["message"]["content"]
                    st.markdown("## AI增强分析报告")
                    st.markdown(analysis_content)
                except (KeyError, IndexError):
                    st.error("处理AI响应时出现错误，请稍后再试。")

def render_virtual_space():
    """渲染虚拟学习空间数据"""
    st.subheader("虚拟空间概览")
    
    # 获取知识分布图表和数据
    fig, df = render_knowledge_distribution()
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True, key="knowledge_dist")
    
    # 显示详细数据
    with st.expander("📊 知识资源详细数据", expanded=False):
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

def render_interaction_network():
    """学习交互网络分析"""
    # 生成网络数据
    nodes = ['学习者A', '学习者B', '学习者C', '导师A', '导师B', 'AI助手']
    edges = []
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            if random.random() > 0.3:  # 70%概率生成连接
                edges.append((i, j, random.randint(1, 10)))

def render_ubiquitous_space():
    """渲染泛在学习空间数据"""
    st.subheader("泛在空间概览")
    
    # 生成模拟数据
    ubiquitous_metrics = {
        'active_learners': random.randint(1000, 2000),
        'ai_interactions': random.randint(500, 1000),
        'learning_paths': random.randint(20, 50),
        'avg_response_time': round(random.uniform(0.5, 1.0), 2)
    }
    
    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "活跃学习者",
            f"{ubiquitous_metrics['active_learners']:,}",
            f"+{random.randint(50, 100)}"
        )
    with col2:
        st.metric(
            "AI交互次数",
            f"{ubiquitous_metrics['ai_interactions']}",
            f"+{random.randint(20, 50)}"
        )
    with col3:
        st.metric(
            "个性化路径",
            f"{ubiquitous_metrics['learning_paths']}",
            f"+{random.randint(2, 5)}"
        )
    with col4:
        st.metric(
            "平均响应时间",
            f"{ubiquitous_metrics['avg_response_time']}秒",
            f"-{random.uniform(0.01, 0.05):.2f}秒"
        )
    
    # 学习行为分析
    st.subheader("学习行为分析")
    col1, col2 = st.columns(2)
    
    with col1:
        # 学习时间分布
        hours = list(range(24))
        behavior_data = {
            '时间': hours,
            '在线学习': [random.randint(50, 200) for _ in hours],
            '移动学习': [random.randint(30, 150) for _ in hours],
            'AI辅助': [random.randint(20, 100) for _ in hours]
        }
        df_behavior = pd.DataFrame(behavior_data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_behavior['时间'],
            y=df_behavior['在线学习'],
            name='在线学习',
            mode='lines+markers',
            line=dict(width=2, color='#1E88E5')
        ))
        fig.add_trace(go.Scatter(
            x=df_behavior['时间'],
            y=df_behavior['移动学习'],
            name='移动学习',
            mode='lines+markers',
            line=dict(width=2, color='#FFC107')
        ))
        fig.add_trace(go.Scatter(
            x=df_behavior['时间'],
            y=df_behavior['AI辅助'],
            name='AI辅助',
            mode='lines+markers',
            line=dict(width=2, color='#4CAF50')
        ))
        
        fig.update_layout(
            title='24小时学习行为分布',
            xaxis_title='时间 (小时)',
            yaxis_title='活跃人数',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 学习场景分布
        scene_data = {
            '场景': ['课堂学习', '图书馆', '实验室', '户外', '居家', '交通工具', '其他'],
            '使用时长': [random.randint(100, 500) for _ in range(7)],
            '学习效果': [random.uniform(3.5, 4.8) for _ in range(7)]
        }
        df_scene = pd.DataFrame(scene_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_scene['场景'],
            y=df_scene['使用时长'],
            name='使用时长',
            marker_color='#1E88E5',
            yaxis='y'
        ))
        fig.add_trace(go.Scatter(
            x=df_scene['场景'],
            y=df_scene['学习效果'],
            name='学习效果',
            mode='lines+markers',
            line=dict(color='#4CAF50'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='学习场景分布与效果',
            yaxis=dict(title='使用时长(分钟)'),
            yaxis2=dict(
                title='学习效果评分',
                overlaying='y',
                side='right',
                range=[0, 5]
            ),
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 学习路径分析
    st.subheader("学习路径分析")
    
    # 生成学习路径数据
    path_data = []
    for _ in range(10):
        path_data.append({
            '路径ID': f'P{random.randint(1000, 9999)}',
            '学习者数量': random.randint(50, 200),
            '平均完成率': f"{random.uniform(0.6, 0.95):.1%}",
            '平均满意度': f"{random.uniform(4.0, 4.9):.1f}",
            '推荐指数': random.randint(1, 5) * '⭐',
            '适应性评分': f"{random.uniform(3.5, 4.8):.1f}"
        })
    
    df_paths = pd.DataFrame(path_data)
    st.dataframe(
        df_paths,
        use_container_width=True,
        hide_index=True,
        column_config={
            "推荐指数": st.column_config.TextColumn(
                "推荐指数",
                help="基于用户反馈的推荐星级",
                width="medium",
            )
        }
    )

def render_physical_space():
    """渲染物理学习空间数据"""
    # 获取物理空间数据
    physical_data = LearningSpaceModel.PHYSICAL_SPACES
    
    # 概览指标
    st.subheader("物理空间概览")
    
    # 生成模拟数据
    space_metrics = {
        'indoor': {
            'total_users': random.randint(500, 2000),
            'utilization': random.uniform(0.6, 0.9),
            'active_spaces': random.randint(10, 20),
            'satisfaction': random.uniform(4.0, 4.8)
        },
        'outdoor': {
            'total_users': random.randint(200, 1000),
            'utilization': random.uniform(0.4, 0.8),
            'active_spaces': random.randint(5, 15),
            'satisfaction': random.uniform(4.2, 4.9)
        }
    }
    
    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_users = sum(data['total_users'] for data in space_metrics.values())
        st.metric(
            "总使用人数",
            f"{total_users:,}",
            f"{random.randint(-50, 100)}"
        )
    with col2:
        avg_utilization = np.mean([data['utilization'] for data in space_metrics.values()])
        st.metric(
            "平均使用率",
            f"{avg_utilization:.1%}",
            f"{random.uniform(-0.05, 0.05):.1%}"
        )
    with col3:
        total_active = sum(data['active_spaces'] for data in space_metrics.values())
        st.metric(
            "活跃空间数",
            total_active,
            random.randint(-2, 5)
        )
    with col4:
        avg_satisfaction = np.mean([data['satisfaction'] for data in space_metrics.values()])
        st.metric(
            "平均满意度",
            f"{avg_satisfaction:.1f}",
            f"{random.uniform(-0.2, 0.2):.1f}"
        )
    
    # 空间分布分析
    st.subheader("空间分布分析")
    col1, col2 = st.columns(2)
    
    with col1:
        # 创建空间分布树形图数据
        tree_data = []
        for location, spaces in physical_data.items():
            for space_id, space_info in spaces.items():
                tree_data.append({
                    '位置': '校内' if location == 'indoor' else '校外',
                    '空间类型': space_info['name'],
                    '使用率': random.uniform(0.4, 0.9),
                    '人数': random.randint(20, 100)
                })
        
        df = pd.DataFrame(tree_data)
        fig = px.treemap(
            df,
            path=['位置', '空间类型'],
            values='人数',
            color='使用率',
            color_continuous_scale='RdYlGn',
            title='学习空间分布'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 创建空间使用热力图
        hours = list(range(8, 22))  # 8:00 - 21:00
        space_types = ['传统学习', '休闲学习', '技能学习', '协作学习', 
                      '个性学习', '创新学习', '展演学习']
        
        utilization_data = np.random.uniform(0.2, 0.9, size=(len(space_types), len(hours)))
        
        fig = go.Figure(data=go.Heatmap(
            z=utilization_data,
            x=[f"{hour}:00" for hour in hours],
            y=space_types,
            colorscale='RdYlGn',
            colorbar=dict(title='使用率')
        ))
        
        fig.update_layout(
            title='空间使用效率分析',
            xaxis_title='时间',
            yaxis_title='空间类型',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 空间详情数据表
    with st.expander("📊 空间详细数据", expanded=False):
        detail_data = []
        for location, spaces in physical_data.items():
            for space_id, space_info in spaces.items():
                detail_data.append({
                    '位置': '校内' if location == 'indoor' else '校外',
                    '空间类型': space_info['name'],
                    '描述': space_info['description'],
                    '当前人数': random.randint(10, 100),
                    '使用率': f"{random.uniform(0.4, 0.9):.1%}",
                    '满意度': f"{random.uniform(4.0, 5.0):.1f}"
                })
        
        df_details = pd.DataFrame(detail_data)
        st.dataframe(
            df_details,
            use_container_width=True,
            hide_index=True
        )

def render_knowledge_distribution():
    """知识内容分布分析"""
    # 获取虚拟空间数据
    virtual_data = LearningSpaceModel.VIRTUAL_SPACES
    
    # 创建知识分布数据
    knowledge_categories = [
        '课程资源',
        '实验资源',
        '案例资源',
        '测评资源',
        '参考资料',
        '实践项目',
        '研讨资料'
    ]
    
    knowledge_data = {
        '资源类型': knowledge_categories,
        '资源数量': [random.randint(100, 1000) for _ in range(len(knowledge_categories))],
        '使用频率': [random.uniform(0.4, 0.9) for _ in range(len(knowledge_categories))],
        '更新周期': [random.randint(1, 30) for _ in range(len(knowledge_categories))],
        '评分': [random.uniform(4.0, 5.0) for _ in range(len(knowledge_categories))]
    }
    
    df = pd.DataFrame(knowledge_data)
    
    # 创建知识分布图表
    fig = go.Figure()
    
    # 添加柱状图 - 资源数量
    fig.add_trace(go.Bar(
        x=df['资源类型'],
        y=df['资源数量'],
        name='资源数量',
        marker_color='#1E88E5',
        yaxis='y'
    ))
    
    # 添加折线图 - 使用频率
    fig.add_trace(go.Scatter(
        x=df['资源类型'],
        y=df['使用频率'],
        name='使用频率',
        mode='lines+markers',
        marker=dict(color='#FFC107'),
        line=dict(color='#FFC107'),
        yaxis='y2'
    ))
    
    # 添加折线图 - 评分
    fig.add_trace(go.Scatter(
        x=df['资源类型'],
        y=df['评分'],
        name='评分',
        mode='lines+markers',
        marker=dict(color='#4CAF50'),
        line=dict(color='#4CAF50'),
        yaxis='y3'
    ))
    
    # 更新布局
    fig.update_layout(
        title='知识资源分布与使用情况',
        xaxis=dict(title='资源类型'),
        yaxis=dict(
            title=dict(text='资源数量', font=dict(color='#1E88E5')),
            tickfont=dict(color='#1E88E5')
        ),
        yaxis2=dict(
            title=dict(text='使用频率', font=dict(color='#FFC107')),
            tickfont=dict(color='#FFC107'),
            overlaying='y',
            side='right',
            range=[0, 1]
        ),
        yaxis3=dict(
            title=dict(text='评分', font=dict(color='#4CAF50')),
            tickfont=dict(color='#4CAF50'),
            overlaying='y',
            side='right',
            position=0.85,
            range=[0, 5]
        ),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        height=400,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig, df  # 返回图表和数据

# 添加安全配置
import secrets

# 生成安全的会话密钥
if 'session_key' not in st.session_state:
    st.session_state.session_key = secrets.token_hex(16)

# 添加基本的 CSRF 保护
def generate_csrf_token():
    if 'csrf_token' not in st.session_state:
        st.session_state.csrf_token = secrets.token_hex(32)
    return st.session_state.csrf_token

# 添加速率限制
def rate_limit(key, limit=100, window=60):
    """简单的速率限制实现"""
    now = datetime.now()
    if 'rate_limit' not in st.session_state:
        st.session_state.rate_limit = {}
    
    if key not in st.session_state.rate_limit:
        st.session_state.rate_limit[key] = []
    
    # 清理过期的请求记录
    st.session_state.rate_limit[key] = [
        t for t in st.session_state.rate_limit[key]
        if t > now - timedelta(seconds=window)
    ]
    
    if len(st.session_state.rate_limit[key]) >= limit:
        return False
    
    st.session_state.rate_limit[key].append(now)
    return True

# 添加缓存支持
@st.cache_data(ttl=3600)  # 缓存1小时
def fetch_data():
    """获取数据的函数"""
    return your_data_fetching_logic()

# 添加数据预加载
def preload_data():
    """预加载常用数据"""
    if 'preloaded_data' not in st.session_state:
        st.session_state.preloaded_data = fetch_data()

# 在AuthConfig类后添加DeepSeek API集成类
class DeepSeekAI:
    def __init__(self):
        # 从环境变量或会话状态获取API密钥
        self.api_key = os.getenv('DEEPSEEK_API_KEY', '')
        # 如果环境变量中没有，尝试从会话状态获取
        if not self.api_key and 'deepseek_api_key' in st.session_state:
            self.api_key = st.session_state.deepseek_api_key
        
        # 手动设置API密钥（临时解决方案）
        if not self.api_key:
            self.api_key = "sk-fd1c7c81430b433daffcc8ebee130906"
        
        # 不显示警告信息
        # st.warning("DeepSeek API密钥未配置，请在设置页面配置API密钥")
        
        # 根据文档更新API基础URL
        self.api_base = "https://api.deepseek.com"  # 不包含/v1
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        self.session = None
    
    async def init_session(self):
        """初始化异步会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """关闭异步会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def generate_response(self, messages: List[Dict[str, str]], 
                               temperature: float = 0.7, 
                               max_tokens: int = 1000) -> Dict[str, Any]:
        """调用DeepSeek API生成响应"""
        await self.init_session()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with self.session.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logging.error(f"DeepSeek API错误: {error_text}")
                    return {"error": f"API错误: {response.status}", "details": error_text}
        except Exception as e:
            logging.error(f"调用DeepSeek API时发生错误: {str(e)}")
            return {"error": f"请求错误: {str(e)}"}
    
    def sync_generate_response(self, messages: List[Dict[str, str]], 
                              temperature: float = 0.7, 
                              max_tokens: int = 500):  # 减少最大令牌数
        """同步调用DeepSeek API (用于非异步环境)"""
        # 检查API密钥
        if not self.api_key:
            return {"error": "API密钥未配置", "details": "请在设置页面配置DeepSeek API密钥"}
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            # 添加详细日志
            logging.info(f"正在调用DeepSeek API，模型: {self.model}")
            logging.info(f"API基础URL: {self.api_base}")
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # 记录响应状态和内容
            logging.info(f"API响应状态码: {response.status_code}")
            if response.status_code != 200:
                logging.error(f"API响应内容: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logging.error(f"DeepSeek API认证错误: {response.text}")
                return {"error": "API认证失败(401)", "details": "请检查API密钥是否正确"}
            elif response.status_code == 402:
                logging.error(f"DeepSeek API付款错误: {response.text}")
                return {"error": "API付款问题(402)", "details": "账户余额不足或付款问题，请检查您的DeepSeek账户状态"}
            elif response.status_code == 403:
                logging.error(f"DeepSeek API权限错误: {response.text}")
                return {"error": "API权限不足(403)", "details": "您的账户可能没有访问此API的权限"}
            elif response.status_code == 429:
                logging.error(f"DeepSeek API请求过多: {response.text}")
                return {"error": "请求频率限制(429)", "details": "请求过于频繁，请稍后再试"}
            else:
                logging.error(f"DeepSeek API错误: {response.status_code} - {response.text}")
                return {"error": f"API错误: {response.status_code}", "details": response.text}
        except requests.exceptions.Timeout:
            logging.error("DeepSeek API请求超时")
            return {"error": "请求超时", "details": "API服务器响应超时，请稍后再试"}
        except requests.exceptions.ConnectionError:
            logging.error("DeepSeek API连接错误")
            return {"error": "连接错误", "details": "无法连接到API服务器，请检查网络连接"}
        except Exception as e:
            logging.error(f"调用DeepSeek API时发生错误: {str(e)}")
            return {"error": f"请求错误", "details": str(e)}
        
        # 如果是付费模型，可以尝试使用免费模型
        if self.model in ["deepseek-chat", "deepseek-coder"]:
            try_free_model = False
            if "error" in response and response.get("error", "").startswith("API错误: 402"):
                logging.info("尝试使用免费模型...")
                payload["model"] = "deepseek-chat-light"  # 假设这是一个免费模型
                try_free_model = True
                
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    logging.info("使用免费模型成功")
                    return response.json()
        return response  # 返回最后一次尝试的结果
    
    def analyze_learning_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析学习数据并提供见解"""
        messages = [
            {"role": "system", "content": "你是一个专业的教育数据分析专家，擅长分析学习空间数据并提供有价值的见解。"},
            {"role": "user", "content": f"请分析以下学习空间数据，并提供关键见解和改进建议：\n{json.dumps(data, ensure_ascii=False)}"}
        ]
        
        response = self.sync_generate_response(messages)
        if "error" in response:
            return {"analysis": "分析过程中出现错误，请稍后再试。", "error": response["error"]}
        
        try:
            content = response["choices"][0]["message"]["content"]
            return {"analysis": content}
        except (KeyError, IndexError) as e:
            logging.error(f"解析DeepSeek响应时出错: {str(e)}")
            return {"analysis": "无法解析AI响应，请稍后再试。", "error": str(e)}

    # 在DeepSeekAI类中添加重试机制
    def sync_generate_response_with_retry(self, messages: List[Dict[str, str]], 
                                         temperature: float = 0.7, 
                                         max_tokens: int = 1000,
                                         max_retries: int = 3) -> Dict[str, Any]:
        """带重试机制的API调用"""
        retries = 0
        while retries < max_retries:
            response = self.sync_generate_response(messages, temperature, max_tokens)
            if "error" not in response or response.get("error", "").startswith("API错误: 5"):
                # 成功或非服务器错误，直接返回
                return response
            
            # 服务器错误，尝试重试
            retries += 1
            if retries < max_retries:
                # 指数退避策略
                wait_time = 2 ** retries
                time.sleep(wait_time)
                logging.info(f"API调用失败，第{retries}次重试...")
        
        return response  # 返回最后一次尝试的结果

    # 在DeepSeekAI类中添加使用量跟踪
    def track_api_usage(self, tokens_used: int = 0):
        """跟踪API使用量"""
        if 'api_usage' not in st.session_state:
            st.session_state.api_usage = {
                'calls': 0,
                'tokens': 0,
                'last_call': None
            }
        
        st.session_state.api_usage['calls'] += 1
        st.session_state.api_usage['tokens'] += tokens_used
        st.session_state.api_usage['last_call'] = datetime.now()

# 添加AI助手界面函数

def render_ai_assistant():
    """渲染AI助手界面"""
    st.subheader("DeepSeek AI 智能助手")
    
    # 初始化会话状态
    if 'ai_messages' not in st.session_state:
        st.session_state.ai_messages = [
            {"role": "system", "content": "你是5A智慧学习空间的AI助手，可以帮助用户分析学习数据、提供学习建议、回答教育相关问题。"},
            {"role": "assistant", "content": "您好！我是基于DeepSeek的5A智慧学习空间AI助手。我可以帮您分析学习数据、提供学习建议或回答教育相关问题。请问有什么可以帮助您的吗？"}
        ]
    
    # 显示对话历史
    for message in st.session_state.ai_messages:
        if message["role"] != "system":
            if message["role"] == "user":
                st.markdown(f"**您:** {message['content']}")
            else:
                st.markdown(f"**AI助手:** {message['content']}")
    
    # 用户输入
    with st.form(key="ai_assistant_form", clear_on_submit=True):
        user_input = st.text_area("请输入您的问题:")
        submit = st.form_submit_button("发送")
        clear = st.form_submit_button("清空对话")
        
        if submit and user_input:
            # 添加用户消息
            st.session_state.ai_messages.append({"role": "user", "content": user_input})
            
            # 调用API获取响应
            with st.spinner("AI思考中..."):
                deepseek_ai = DeepSeekAI()
                response = deepseek_ai.sync_generate_response(
                    st.session_state.ai_messages,
                    temperature=0.7
                )
                
                if "error" in response:
                    error_message = f"获取AI响应时出错: {response.get('error', '未知错误')}"
                    st.session_state.ai_messages.append({"role": "assistant", "content": f"抱歉，{error_message}"})
                else:
                    try:
                        ai_response = response["choices"][0]["message"]["content"]
                        st.session_state.ai_messages.append({"role": "assistant", "content": ai_response})
                    except (KeyError, IndexError) as e:
                        st.session_state.ai_messages.append({"role": "assistant", "content": f"抱歉，处理响应时出错: {str(e)}"})
            
            st.rerun()
        
        if clear:
            # 保留系统消息，清空对话历史
            system_message = next((msg for msg in st.session_state.ai_messages if msg["role"] == "system"), None)
            st.session_state.ai_messages = [system_message] if system_message else []
            st.session_state.ai_messages.append({"role": "assistant", "content": "对话已清空。有什么可以帮您的吗？"})
            st.rerun()

# 添加学习路径推荐功能

def render_learning_path_recommendation():
    """基于DeepSeek的学习路径推荐"""
    st.subheader("个性化学习路径推荐")
    
    # 学习者信息输入
    with st.form("learner_info_form"):
        learner_name = st.text_input("学习者姓名")
        learner_level = st.selectbox("当前水平", ["初级", "中级", "高级"])
        learning_goal = st.text_area("学习目标")
        preferred_style = st.multiselect(
            "偏好学习方式", 
            ["视频学习", "阅读学习", "实践操作", "小组讨论", "自主探究"]
        )
        available_time = st.slider("每周可用学习时间(小时)", 1, 40, 10)
        
        submit = st.form_submit_button("生成学习路径")
        
        if submit:
            if not learner_name or not learning_goal:
                st.error("请填写学习者姓名和学习目标")
            else:
                with st.spinner("AI正在生成个性化学习路径..."):
                    # 构建学习者画像
                    learner_profile = {
                        "name": learner_name,
                        "level": learner_level,
                        "goal": learning_goal,
                        "preferred_style": preferred_style,
                        "available_time": available_time
                    }
                    
                    # 调用DeepSeek生成学习路径
                    deepseek_ai = DeepSeekAI()
                    prompt = f"""
                    请为以下学习者设计一个个性化的学习路径:
                    
                    学习者信息:
                    - 姓名: {learner_name}
                    - 当前水平: {learner_level}
                    - 学习目标: {learning_goal}
                    - 偏好学习方式: {', '.join(preferred_style)}
                    - 每周可用时间: {available_time}小时
                    
                    请提供:
                    1. 学习路径概述
                    2. 阶段性学习目标(3-5个阶段)
                    3. 每个阶段的具体学习资源和活动
                    4. 学习进度评估方式
                    5. 时间安排建议
                    
                    请确保学习路径符合学习者的水平、目标和偏好，并能在给定时间内完成。
                    """
                    
                    messages = [
                        {"role": "system", "content": "你是一个专业的教育规划专家，擅长设计个性化学习路径。"},
                        {"role": "user", "content": prompt}
                    ]
                    
                    response = deepseek_ai.sync_generate_response(messages)
                    
                    if "error" in response:
                        st.error(f"生成学习路径时出现错误: {response.get('error', '未知错误')}")
                    else:
                        try:
                            path_content = response["choices"][0]["message"]["content"]
                            st.markdown("## 个性化学习路径")
                            st.markdown(path_content)
                            
                            # 添加保存和分享选项
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    "下载学习路径",
                                    path_content,
                                    file_name=f"{learner_name}_学习路径.md",
                                    mime="text/markdown"
                                )
                            with col2:
                                st.button("分享学习路径", 
                                         help="此功能将在未来版本中实现")
                        except (KeyError, IndexError):
                            st.error("处理AI响应时出现错误，请稍后再试。")

# 添加学习空间智能推荐功能

def render_space_recommendation():
    """基于学习需求的空间推荐"""
    st.subheader("学习空间智能推荐")
    
    # 学习需求输入
    with st.form("learning_needs_form"):
        learning_activity = st.selectbox(
            "学习活动类型",
            ["个人自习", "小组讨论", "实验操作", "创新创作", "展示汇报", "技能训练"]
        )
        
        participant_count = st.number_input("参与人数", 1, 100, 1)
        
        duration = st.slider("预计时长(小时)", 0.5, 8.0, 2.0, 0.5)
        
        required_resources = st.multiselect(
            "所需资源",
            ["电脑/网络", "投影设备", "白板", "实验器材", "创作工具", "参考资料"]
        )
        
        special_requirements = st.text_area("特殊需求(可选)")
        
        submit = st.form_submit_button("推荐学习空间")
        
        if submit:
            with st.spinner("AI正在分析最佳学习空间..."):
                # 构建学习需求
                learning_needs = {
                    "activity_type": learning_activity,
                    "participant_count": participant_count,
                    "duration": duration,
                    "required_resources": required_resources,
                    "special_requirements": special_requirements
                }
                
                # 获取可用空间数据
                available_spaces = cached_space_usage().to_dict()
                
                # 调用DeepSeek进行空间推荐
                deepseek_ai = DeepSeekAI()
                prompt = f"""
                请根据以下学习需求，从可用的学习空间中推荐最适合的空间:
                
                学习需求:
                - 活动类型: {learning_activity}
                - 参与人数: {participant_count}人
                - 预计时长: {duration}小时
                - 所需资源: {', '.join(required_resources) if required_resources else '无特殊要求'}
                - 特殊需求: {special_requirements if special_requirements else '无'}
                
                可用学习空间:
                {json.dumps(available_spaces, ensure_ascii=False)}
                
                请提供:
                1. 最佳推荐空间(1-3个)
                2. 每个推荐空间的优势和适合理由
                3. 使用该空间的注意事项
                4. 空间预约建议
                
                请确保推荐的空间能够满足学习需求，并考虑当前空间的使用率和可用性。
                """
                
                messages = [
                    {"role": "system", "content": "你是一个专业的学习空间顾问，擅长根据学习需求推荐最合适的学习空间。"},
                    {"role": "user", "content": prompt}
                ]
                
                response = deepseek_ai.sync_generate_response(messages)
                
                if "error" in response:
                    st.error(f"生成空间推荐时出现错误: {response.get('error', '未知错误')}")
                else:
                    try:
                        recommendation = response["choices"][0]["message"]["content"]
                        st.markdown("## 学习空间推荐")
                        st.markdown(recommendation)
                        
                        # 添加预约按钮
                        if st.button("预约推荐空间"):
                            st.success("预约请求已发送，请等待确认。")
                    except (KeyError, IndexError):
                        st.error("处理AI响应时出现错误，请稍后再试。")

# 添加学习行为智能分析功能

def render_learning_behavior_analysis():
    """基于DeepSeek的学习行为智能分析"""
    st.subheader("学习行为智能分析")
    
    # 分析选项
    analysis_period = st.selectbox(
        "分析周期",
        ["今日", "本周", "本月", "本学期"]
    )
    
    analysis_focus = st.multiselect(
        "分析重点",
        ["学习时间分布", "学习空间偏好", "学习资源使用", "学习效果评估", "学习行为模式"],
        default=["学习时间分布", "学习行为模式"]
    )
    
    # 生成模拟数据
    if analysis_period == "今日":
        time_range = 24
        time_unit = "小时"
    elif analysis_period == "本周":
        time_range = 7
        time_unit = "天"
    elif analysis_period == "本月":
        time_range = 30
        time_unit = "天"
    else:
        time_range = 16
        time_unit = "周"
    
    behavior_data = {
        "时间分布": {
            "labels": [str(i) for i in range(time_range)],
            "学习时长": [random.uniform(0.5, 4.0) for _ in range(time_range)],
            "专注度": [random.uniform(0.6, 0.95) for _ in range(time_range)]
        },
        "空间偏好": {
            "传统学习空间": random.uniform(0.1, 0.3),
            "休闲学习空间": random.uniform(0.1, 0.2),
            "技能学习空间": random.uniform(0.1, 0.2),
            "协作学习空间": random.uniform(0.1, 0.2),
            "个性学习空间": random.uniform(0.1, 0.2),
            "创新学习空间": random.uniform(0.05, 0.15),
            "展演学习空间": random.uniform(0.05, 0.1)
        },
        "资源使用": {
            "视频资源": random.uniform(0.2, 0.4),
            "文本资源": random.uniform(0.2, 0.4),
            "交互资源": random.uniform(0.1, 0.3),
            "实践资源": random.uniform(0.1, 0.3),
            "评估资源": random.uniform(0.05, 0.2)
        },
        "学习效果": {
            "知识掌握": [random.uniform(0.7, 0.95) for _ in range(5)],
            "技能提升": [random.uniform(0.6, 0.9) for _ in range(5)],
            "学习满意度": [random.uniform(0.75, 0.95) for _ in range(5)]
        }
    }
    
    # 显示基础分析图表
    if "学习时间分布" in analysis_focus:
        st.subheader("学习时间分布")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=behavior_data["时间分布"]["labels"],
            y=behavior_data["时间分布"]["学习时长"],
            name="学习时长(小时)",
            marker_color="#1E88E5"
        ))
        fig.add_trace(go.Scatter(
            x=behavior_data["时间分布"]["labels"],
            y=behavior_data["时间分布"]["专注度"],
            name="专注度",
            mode="lines+markers",
            yaxis="y2",
            marker=dict(color="#FFC107"),
            line=dict(color="#FFC107")
        ))
        fig.update_layout(
            title=f"{analysis_period}学习时间分布",
            xaxis_title=f"{time_unit}",
            yaxis=dict(title="学习时长(小时)"),
            yaxis2=dict(
                title="专注度",
                overlaying="y",
                side="right",
                range=[0, 1]
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if "学习空间偏好" in analysis_focus:
        st.subheader("学习空间偏好")
        fig = px.pie(
            values=list(behavior_data["空间偏好"].values()),
            names=list(behavior_data["空间偏好"].keys()),
            title="学习空间使用分布"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # AI增强分析
    st.subheader("AI增强分析")
    
    if st.button("生成AI分析报告"):
        with st.spinner("AI正在分析学习行为数据..."):
            # 调用DeepSeek进行分析
            deepseek_ai = DeepSeekAI()
            prompt = f"""
            请分析以下学习行为数据，提供深入见解和改进建议:
            
            分析周期: {analysis_period}
            分析重点: {', '.join(analysis_focus)}
            
            学习行为数据:
            {json.dumps(behavior_data, ensure_ascii=False)}
            
            请提供:
            1. 学习行为模式分析
            2. 学习效率评估
            3. 学习习惯优缺点
            4. 针对性改进建议
            5. 未来学习规划建议
            
            请确保分析深入、具体，并提供可操作的建议。
            """
            
            messages = [
                {"role": "system", "content": "你是一个专业的学习行为分析专家，擅长分析学习数据并提供个性化的学习建议。"},
                {"role": "user", "content": prompt}
            ]
            
            response = deepseek_ai.sync_generate_response(messages)
            
            if "error" in response:
                st.error(f"生成分析报告时出现错误: {response.get('error', '未知错误')}")
            else:
                try:
                    analysis_report = response["choices"][0]["message"]["content"]
                    st.markdown("## 学习行为分析报告")
                    st.markdown(analysis_report)
                    
                    # 添加下载按钮
                    st.download_button(
                        "下载分析报告",
                        analysis_report,
                        file_name=f"学习行为分析报告_{analysis_period}.md",
                        mime="text/markdown"
                    )
                except (KeyError, IndexError):
                    st.error("处理AI响应时出现错误，请稍后再试。")

# 添加智能学习诊断功能

def render_learning_diagnosis():
    """基于DeepSeek的智能学习诊断"""
    st.subheader("智能学习诊断")
    
    # 学习者信息输入
    with st.form("learning_diagnosis_form"):
        learning_subject = st.text_input("学习科目/领域")
        current_level = st.selectbox("当前水平", ["初学者", "基础", "中级", "高级", "专家"])
        
        learning_challenges = st.text_area(
            "学习中遇到的困难",
            placeholder="例如：难以理解某些概念、记忆效果不佳、缺乏学习动力等"
        )
        
        learning_goals = st.text_area(
            "学习目标",
            placeholder="例如：掌握核心概念、通过考试、应用于实际项目等"
        )
        
        learning_methods = st.multiselect(
            "当前学习方法",
            ["课堂学习", "自学", "小组学习", "在线课程", "实践操作", "阅读", "视频学习", "其他"]
        )
        
        learning_time = st.slider("每周学习时间(小时)", 1, 40, 10)
        
        submit = st.form_submit_button("开始诊断")
        
        if submit:
            if not learning_subject or not learning_challenges or not learning_goals:
                st.error("请填写学习科目、困难和目标")
            else:
                with st.spinner("AI正在进行学习诊断..."):
                    # 构建诊断请求
                    diagnosis_request = {
                        "subject": learning_subject,
                        "level": current_level,
                        "challenges": learning_challenges,
                        "goals": learning_goals,
                        "methods": learning_methods,
                        "time": learning_time
                    }
                    
                    # 调用DeepSeek进行诊断
                    deepseek_ai = DeepSeekAI()
                    prompt = f"""
                    请对以下学习情况进行全面诊断，并提供改进方案:
                    
                    学习科目: {learning_subject}
                    当前水平: {current_level}
                    学习困难: {learning_challenges}
                    学习目标: {learning_goals}
                    学习方法: {', '.join(learning_methods) if learning_methods else '未指定'}
                    每周学习时间: {learning_time}小时
                    
                    请提供:
                    1. 学习问题诊断
                    2. 学习方法评估
                    3. 时间管理建议
                    4. 针对性学习策略
                    5. 资源推荐
                    6. 学习计划调整
                    
                    请确保诊断全面、具体，并提供可操作的改进方案。
                    """
                    
                    messages = [
                        {"role": "system", "content": "你是一个专业的学习诊断专家，擅长分析学习问题并提供个性化的学习改进方案。"},
                        {"role": "user", "content": prompt}
                    ]
                    
                    response = deepseek_ai.sync_generate_response(messages)
                    
                    if "error" in response:
                        st.error(f"生成诊断报告时出现错误: {response.get('error', '未知错误')}")
                    else:
                        try:
                            diagnosis_report = response["choices"][0]["message"]["content"]
                            st.markdown("## 学习诊断报告")
                            st.markdown(diagnosis_report)
                            
                            # 添加下载和分享选项
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    "下载诊断报告",
                                    diagnosis_report,
                                    file_name=f"{learning_subject}_学习诊断报告.md",
                                    mime="text/markdown"
                                )
                            with col2:
                                st.button("分享诊断报告", help="此功能将在未来版本中实现")
                        except (KeyError, IndexError):
                            st.error("处理AI响应时出现错误，请稍后再试。")

# 添加帮助页面
def render_help_page():
    """渲染帮助页面"""
    st.title("帮助中心")
    
    # 使用手风琴组件组织帮助内容
    with st.expander("🔍 如何使用AI助手", expanded=True):
        st.markdown("""
        ### AI助手使用指南
        
        1. **基本对话**：在输入框中输入您的问题，点击"发送"按钮获取AI回复。
        
        2. **快速分析**：点击快速分析选项，可以快速获取特定主题的分析结果。
        
        3. **清空对话**：点击"清空对话"按钮可以重新开始对话。
        
        4. **数据分析**：您可以要求AI助手分析学习数据，提供学习建议。
        
        5. **教育咨询**：您可以咨询任何教育相关的问题，AI助手会尽力回答。
        """)
    
    with st.expander("⚙️ API配置说明"):
        st.markdown("""
        ### DeepSeek API配置指南
        
        1. **获取API密钥**：访问DeepSeek官网获取您的API密钥。
        
        2. **配置API**：在"设置"页面的"API配置"标签页中输入您的API密钥。
        
        3. **选择模型**：根据您的需求选择合适的DeepSeek模型。
        
        4. **测试连接**：配置完成后，点击"测试API连接"确认连接是否成功。
        
        5. **故障排除**：如果连接失败，请检查API密钥是否正确，或查看错误详情。
        """)
    
    with st.expander("📊 数据分析功能"):
        st.markdown("""
        ### 数据分析功能说明
        
        1. **物理空间分析**：分析物理学习空间的使用情况、满意度和优化建议。
        
        2. **虚拟空间分析**：分析在线学习平台的使用情况和学习效果。
        
        3. **泛在空间分析**：整合分析跨场景的学习数据。
        
        4. **趋势分析**：分析学习数据的时间趋势和预测未来趋势。
        
        5. **AI增强分析**：使用AI深度分析学习数据，提供更深入的见解。
        """)
    
    with st.expander("❓ 常见问题"):
        st.markdown("""
        ### 常见问题解答
        
        1. **AI助手无法响应**：请检查API配置是否正确，或查看错误详情。
        
        2. **数据不显示**：请检查数据源连接，或尝试刷新页面。
        
        3. **系统响应缓慢**：可能是数据量过大或网络问题，请稍后再试。
        
        4. **API错误**：请查看错误详情，常见错误包括认证失败(401)和付款问题(402)。
        
        5. **功能建议**：如有功能建议，请联系系统管理员。
        """)
    
    # 添加联系信息
    st.markdown("---")
    st.markdown("### 联系我们")
    st.markdown("如有其他问题，请联系系统管理员：admin@example.com")

if __name__ == "__main__":
    main() 