# 标准库导入
import os
import json
import time
import random  # 添加这行
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from io import BytesIO

# 第三方库导入
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from reportlab.pdfgen import canvas

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
    """获取多语言文本"""
    texts = {
        "title": {
            "en": "5A Smart Learning Space Dashboard",
            "zh": "5A智慧学习空间数据大屏"
        },
        "dashboard": {
            "en": "Data Dashboard",
            "zh": "数据大屏"
        },
        "analysis": {
            "en": "Data Analysis",
            "zh": "数据分析"
        },
        "ai_assistant": {
            "en": "AI Assistant",
            "zh": "AI助手"
        },
        "learning_space": {
            "en": "Learning Space Recommendation",
            "zh": "学习空间推荐"
        },
        "learning_path": {
            "en": "Learning Path Planning",
            "zh": "学习路径规划"
        },
        "learning_behavior": {
            "en": "Learning Behavior Analysis",
            "zh": "学习行为分析"
        },
        "learning_diagnosis": {
            "en": "Learning Diagnosis",
            "zh": "学习诊断"
        },
        "learning_tracker": {  # 新增
            "en": "Learning Records",
            "zh": "学习记录"
        },
        "help": {
            "en": "Help Center",
            "zh": "帮助中心"
        },
        "settings": {
            "en": "Settings",
            "zh": "设置"
        },
        "logout": {
            "en": "Logout",
            "zh": "注销"
        }
    }
    return texts[key][st.session_state.language]

# 页面配置
st.set_page_config(
    page_title="基于AIGC的智慧学习空间",
    page_icon="🎓",
    layout="wide"
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
st.title("基于AIGC的智慧学习空间")
st.markdown("### 智能化学习空间分析与可视化平台")

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
def render_login_page():
    """渲染登录页面"""
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            background: white;
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-footer {
            text-align: center;
            margin-top: 1rem;
            font-size: 0.9rem;
            color: #666;
        }
        .app-title {
            color: #1E88E5;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 创建居中的登录容器
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # 登录页面标题
        st.markdown('<div class="login-header">', unsafe_allow_html=True)
        st.markdown('<div class="app-title">智慧学习空间</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 登录表单
        with st.form("login_form"):
            # 用户名输入
            username = st.text_input(
                "用户名",
                placeholder="请输入用户名",
                help="输入您的用户名或学号"
            )
            
            # 密码输入
            password = st.text_input(
                "密码", 
                type="password",
                placeholder="请输入密码",
                help="输入您的登录密码"
            )
            
            # 记住我选项
            col1, col2 = st.columns(2)
            with col1:
                remember = st.checkbox("记住我", value=True)
            with col2:
                st.markdown('<div style="text-align: right;"><a href="#">忘记密码？</a></div>', 
                          unsafe_allow_html=True)
            
            # 登录按钮
            submit = st.form_submit_button(
                "登 录",
                use_container_width=True,
                type="primary"
            )
        
        # 登录处理
        if submit:
            if username and password:
                # 这里添加实际的登录验证逻辑
                if username == "admin" and password == "admin":  # 示例验证
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("登录成功！正在跳转...")
                    st.rerun()
                else:
                    st.error("用户名或密码错误！")
            else:
                st.warning("请输入用户名和密码！")
        
        # 其他登录选项
        st.markdown('<div class="login-footer">', unsafe_allow_html=True)
        st.markdown("其他登录方式", help="选择其他方式登录")
        
        # 第三方登录按钮
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.button("🎓 校园", use_container_width=True)
        with col2:
            st.button("📱 手机", use_container_width=True)
        with col3:
            st.button("💳 一卡通", use_container_width=True)
        with col4:
            st.button("👥 访客", use_container_width=True)
        
        # 注册提示
        st.markdown("""
            <div style="text-align: center; margin-top: 1rem;">
                还没有账号？<a href="#">立即注册</a>
            </div>
        """, unsafe_allow_html=True)
        
        # 页脚信息
        st.markdown("""
            <div style="text-align: center; margin-top: 2rem; color: #666; font-size: 0.8rem;">
                登录即表示您同意我们的<a href="#">服务条款</a>和<a href="#">隐私政策</a>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

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
        'online_classroom': {
            'name': '在线课堂',
            'features': ['直播互动', '录播回放', '在线答疑'],
            'active_users': random.randint(100, 500),
            'course_count': random.randint(20, 100),
            'satisfaction': random.uniform(4.0, 5.0)
        },
        'digital_library': {
            'name': '数字图书馆',
            'features': ['电子书籍', '学术论文', '多媒体资源'],
            'resource_count': random.randint(5000, 10000),
            'daily_visits': random.randint(500, 2000),
            'download_count': random.randint(100, 1000)
        },
        'virtual_lab': {
            'name': '虚拟实验室',
            'features': ['实验模拟', '数据分析', '远程操作'],
            'experiment_count': random.randint(30, 100),
            'active_projects': random.randint(10, 50),
            'completion_rate': random.uniform(0.7, 0.95)
        },
        'collaboration_space': {
            'name': '协作空间',
            'features': ['团队项目', '在线会议', '文档共享'],
            'team_count': random.randint(20, 100),
            'active_projects': random.randint(30, 150),
            'member_engagement': random.uniform(0.6, 0.9)
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
        'service_layer': {  # 服务层
            'learning_services': {
                'name': '学习服务',
                'features': ['个性化推荐', '学习诊断', '智能辅导'],
                'active_users': random.randint(500, 2000)
            },
            'data_services': {
                'name': '数据服务',
                'features': ['数据采集', '数据分析', '数据可视化'],
                'data_points': random.randint(10000, 50000)
            },
            'integration_services': {
                'name': '集成服务',
                'features': ['系统集成', '数据同步', 'API接口'],
                'connected_systems': random.randint(5, 20)
            }
        },
        'application_layer': {  # 应用层
            'ai_tutor': {
                'name': 'AI导师服务',
                'features': ['实时答疑', '学习指导', '个性化推荐'],
                'active_sessions': random.randint(100, 500)
            },
            'resource_access': {
                'name': '资源访问服务',
                'features': ['多终端访问', '资源推荐', '学习追踪'],
                'daily_requests': random.randint(1000, 5000)
            },
            'learning_analytics': {
                'name': '学习分析服务',
                'features': ['效果评估', '行为分析', '预警干预'],
                'analysis_tasks': random.randint(50, 200)
            }
        }
    }

# 修改主应用入口
def main():
    """主函数"""
    # 初始化session state
    if 'language' not in st.session_state:
        st.session_state.language = 'zh'
    if 'sidebar_option' not in st.session_state:
        st.session_state.sidebar_option = 'dashboard'
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # 应用主题
    theme = st.session_state.get('theme', 'Light')
    apply_theme(theme)
    
    # 根据登录状态显示不同内容
    if not st.session_state.logged_in:
        if st.session_state.get('page') == "register":
            register_page()
        elif st.session_state.get('page') == "reset":
            reset_password_page()
        else:
            render_login_page()
    else:
        # 渲染侧边栏
        sidebar()
        
        # 根据侧边栏选项渲染不同页面
        if st.session_state.sidebar_option == "dashboard":
            render_dashboard()
        elif st.session_state.sidebar_option == "analysis":
            render_analysis()
        elif st.session_state.sidebar_option == "ai_assistant":
            render_ai_assistant()
        elif st.session_state.sidebar_option == "learning_space":
            render_learning_space()
        elif st.session_state.sidebar_option == "learning_path":
            render_learning_path()
        elif st.session_state.sidebar_option == "learning_behavior":
            render_learning_behavior()
        elif st.session_state.sidebar_option == "learning_diagnosis":
            render_learning_diagnosis()
        elif st.session_state.sidebar_option == "learning_tracker":
            render_learning_tracker()
        elif st.session_state.sidebar_option == "help":
            render_help_page()
        elif st.session_state.sidebar_option == "settings":
            render_settings()
        elif st.session_state.sidebar_option == "logout":
            handle_logout()

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

# 添加主题和样式配置
def apply_custom_style():
    """应用自定义样式"""
    st.markdown("""
        <style>
        /* 主标题样式 */
        .main-header {
            color: #1E88E5;
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 2rem;
            text-align: center;
            padding: 1rem;
            background: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%);
            border-radius: 10px;
        }
        
        /* 子标题样式 */
        .sub-header {
            color: #424242;
            font-size: 1.5rem;
            font-weight: 500;
            margin: 1.5rem 0;
            padding-left: 0.5rem;
            border-left: 4px solid #1E88E5;
        }
        
        /* 卡片容器样式 */
        .stcard {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        
        /* 数据指标样式 */
        .metric-container {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        
        /* Tab样式优化 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            margin-bottom: 1rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f8f9fa;
            border-radius: 4px;
            gap: 4px;
            padding: 0.5rem 1rem;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #1E88E5 !important;
            color: white !important;
        }
        
        /* 按钮样式 */
        .stButton>button {
            background-color: #1E88E5;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #1565C0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        /* 滑块样式 */
        .stSlider div[data-baseweb="slider"] {
            margin-top: 1rem;
        }
        
        /* 分割线样式 */
        hr {
            margin: 2rem 0;
            border: none;
            border-top: 1px solid #e0e0e0;
        }
        </style>
    """, unsafe_allow_html=True)

def render_dashboard():
    """渲染主数据大屏"""
    # 应用自定义样式
    apply_custom_style()
    
    # 添加页面标题和描述
    st.markdown('<h1 class="main-header">🎓 智慧学习空间数据大屏</h1>', unsafe_allow_html=True)
    
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
        st.markdown('<h3 class="sub-header">⚙️ 控制面板</h3>', unsafe_allow_html=True)
        auto_refresh = st.checkbox("自动刷新", value=st.session_state.get('auto_refresh', False))
        refresh_interval = st.slider("刷新间隔(秒)", 5, 300, 30)
        if auto_refresh:
            st.session_state.auto_refresh = True
            time.sleep(refresh_interval)
            st.rerun()
    
    # 使用tabs来组织不同空间的数据
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📍 物理空间", 
        "💻 虚拟空间", 
        "🌐 泛在空间", 
        "📈 趋势分析", 
        "🤖 AI助手"
    ])
    
    with tab1:
        st.markdown('<div class="stcard">', unsafe_allow_html=True)
        render_physical_space()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="stcard">', unsafe_allow_html=True)
        render_virtual_space()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="stcard">', unsafe_allow_html=True)
        render_ubiquitous_space()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown('<div class="stcard">', unsafe_allow_html=True)
        st.plotly_chart(render_trend_analysis(), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab5:
        st.markdown('<div class="stcard">', unsafe_allow_html=True)
        render_ai_assistant()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 添加底部状态栏
    st.markdown("---")
    cols = st.columns([1, 1, 1])
    with cols[0]:
        st.markdown("""
        <div class="metric-container" style="text-align: left;">
            <div style="color: #1E88E5;">
                <span style="font-size: 1.2rem;">系统状态:</span>
                <span style="color: #43A047;">🟢 正常运行中</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""
        <div class="metric-container" style="text-align: center;">
            <div style="color: #1E88E5;">
                <span style="font-size: 1.2rem;">最后更新:</span>
                <span>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        api_calls = st.session_state.get('api_usage', {}).get('calls', 0)
        st.markdown(f"""
        <div class="metric-container" style="text-align: right;">
            <div style="color: #1E88E5;">
                <span style="font-size: 1.2rem;">API调用次数:</span>
                <span>{api_calls}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def plot_usage_trend():
    """绘制使用趋势图表"""
    # 生成示例数据
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    data = pd.DataFrame({
        'date': dates,
        'physical': np.random.uniform(60, 90, len(dates)),
        'virtual': np.random.uniform(50, 80, len(dates)),
        'ubiquitous': np.random.uniform(40, 70, len(dates))
    })
    
    # 创建趋势图
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['physical'],
        name='物理空间',
        mode='lines+markers',
        line=dict(color='#1E88E5', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['virtual'],
        name='虚拟空间',
        mode='lines+markers',
        line=dict(color='#43A047', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['ubiquitous'],
        name='泛在空间',
        mode='lines+markers',
        line=dict(color='#FB8C00', width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title=None,
        xaxis_title='日期',
        yaxis_title='使用率 (%)',
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_popular_spaces():
    """绘制热门空间排名"""
    spaces = ['创新实验室', '协作学习区', '静思空间', '研讨室', '多媒体教室']
    usage = [95, 88, 82, 75, 70]
    
    fig = go.Figure(go.Bar(
        x=usage,
        y=spaces,
        orientation='h',
        marker=dict(
            color='#1E88E5',
            line=dict(color='#1565C0', width=1)
        )
    ))
    
    fig.update_layout(
        title=None,
        xaxis_title='使用率 (%)',
        yaxis_title=None,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_behavior_analysis():
    """绘制学习行为分析雷达图"""
    categories = ['专注度', '互动性', '持续时间', '资源利用', '学习效果']
    values = [85, 78, 92, 65, 88]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        line=dict(color='#1E88E5', width=2)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def generate_ai_insights():
    """生成AI分析洞察"""
    try:
        deepseek_ai = DeepSeekAI()
        prompt = """
        基于以下数据生成简短的分析洞察和建议：
        
        1. 空间使用率：85%
        2. 访问人次：1,234
        3. 用户满意度：92%
        4. 活跃空间数：45
        5. 热门空间：创新实验室、协作学习区
        6. 学习行为特征：专注度高、互动性强
        
        请提供：
        1. 关键发现（2-3点）
        2. 改进建议（2-3点）
        3. 未来预测（1-2点）
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的学习空间分析专家，擅长提供简洁、实用的分析见解。"},
            {"role": "user", "content": prompt}
        ]
        
        response = deepseek_ai.sync_generate_response_with_retry(
            messages,
            temperature=0.7,
            max_tokens=300
        )
        
        if "error" in response:
            st.error(f"生成分析洞察时出错: {response.get('error', '未知错误')}")
        else:
            analysis = response["choices"][0]["message"]["content"]
            st.markdown(analysis)
            
    except Exception as e:
        st.error(f"生成分析洞察时出错: {str(e)}")

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

# 在DeepSeekAI类之前添加基础AI类
class BaseAI:
    """AI模型基类"""
    def __init__(self):
        self.name = "Base AI"
    
    def generate_response(self, messages, **kwargs):
        raise NotImplementedError
    
    def sync_generate_response(self, messages, **kwargs):
        return self.generate_response(messages, **kwargs)

class DeepSeekAI(BaseAI):
    """DeepSeek AI实现"""
    def __init__(self):
        super().__init__()
        self.name = "DeepSeek"
        
        load_dotenv()  # 确保加载环境变量
        # 尝试从Streamlit Secrets获取API密钥
        if "DEEPSEEK_API_KEY" in st.secrets:
            self.api_key = st.secrets["DEEPSEEK_API_KEY"]
        else:
            # 回退到环境变量
            self.api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not self.api_key:
            st.error("DeepSeek API密钥未配置")
            return
            
        self.base_url = "https://api.deepseek.com/v1"
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_response(self, messages, **kwargs):
        """生成回复"""
        try:
            url = f"{self.base_url}/chat/completions"
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', 2000)
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"DeepSeek API调用失败({response.status_code}): {response.text}"
                st.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"DeepSeek API错误: {str(e)}"
            st.error(error_msg)
            return {"error": error_msg}

class KimiAI(BaseAI):
    """Kimi AI实现"""
    def __init__(self):
        super().__init__()
        self.name = "Kimi"
        
        load_dotenv()  # 确保加载环境变量
        self.api_key = os.getenv('KIMI_API_KEY')
        self.base_url = "https://api.moonshot.cn/v1"
        
        if not self.api_key:
            st.error("Kimi API密钥未配置，请在.env文件中设置KIMI_API_KEY")
            return
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_response(self, messages, **kwargs):
        """生成回复"""
        try:
            url = f"{self.base_url}/chat/completions"
            
            data = {
                "model": "moonshot-v1-8k",
                "messages": messages,
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', 2000)
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Kimi API调用失败({response.status_code}): {response.text}"
                st.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Kimi API错误: {str(e)}"
            st.error(error_msg)
            return {"error": error_msg}

class ErnieAI(BaseAI):
    """文心一言AI实现"""
    def __init__(self):
        super().__init__()
        self.name = "文心一言"
        # 使用正确的API密钥
        self.api_key = "ALTAK-wkA24WktBRKDpY6tDo8Lh"  # API Key
        self.secret_key = "1ce45e39bb90c1a26460babd8a719db3fa01cd56"  # Secret Key
        self.access_token = None
        self.base_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
        
        # 初始化时获取access token
        self._refresh_token()
        
        self.headers = {
            "Content-Type": "application/json"
        }

    def _refresh_token(self):
        """获取access token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        try:
            response = requests.post(url, params=params)
            result = response.json()
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                st.success("成功获取access token")
            else:
                st.error(f"获取access token失败: {result.get('error_description', '未知错误')}")
                
        except Exception as e:
            st.error(f"获取access token错误: {str(e)}")

    def generate_response(self, messages, **kwargs):
        """生成回复"""
        if not self.access_token:
            self._refresh_token()
            if not self.access_token:
                return {"error": "无法获取access token"}

        try:
            url = f"{self.base_url}?access_token={self.access_token}"
            
            data = {
                "messages": messages,
                "temperature": kwargs.get('temperature', 0.7)
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"文心一言API调用失败({response.status_code}): {response.text}"
                st.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"文心一言API错误: {str(e)}"
            st.error(error_msg)
            return {"error": error_msg}

# 在render_ai_assistant函数中添加模型选择
def render_ai_assistant():
    """渲染AI助手界面"""
    st.subheader("AI智能助手")
    
    # 选择AI模型
    ai_models = {
        "DeepSeek": DeepSeekAI,
        "Kimi": KimiAI,
        "文心一言": ErnieAI,
        "豆包": DouBaoAI
    }
    
    selected_model = st.selectbox(
        "选择AI模型",
        list(ai_models.keys()),
        index=0,
        key="selected_ai_model"
    )

    # 初始化会话状态
    if 'ai_messages' not in st.session_state:
        st.session_state.ai_messages = []
        
    # 初始化当前选择的AI模型实例
    try:
        ai_instance = ai_models[selected_model]()
    except Exception as e:
        st.error(f"初始化{selected_model}失败: {str(e)}")
        return

    # 显示对应模型的欢迎语
    welcome_messages = {
        "DeepSeek": "您好！我是基于DeepSeek的智能学习助手。我可以帮您分析学习数据、提供学习建议或回答教育相关问题。请问有什么可以帮助您的吗？",
        "Kimi": "您好！我是基于Kimi的智能学习助手。我可以帮您分析学习数据、提供学习建议或回答教育相关问题。请问有什么可以帮助您的吗？",
        "文心一言": "您好！我是基于文心一言的智能学习助手。我可以帮您分析学习数据、提供学习建议或回答教育相关问题。请问有什么可以帮助您的吗？",
        "豆包": "您好！我是基于豆包的智能学习助手。我可以帮您分析学习数据、提供学习建议或回答教育相关问题。请问有什么可以帮助您的吗？"
    }
    
    if not st.session_state.ai_messages:
        st.session_state.ai_messages.append({
            "role": "assistant",
            "content": welcome_messages[selected_model]
        })
    
    # 显示对话历史
    for message in st.session_state.ai_messages:
        if message["role"] == "user":
            st.write(f"您: {message['content']}")
        else:
            st.write(f"AI助手({selected_model}): {message['content']}")
    
    # 用户输入和按钮
    with st.form(key="chat_form"):
        user_input = st.text_area("请输入您的问题:", key="chat_input")
        col1, col2 = st.columns([1, 5])
        
        with col1:
            submit = st.form_submit_button("发送")
        with col2:
            clear = st.form_submit_button("清空对话")

        if submit and user_input:
            # 添加用户消息到历史记录
            st.session_state.ai_messages.append({"role": "user", "content": user_input})
            
            # 调用API获取响应
            with st.spinner("AI思考中..."):
                response = ai_instance.generate_response(st.session_state.ai_messages)
                
                if "error" not in response:
                    if "choices" in response and len(response["choices"]) > 0:
                        ai_message = response["choices"][0]["message"]["content"]
                        st.session_state.ai_messages.append({"role": "assistant", "content": ai_message})
                    else:
                        st.error("AI响应格式错误")
                else:
                    st.error(f"生成回复时出错: {response['error']}")
            
            st.rerun()

        if clear:
            st.session_state.ai_messages = []
            st.session_state.ai_messages.append({
                "role": "assistant",
                "content": welcome_messages[selected_model]
            })
            st.rerun()

# 添加学习路径推荐功能

def render_learning_path_recommendation():
    """渲染学习路径推荐页面"""
    st.subheader("个性化学习路径推荐")
    
    # 创建表单
    with st.form(key="learning_path_form"):
        # 学习者信息
        learner_name = st.text_input("学习者姓名")
        learner_level = st.selectbox("当前水平", ["初级", "中级", "高级"])
        learning_goal = st.text_area("学习目标")
        
        # 学习偏好
        preferred_style = st.multiselect(
            "偏好学习方式",
            ["视频学习", "阅读学习", "实践学习", "社交学习", "游戏化学习"],
            default=["视频学习"]
        )
        
        # 时间安排
        available_time = st.slider("每周可用学习时间(小时)", 1, 40, 10)
        
        # 提交按钮
        submit = st.form_submit_button("生成学习路径")
    
    # 表单外处理提交逻辑
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
                
                response = deepseek_ai.generate_response(messages)
                
                if "error" in response:
                    st.error(f"生成学习路径时出现错误: {response.get('error', '未知错误')}")
                else:
                    try:
                        path_content = response["choices"][0]["message"]["content"]
                        st.markdown("## 个性化学习路径")
                        st.markdown(path_content)
                        
                        # 保存学习路径数据到会话状态
                        st.session_state.learning_path_data = path_content
                        
                        # 添加下载按钮（在表单外部）
                        st.download_button(
                            label="下载学习路径",
                            data=path_content,
                            file_name=f"{learner_name}_学习路径.md",
                            mime="text/markdown"
                        )
                        
                        # 添加分享按钮
                        st.button("分享学习路径", help="此功能将在未来版本中实现")
                    except (KeyError, IndexError):
                        st.error("处理AI响应时出现错误，请稍后再试。")

# 添加学习空间智能推荐功能

def render_space_recommendation():
    """渲染学习空间推荐"""
    st.title("学习空间推荐")
    
    # 创建一个容器来显示结果
    result_container = st.container()
    
    with st.form("space_recommendation_form"):
        # 学习需求输入
        activity_type = st.selectbox(
            "学习活动类型",
            ["个人自习", "小组讨论", "实验操作", "创新创作", "展示汇报", "技能训练"]
        )
        
        participant_count = st.number_input("参与人数", 1, 100, 1)
        
        duration_hours = st.slider("预计时长(小时)", 0.5, 8.0, 2.0, 0.5)
        
        selected_resources = st.multiselect(
            "所需资源",
            ["电脑/网络", "投影设备", "白板", "实验器材", "创作工具", "参考资料"]
        )
        
        special_requirements = st.text_area("特殊需求(可选)")
        
        # 定义submit变量
        submit_button = st.form_submit_button("推荐学习空间")
    
    # 表单提交后的处理逻辑
    if submit_button:
        with st.spinner("正在生成学习空间推荐..."):
            try:
                # 构建学习需求
                learning_needs = {
                    "activity_type": activity_type,
                    "participant_count": participant_count,
                    "duration": duration_hours,
                    "required_resources": selected_resources,
                    "special_requirements": special_requirements
                }
                
                # 获取可用空间数据
                available_spaces = cached_space_usage().to_dict()
                
                # 调用DeepSeek进行空间推荐
                deepseek_ai = DeepSeekAI()
                prompt = f"""
                请根据以下学习需求，从可用的学习空间中推荐最适合的空间:
                
                学习需求:
                - 活动类型: {activity_type}
                - 参与人数: {participant_count}人
                - 预计时长: {duration_hours}小时
                - 所需资源: {', '.join(selected_resources) if selected_resources else '无特殊要求'}
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
                
                # 使用带重试的API调用
                response = deepseek_ai.sync_generate_response_with_retry(
                    messages,
                    temperature=0.7,
                    timeout=45,
                    max_retries=3
                )
                
                # 在表单外的容器中显示结果
                with result_container:
                    if "error" in response:
                        st.error(f"生成空间推荐时出现错误: {response.get('error', '未知错误')}")
                        st.info("正在使用离线备用方案...")
                        
                        # 提供一些预定义的推荐
                        st.markdown("## 备用学习空间推荐")
                        
                        # 基于用户选择的资源和时间生成简单推荐
                        resources = []
                        if "电脑/网络" in selected_resources:
                            resources.append("电脑/网络")
                        if "投影设备" in selected_resources:
                            resources.append("投影设备")
                        if "白板" in selected_resources:
                            resources.append("白板")
                        
                        if "个人自习" in activity_type:
                            st.markdown("### 推荐空间: 图书馆自习区")
                            st.markdown(f"- 可用资源: {', '.join(resources)}")
                            st.markdown(f"- 适合时长: {duration_hours}小时")
                            st.markdown("- 特点: 安静、专注、适合个人学习")
                        
                        elif "小组讨论" in activity_type:
                            st.markdown("### 推荐空间: 协作学习室")
                            st.markdown(f"- 可用资源: {', '.join(resources)}")
                            st.markdown(f"- 适合时长: {duration_hours}小时")
                            st.markdown("- 特点: 适合小组讨论、配备白板和投影设备")
                        
                        elif "实验操作" in activity_type:
                            st.markdown("### 推荐空间: 实验室")
                            st.markdown(f"- 可用资源: {', '.join(resources)}")
                            st.markdown(f"- 适合时长: {duration_hours}小时")
                            st.markdown("- 特点: 配备实验设备、适合实践操作")
                        
                        else:
                            st.markdown("### 推荐空间: 综合学习区")
                            st.markdown(f"- 可用资源: {', '.join(resources)}")
                            st.markdown(f"- 适合时长: {duration_hours}小时")
                            st.markdown("- 特点: 灵活布局、适合多种学习活动")
                    else:
                        try:
                            recommendation = response["choices"][0]["message"]["content"]
                            st.markdown("## 学习空间推荐")
                            st.markdown(recommendation)
                            
                            # 这个按钮在表单外部，是合法的
                            if st.button("预约推荐空间"):
                                st.success("预约请求已发送，请等待确认。")
                        except (KeyError, IndexError) as e:
                            st.error(f"处理AI响应时出现错误: {str(e)}")
                
            except Exception as e:
                with result_container:
                    st.error(f"生成空间推荐时出现错误: {str(e)}")
                    st.info("请稍后再试或联系系统管理员获取帮助。")

# 添加学习行为智能分析功能

def render_learning_behavior_analysis():
    """渲染学习行为分析页面"""
    st.subheader("学习行为分析")
    
    # 创建选项卡
    behavior_tabs = st.tabs(["📊 行为概览", "🔍 详细分析", "💡 改进建议"])
    
    # 添加AI分析部分
    with st.expander("🤖 获取AI个性化学习行为分析", expanded=True):
        st.write("请填写以下信息，AI将为您提供深度的学习行为分析")
        
        # 创建表单收集学习行为数据
        with st.form("learning_behavior_form"):
            # 基本学习信息
            col1, col2 = st.columns(2)
            with col1:
                study_time = st.number_input(
                    "平均每日学习时长（小时）",
                    min_value=0.0,
                    max_value=24.0,
                    value=2.5,
                    step=0.5
                )
                attention_rate = st.slider(
                    "平均专注度",
                    min_value=0,
                    max_value=100,
                    value=85,
                    format="%d%%"
                )
            
            with col2:
                task_completion = st.slider(
                    "任务完成率",
                    min_value=0,
                    max_value=100,
                    value=78,
                    format="%d%%"
                )
                knowledge_mastery = st.slider(
                    "知识点掌握度",
                    min_value=0,
                    max_value=100,
                    value=82,
                    format="%d%%"
                )
            
            # 学习习惯
            st.write("#### 学习习惯评估")
            habits_col1, habits_col2 = st.columns(2)
            
            with habits_col1:
                planning = st.select_slider(
                    "学习计划性",
                    options=["很差", "较差", "一般", "良好", "优秀"],
                    value="良好"
                )
                note_taking = st.select_slider(
                    "笔记记录习惯",
                    options=["很差", "较差", "一般", "良好", "优秀"],
                    value="良好"
                )
            
            with habits_col2:
                review_frequency = st.select_slider(
                    "复习频率",
                    options=["很少", "偶尔", "一般", "经常", "频繁"],
                    value="经常"
                )
                self_reflection = st.select_slider(
                    "自我反思程度",
                    options=["很少", "偶尔", "一般", "经常", "频繁"],
                    value="一般"
                )
            
            # 学习困难
            st.write("#### 学习困难")
            difficulties = st.multiselect(
                "目前遇到的主要学习困难（可多选）",
                ["注意力不集中", "学习动力不足", "时间管理差", "记忆效果差", 
                 "理解困难", "知识运用难", "学习方法不当", "其他"],
                default=["注意力不集中", "时间管理差"]
            )
            
            # 学习目标达成情况
            st.write("#### 目标达成")
            goal_achievement = st.text_area(
                "描述您的学习目标达成情况",
                placeholder="例如：完成了80%的计划任务，但是深度学习部分还需要加强..."
            )
            
            analyze_button = st.form_submit_button("开始分析")
        
        if analyze_button:
            with st.spinner("AI正在深入分析您的学习行为..."):
                # 构建分析提示
                prompt = f"""
                请对以下学习行为数据进行全面分析，并提供改进建议：

                基本学习数据：
                - 日均学习时长：{study_time}小时
                - 平均专注度：{attention_rate}%
                - 任务完成率：{task_completion}%
                - 知识掌握度：{knowledge_mastery}%

                学习习惯评估：
                - 计划性：{planning}
                - 笔记习惯：{note_taking}
                - 复习频率：{review_frequency}
                - 自我反思：{self_reflection}

                当前学习困难：{', '.join(difficulties)}

                目标达成情况：{goal_achievement}

                请提供：
                1. 学习行为综合评估
                2. 存在的主要问题分析
                3. 学习效率提升建议
                4. 针对性的改进策略
                5. 可行的行动计划
                
                分析要具体且有建设性，注重实用性和可操作性。
                """
                
                # 调用AI进行分析
                ai = DouBaoAI()
                messages = [
                    {"role": "system", "content": "你是一个专业的学习行为分析专家，擅长诊断学习问题并提供个性化的改进建议。"},
                    {"role": "user", "content": prompt}
                ]
                
                response = ai.generate_response(messages)
                
                if "error" in response:
                    st.error(f"生成分析报告时出现错误: {response['error']}")
                else:
                    try:
                        analysis = response["choices"][0]["message"]["content"]
                        
                        # 显示分析结果
                        st.success("✨ AI已完成学习行为分析")
                        
                        # 使用列布局展示分析内容
                        report_col1, report_col2 = st.columns([2, 1])
                        
                        with report_col1:
                            st.markdown(analysis)
                        
                        with report_col2:
                            st.info("""
                            💡 **温馨提示**
                            
                            - 建议定期进行学习行为分析
                            - 根据分析结果调整学习策略
                            - 持续跟踪改进效果
                            - 建立良好的学习反馈循环
                            """)
                            
                            # 添加下载报告按钮
                            st.download_button(
                                "📥 下载分析报告",
                                analysis,
                                file_name="learning_behavior_analysis.txt",
                                mime="text/plain"
                            )
                    
                    except (KeyError, IndexError):
                        st.error("处理AI响应时出现错误，请稍后再试。")
    
    # 行为概览选项卡
    with behavior_tabs[0]:
        st.write("### 学习行为概览")
        
        # 显示关键指标
        metrics_cols = st.columns(4)
        with metrics_cols[0]:
            st.metric("平均学习时长", "2.5小时/天", "↑ 0.5小时")
        with metrics_cols[1]:
            st.metric("平均专注度", "85%", "↑ 5%")
        with metrics_cols[2]:
            st.metric("任务完成率", "78%", "↓ -2%")
        with metrics_cols[3]:
            st.metric("知识点掌握度", "82%", "↑ 3%")
        
        # 学习行为趋势图
        st.write("### 学习行为趋势")
        
        # 生成示例数据
        dates = pd.date_range(start='2023-02-19', end='2023-03-19', freq='D')
        study_hours = np.random.normal(2.5, 0.5, size=len(dates))
        attention_levels = np.random.normal(85, 5, size=len(dates))
        
        # 创建DataFrame
        df = pd.DataFrame({
            'date': dates,
            'study_hours': study_hours,
            'attention': attention_levels
        })
        
        # 创建趋势图
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'], 
            y=df['study_hours'],
            mode='lines',
            name='学习时长(小时)'
        ))
        fig.add_trace(go.Scatter(
            x=df['date'], 
            y=df['attention'],
            mode='lines',
            name='专注度(%)',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='学习行为趋势分析',
            xaxis_title='日期',
            yaxis_title='学习时长(小时)',
            yaxis2=dict(
                title='专注度(%)',
                overlaying='y',
                side='right',
                range=[0, 100]
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 详细分析选项卡
    with behavior_tabs[1]:
        st.write("### 详细学习行为分析")
        
        # 学习时间分布
        st.write("#### 学习时间分布")
        time_data = {
            '时间段': ['早晨(6-9点)', '上午(9-12点)', '下午(12-18点)', '晚上(18-22点)', '深夜(22-6点)'],
            '学习时长(小时)': [0.5, 0.8, 0.6, 1.2, 0.3]
        }
        time_df = pd.DataFrame(time_data)
        
        fig = px.bar(
            time_df, 
            x='时间段', 
            y='学习时长(小时)',
            title='学习时间分布',
            color='学习时长(小时)',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 学习内容分布
        st.write("#### 学习内容分布")
        content_data = {
            '学习内容': ['理论学习', '实践操作', '复习巩固', '测试评估', '拓展学习'],
            '占比': [35, 25, 20, 15, 5]
        }
        content_df = pd.DataFrame(content_data)
        
        fig = px.pie(
            content_df,
            values='占比',
            names='学习内容',
            title='学习内容分布'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 学习效率评估
        st.write("#### 学习效率评估")
        efficiency_data = {
            '学习环境': ['安静环境', '嘈杂环境', '户外环境', '图书馆', '咖啡厅'],
            '效率评分': [9.2, 6.5, 7.8, 8.9, 7.2]
        }
        efficiency_df = pd.DataFrame(efficiency_data)
        
        fig = px.bar(
            efficiency_df,
            x='学习环境',
            y='效率评分',
            title='不同环境学习效率评估',
            color='效率评分',
            color_continuous_scale=px.colors.sequential.Plasma
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 改进建议选项卡
    with behavior_tabs[2]:
        st.write("### 学习行为改进建议")
        
        # 显示改进建议
        with st.container():
            st.info("#### 时间管理优化")
            st.write("""
            1. **制定合理的学习计划**：根据个人精力分布，将重要内容安排在精力充沛的时段
            2. **使用番茄工作法**：25分钟专注学习，5分钟短暂休息
            3. **建立每日例行学习**：固定时间段专门用于学习，形成习惯
            4. **减少无效学习时间**：避免边学习边刷手机等分散注意力的行为
            """)
        
        with st.container():
            st.success("#### 学习方法改进")
            st.write("""
            1. **主动学习法**：提前预习，带着问题学习
            2. **费曼学习法**：学会向他人解释所学内容，检验理解程度
            3. **间隔重复**：科学安排复习时间，提高记忆效果
            4. **思维导图**：构建知识体系，加深理解
            """)
        
        with st.container():
            st.warning("#### 专注力提升")
            st.write("""
            1. **环境优化**：选择安静、整洁的学习环境
            2. **减少干扰**：学习时关闭社交媒体通知
            3. **冥想训练**：每天进行5-10分钟的专注力训练
            4. **适当休息**：避免长时间连续学习导致的注意力下降
            """)
        
        with st.container():
            st.error("#### 学习动力维持")
            st.write("""
            1. **设定明确目标**：将大目标分解为小目标，获得成就感
            2. **奖励机制**：完成学习任务后给予自己适当奖励
            3. **学习社群**：加入学习小组，相互监督和鼓励
            4. **可视化进度**：记录学习进展，看到自己的成长
            """)

def render_learning_diagnosis():
    """渲染学习诊断页面"""
    st.subheader("学习诊断")
    
    # 创建表单
    with st.form(key="diagnosis_form"):
        # 表单内容保持不变
        student_name = st.text_input("学生姓名")
        subject = st.selectbox("学科", ["数学", "语文", "英语", "物理", "化学", "生物"])
        
        # 上传成绩数据
        uploaded_file = st.file_uploader("上传成绩数据(CSV格式)", type=["csv"])
        
        # 诊断选项
        diagnosis_options = st.multiselect(
            "诊断内容",
            ["知识点掌握情况", "学习习惯分析", "学习效率评估", "学习风格识别", "学习障碍识别"],
            ["知识点掌握情况", "学习习惯分析"]
        )
        
        # 提交按钮
        submit_button = st.form_submit_button("开始诊断")
    
    # 表单外处理提交逻辑
    if submit_button:
        if not student_name:
            st.error("请输入学生姓名")
        else:
            with st.spinner("正在进行学习诊断..."):
                # 生成诊断报告
                st.success("诊断完成！")
                
                # 显示诊断结果
                st.subheader("诊断结果")
                
                # 模拟诊断数据
                diagnosis_data = generate_diagnosis_data(subject)
                
                # 知识点掌握情况
                if "知识点掌握情况" in diagnosis_options:
                    st.write("#### 知识点掌握情况")
                    
                    # 创建知识点掌握情况图表
                    fig = px.bar(
                        diagnosis_data["knowledge_points"],
                        x="knowledge_point",
                        y="mastery",
                        color="mastery",
                        color_continuous_scale=["red", "yellow", "green"],
                        labels={"knowledge_point": "知识点", "mastery": "掌握程度"},
                        title="知识点掌握程度分析"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # 学习习惯分析
                if "学习习惯分析" in diagnosis_options:
                    st.write("#### 学习习惯分析")
                    
                    # 创建学习习惯雷达图
                    fig = go.Figure()
                    
                    categories = list(diagnosis_data["learning_habits"].keys())
                    values = list(diagnosis_data["learning_habits"].values())
                    
                    fig.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name='学习习惯'
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 10]
                            )
                        ),
                        title="学习习惯雷达图"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # 学习效率评估
                if "学习效率评估" in diagnosis_options:
                    st.write("#### 学习效率评估")
                    
                    # 创建学习效率折线图
                    fig = px.line(
                        diagnosis_data["efficiency"],
                        x="date",
                        y="efficiency",
                        labels={"date": "日期", "efficiency": "学习效率"},
                        title="学习效率趋势"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # 学习风格识别
                if "学习风格识别" in diagnosis_options:
                    st.write("#### 学习风格识别")
                    
                    # 创建学习风格饼图
                    fig = px.pie(
                        values=list(diagnosis_data["learning_style"].values()),
                        names=list(diagnosis_data["learning_style"].keys()),
                        title="学习风格分布"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # 学习障碍识别
                if "学习障碍识别" in diagnosis_options:
                    st.write("#### 学习障碍识别")
                    
                    for obstacle, description in diagnosis_data["obstacles"].items():
                        st.info(f"**{obstacle}**: {description}")
                
                # 生成诊断报告
                report = generate_diagnosis_report(student_name, subject, diagnosis_data, diagnosis_options)
                
                # 表单外部使用下载按钮
                st.download_button(
                    label="下载诊断报告",
                    data=report,
                    file_name=f"{student_name}_{subject}_诊断报告.txt",
                    mime="text/plain"
                )

# 添加帮助页面
def render_help_page():
    """渲染帮助中心页面"""
    st.title("帮助中心")
    
    # 创建选项卡
    tab1, tab2, tab3, tab4 = st.tabs(["📚 使用指南", "❓ 常见问题", "🔧 故障排除", "📞 联系支持"])
    
    with tab1:
        st.subheader("使用指南")
        
        # 基础功能指南
        with st.expander("基础功能介绍", expanded=True):
            st.markdown("""
            ### 1. 数据大屏
            - 实时展示学习数据和统计信息
            - 支持多维度数据可视化
            - 提供关键指标监控
            
            ### 2. 数据分析
            - 学习行为分析
            - 趋势图表展示
            - 深度数据洞察
            
            ### 3. AI助手
            - 智能问答服务
            - 个性化学习建议
            - 学习规划辅助
            
            ### 4. 学习空间推荐
            - 物理空间预约
            - 虚拟学习平台
            - 移动学习工具
            """)
        
        # 快速入门指南
        with st.expander("快速入门"):
            st.markdown("""
            ### 第一步：账号设置
            1. 完善个人信息
            2. 设置学习目标
            3. 配置通知选项
            
            ### 第二步：功能探索
            1. 浏览数据大屏
            2. 尝试AI助手
            3. 查看学习分析
            
            ### 第三步：开始学习
            1. 选择学习空间
            2. 制定学习计划
            3. 记录学习过程
            """)
        
        # 高级功能指南
        with st.expander("高级功能说明"):
            st.markdown("""
            ### 1. 数据导出
            - 支持多种格式导出
            - 自定义导出内容
            - 批量数据处理
            
            ### 2. API集成
            - API接口说明
            - 调用示例
            - 安全认证
            
            ### 3. 自定义配置
            - 界面主题设置
            - 数据展示定制
            - 通知规则配置
            """)
    
    with tab2:
        st.subheader("常见问题解答")
        
        # 账号相关
        with st.expander("账号相关问题"):
            st.markdown("""
            **Q: 如何修改密码？**  
            A: 在设置页面的"账户设置"选项卡中可以修改密码。
            
            **Q: 忘记密码怎么办？**  
            A: 点击登录页面的"忘记密码"，通过邮箱验证重置密码。
            
            **Q: 如何更新个人信息？**  
            A: 在个人中心可以更新您的基本信息和学习偏好。
            """)
        
        # 功能相关
        with st.expander("功能相关问题"):
            st.markdown("""
            **Q: 数据分析多久更新一次？**  
            A: 系统每小时自动更新一次数据，也可手动刷新。
            
            **Q: 如何使用AI助手？**  
            A: 在AI助手页面输入您的问题，系统会智能分析并给出回答。
            
            **Q: 学习空间如何预约？**  
            A: 在学习空间推荐页面选择合适的空间和时间段进行预约。
            """)
        
        # 技术相关
        with st.expander("技术相关问题"):
            st.markdown("""
            **Q: 支持哪些浏览器？**  
            A: 推荐使用Chrome、Firefox、Edge等现代浏览器。
            
            **Q: 数据是否安全？**  
            A: 系统采用加密传输和存储，确保数据安全。
            
            **Q: 如何确保AI助手的准确性？**  
            A: AI助手基于最新的深度学习模型，持续优化更新。
            """)
    
    with tab3:
        st.subheader("故障排除")
        
        # 常见故障
        with st.expander("常见故障解决"):
            st.markdown("""
            ### 1. 页面加载问题
            - 清除浏览器缓存
            - 检查网络连接
            - 尝试刷新页面
            
            ### 2. 数据显示异常
            - 确认数据时间范围
            - 检查筛选条件
            - 重置图表设置
            
            ### 3. AI助手无响应
            - 检查API配置
            - 确认网络状态
            - 尝试重新提问
            """)
        
        # 错误代码说明
        with st.expander("错误代码说明"):
            st.markdown("""
            ### 常见错误代码
            - E001: 网络连接失败
            - E002: 认证失败
            - E003: 数据加载错误
            - E004: API调用超时
            - E005: 权限不足
            """)
        
        # 性能优化
        with st.expander("性能优化建议"):
            st.markdown("""
            ### 提升使用体验
            1. 使用推荐的浏览器版本
            2. 定期清理缓存数据
            3. 避免同时打开多个数据图表
            4. 合理设置数据查询范围
            5. 使用合适的网络环境
            """)
    
    with tab4:
        st.subheader("联系支持")
        
        # 联系方式
        st.markdown("""
        ### 技术支持
        - 邮箱：281707197@qq.com
        - 电话：17748975638
        - 工作时间：周一至周五 9:00-18:00
        
        ### 反馈建议
        我们重视您的反馈，可以通过以下方式提供建议：
        """)
        
        # 反馈表单
        with st.form("feedback_form"):
            feedback_type = st.selectbox(
                "反馈类型",
                ["功能建议", "故障报告", "使用咨询", "其他"]
            )
            description = st.text_area("详细描述")
            contact = st.text_input("联系方式（选填）")
            
            if st.form_submit_button("提交反馈"):
                st.success("感谢您的反馈！我们会尽快处理。")
        
        # 在线支持
        st.markdown("""
        ### 在线支持
        - [帮助文档](https://example.com/docs)
        - [视频教程](https://example.com/tutorials)
        - [开发者社区](https://example.com/community)
        """)

# 如果render_learning_path函数不存在，而是使用render_learning_path_recommendation
# 添加一个别名函数
def render_learning_path():
    """学习路径规划的别名函数"""
    render_learning_path_recommendation()

def sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        # 语言选择
        st.write("Language/语言")
        language = st.selectbox(
            "",
            ["中文", "English"],
            label_visibility="collapsed",
            key="language_selector"
        )
        st.session_state.language = "zh" if language == "中文" else "en"
        
        # 主题风格
        st.write("主题风格")
        theme = st.selectbox(
            "",
            ["Light", "Dark"],
            label_visibility="collapsed",
            key="theme_selector"
        )
        apply_theme(theme)
        
        # 功能选项
        st.write("选择操作")
        options = [
            ("数据大屏", "dashboard", "📊"),
            ("数据分析", "analysis", "📈"),
            ("AI助手", "ai_assistant", "🤖"),
            ("学习空间推荐", "learning_space", "🎯"),
            ("学习路径规划", "learning_path", "🗺️"),
            ("学习行为分析", "learning_behavior", "📋"),
            ("学习诊断", "learning_diagnosis", "🔍"),
            ("学习记录", "learning_tracker", "📝"),
            ("帮助中心", "help", "❓"),
            ("设置", "settings", "⚙️"),
            ("注销", "logout", "🚪")
        ]
        
        # 使用容器来改善布局
        for label, key, icon in options:
            col1, col2 = st.columns([0.2, 3])
            with col1:
                st.write(icon)
            with col2:
                if st.button(
                    label,
                    key=f"btn_{key}",
                    use_container_width=True,
                    type="secondary" if st.session_state.sidebar_option != key else "primary"
                ):
                    st.session_state.sidebar_option = key
                    st.rerun()

def render_sidebar():
    """渲染侧边栏（旧版本兼容）"""
    sidebar()

def render_analysis():
    """渲染数据分析页面"""
    st.title("数据分析")
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["📊 基础分析", "📈 趋势分析", "🔍 深度洞察"])
    
    with tab1:
        st.subheader("基础数据分析")
        
        # 显示基础统计数据
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="总学习人数",
                value="1,234",
                delta="12%",
                help="过去30天的累计学习人数"
            )
            
        with col2:
            st.metric(
                label="平均学习时长",
                value="45分钟/天",
                delta="5分钟",
                help="每人每天平均学习时长"
            )
            
        with col3:
            st.metric(
                label="知识点掌握率",
                value="78%",
                delta="-2%",
                help="知识点测试通过率"
            )
            
        # 添加学习时间分布图
        st.subheader("学习时间分布")
        
        # 生成示例数据
        hours = list(range(24))
        study_count = np.random.poisson(lam=20, size=24)
        
        # 创建柱状图
        fig = go.Figure(data=[
            go.Bar(
                x=hours,
                y=study_count,
                marker_color='#1E88E5'
            )
        ])
        
        fig.update_layout(
            title="24小时学习人数分布",
            xaxis_title="小时",
            yaxis_title="学习人数"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        st.subheader("趋势分析")
        
        # 生成趋势数据
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        trend_data = pd.DataFrame({
            'date': dates,
            'daily_users': np.random.normal(100, 10, 30),
            'avg_duration': np.random.normal(45, 5, 30)
        })
        
        # 创建趋势图
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=trend_data['date'],
            y=trend_data['daily_users'],
            name='日活跃用户',
            line=dict(color='#1E88E5')
        ))
        
        fig.add_trace(go.Scatter(
            x=trend_data['date'],
            y=trend_data['avg_duration'],
            name='平均时长(分钟)',
            line=dict(color='#43A047')
        ))
        
        fig.update_layout(
            title="30天趋势分析",
            xaxis_title="日期",
            yaxis_title="数值",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    with tab3:
        st.subheader("深度洞察")
        
        # 添加AI分析按钮
        if st.button("生成AI分析报告"):
            with st.spinner("AI正在分析数据..."):
                try:
                    # 调用AI接口生成分析
                    analysis = """
                    ### 数据分析报告
                    
                    #### 主要发现
                    1. 用户活跃度稳定增长，环比增长12%
                    2. 平均学习时长略有提升，达到45分钟/天
                    3. 知识点掌握率出现小幅下降
                    
                    #### 改进建议
                    1. 优化学习内容难度梯度
                    2. 增加互动学习环节
                    3. 加强个性化学习指导
                    """
                    
                    st.markdown(analysis)
                    
                except Exception as e:
                    st.error(f"生成分析报告失败: {str(e)}")
        
        # 添加数据导出功能
        if st.button("导出分析数据"):
            st.success("数据已导出！")

def render_api_settings():
    """渲染API配置页面"""
    st.title("DeepSeek API配置")
    
    # 从session_state或环境变量获取当前配置
    current_api_key = st.session_state.get('deepseek_api_key', '')
    current_api_url = st.session_state.get('deepseek_api_url', 'https://api.deepseek.com')
    current_model = st.session_state.get('deepseek_model', 'deepseek-chat')
    
    # 显示当前API状态
    if current_api_key:
        st.success("API状态: 已配置")
        # 显示部分隐藏的API密钥
        masked_key = current_api_key[:4] + "*" * (len(current_api_key) - 8) + current_api_key[-4:]
        st.info(f"当前API密钥: {masked_key}")
    else:
        st.warning("API状态: 未配置")
    
    # API配置表单
    with st.form("deepseek_api_settings_form", clear_on_submit=False):
        # API密钥输入
        api_key = st.text_input(
            "DeepSeek API密钥",
            type="password",
            value=current_api_key,
            help="请输入您的DeepSeek API密钥",
            key="deepseek_api_key_input"
        )
        
        # API基础URL
        api_url = st.text_input(
            "API基础URL",
            value=current_api_url,
            help="DeepSeek API的基础URL",
            key="deepseek_api_url_input"
        )
        
        # 模型选择
        model = st.selectbox(
            "DeepSeek模型",
            ["deepseek-chat", "deepseek-coder", "deepseek-ai"],
            index=["deepseek-chat", "deepseek-coder", "deepseek-ai"].index(current_model),
            help="选择要使用的DeepSeek模型",
            key="deepseek_model_select"
        )
        
        cols = st.columns([1, 1])
        with cols[0]:
            submit = st.form_submit_button("保存API设置")
        with cols[1]:
            test_button = st.form_submit_button("测试API连接")
        
        if submit:
            # 保存前检查API密钥格式
            api_key = api_key.strip()  # 移除空格
            if not api_key.startswith('Bearer '):
                api_key = f"Bearer {api_key}"
            
            # 保存API设置
            st.session_state.deepseek_api_key = api_key
            st.session_state.deepseek_api_url = api_url.rstrip('/')  # 移除末尾的斜杠
            st.session_state.deepseek_model = model
            
            # 更新环境变量
            os.environ['DEEPSEEK_API_KEY'] = api_key
            os.environ['DEEPSEEK_API_URL'] = api_url.rstrip('/')
            os.environ['DEEPSEEK_MODEL'] = model
            
            st.success("API设置已保存！")
            st.write("当前配置:")
            st.write(f"- API URL: {api_url}")
            st.write(f"- 模型: {model}")
            st.write(f"- API密钥: {api_key[:10]}...")
            
            time.sleep(1)
            st.rerun()
        
        if test_button:
            try:
                # 构造测试请求
                headers = {
                    "Authorization": f"Bearer {api_key.strip()}", # 确保移除可能的空格
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                # 构造测试请求
                test_data = {
                    "model": "deepseek-chat",  # 使用具体的模型名称
                    "messages": [
                        {"role": "user", "content": "Hello"}
                    ],
                    "max_tokens": 50,
                    "temperature": 0.7
                }
                
                with st.spinner("正在测试API连接..."):
                    # 打印请求信息以便调试
                    st.write("请求URL:", f"{api_url}/v1/chat/completions")
                    st.write("请求头:", {k: v[:10] + '...' if k == 'Authorization' else v for k, v in headers.items()})
                    
                    response = requests.post(
                        f"{api_url}/v1/chat/completions",
                        headers=headers,
                        json=test_data,
                        timeout=10
                    )
                    
                    # 打印完整的响应信息
                    st.write("响应状态码:", response.status_code)
                    st.write("响应内容:", response.text)
                    
                    if response.status_code == 200:
                        st.success("API连接测试成功！")
                    else:
                        st.error(f"API测试失败: {response.status_code}")
                        st.error(f"错误信息: {response.text}")
                        
            except requests.exceptions.RequestException as e:
                st.error(f"API连接测试失败: {str(e)}")
                st.info("请检查API密钥和网络连接")

def render_usage_statistics():
    """渲染使用统计页面"""
    st.title("使用统计")
    
    # 从session_state获取API使用统计
    api_usage = st.session_state.get('api_usage', {
        'calls': 0,
        'tokens': 0,
        'last_call': None
    })
    
    # 显示统计数据
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="API调用次数",
            value=api_usage['calls'],
            delta=None,
            help="累计API调用总次数"
        )
    
    with col2:
        st.metric(
            label="Token使用量",
            value=api_usage['tokens'],
            delta=None,
            help="累计Token使用总量"
        )
    
    with col3:
        last_call = api_usage['last_call']
        last_call_str = last_call.strftime("%Y-%m-%d %H:%M:%S") if last_call else "从未使用"
        st.metric(
            label="最后调用时间",
            value=last_call_str,
            delta=None,
            help="最近一次API调用时间"
        )
    
    # 添加使用趋势图
    st.subheader("使用趋势")
    
    # 生成示例数据（实际应用中应该使用真实数据）
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    data = pd.DataFrame({
        'date': dates,
        'api_calls': np.random.randint(10, 100, size=30),
        'tokens': np.random.randint(1000, 5000, size=30)
    })
    
    # 创建API调用趋势图
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=data['date'],
        y=data['api_calls'],
        mode='lines+markers',
        name='API调用次数',
        line=dict(color='#1E88E5', width=2),
        marker=dict(size=6)
    ))
    
    fig1.update_layout(
        title="每日API调用次数",
        xaxis_title="日期",
        yaxis_title="调用次数",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # 创建Token使用趋势图
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=data['date'],
        y=data['tokens'],
        mode='lines+markers',
        name='Token使用量',
        line=dict(color='#43A047', width=2),
        marker=dict(size=6)
    ))
    
    fig2.update_layout(
        title="每日Token使用量",
        xaxis_title="日期",
        yaxis_title="Token数量",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # 添加使用记录表格
    st.subheader("最近使用记录")
    
    # 生成示例使用记录（实际应用中应该使用真实数据）
    records = pd.DataFrame({
        '时间': pd.date_range(end=datetime.now(), periods=10, freq='H'),
        '操作类型': ['对话生成', '代码分析', '文本总结'] * 3 + ['对话生成'],
        'Token数': np.random.randint(100, 500, size=10),
        '状态': ['成功'] * 8 + ['失败'] * 2
    })
    
    # 为状态添加颜色标记
    def color_status(val):
        color = 'green' if val == '成功' else 'red'
        return f'color: {color}'
    
    # 显示带样式的表格
    st.dataframe(
        records.style.applymap(color_status, subset=['状态']),
        use_container_width=True
    )
    
    # 添加导出选项
    if st.button("导出统计数据"):
        # 这里应该实现导出逻辑
        st.success("统计数据已导出！")
        
    # 添加重置选项
    if st.button("重置统计数据"):
        if st.session_state.get('api_usage'):
            st.session_state.api_usage = {
                'calls': 0,
                'tokens': 0,
                'last_call': None
            }
            st.success("统计数据已重置！")
            st.rerun()

def render_learning_tracker():
    """渲染学习记录与激励机制模块"""
    st.title("学习记录与激励系统")
    
    # 初始化session state
    if 'learning_records' not in st.session_state:
        st.session_state.learning_records = {
            'daily_goals': {},  # 每日目标
            'completed_tasks': [],  # 已完成任务
            'points': 100,  # 初始积分
            'streak_days': 0,  # 连续学习天数
            'penalties': [],  # 惩罚记录
            'rewards': []  # 奖励记录
        }
    
    # 侧边栏：显示当前状态
    with st.sidebar:
        st.subheader("📊 学习状态")
        st.metric("当前积分", st.session_state.learning_records['points'])
        st.metric("连续学习天数", st.session_state.learning_records['streak_days'])
        
        # 显示警告区
        if st.session_state.learning_records['points'] < 60:
            st.warning("⚠️ 积分偏低，请注意保持学习频率！")
        elif st.session_state.learning_records['points'] > 150:
            st.success("🌟 表现优秀，继续保持！")
    
    # 主要内容区
    tab1, tab2, tab3 = st.tabs(["📝 每日任务", "🎯 目标追踪", "📈 学习分析"])
    
    with tab1:
        st.subheader("今日学习任务")
        
        # 添加新任务
        with st.form("add_task_form"):
            task = st.text_input("添加新任务")
            estimated_time = st.slider("预计用时(分钟)", 15, 180, 60, 15)
            priority = st.select_slider("优先级", options=["低", "中", "高"])
            
            if st.form_submit_button("添加任务"):
                new_task = {
                    'task': task,
                    'estimated_time': estimated_time,
                    'priority': priority,
                    'status': 'pending',
                    'created_at': datetime.now()
                }
                st.session_state.learning_records['daily_goals'][task] = new_task
                st.success("任务已添加！")
        
        # 显示任务列表
        for task, details in st.session_state.learning_records['daily_goals'].items():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📌 {task}")
                st.caption(f"预计用时: {details['estimated_time']}分钟 | 优先级: {details['priority']}")
            
            with col2:
                if details['status'] == 'pending':
                    if st.button("完成", key=f"complete_{task}"):
                        details['status'] = 'completed'
                        details['completed_at'] = datetime.now()
                        st.session_state.learning_records['points'] += 10
                        st.session_state.learning_records['completed_tasks'].append(details)
                        st.success("任务完成！获得10积分")
                        st.rerun()
            
            with col3:
                if details['status'] == 'pending':
                    if st.button("放弃", key=f"abandon_{task}"):
                        details['status'] = 'abandoned'
                        st.session_state.learning_records['points'] -= 5
                        penalty = {
                            'task': task,
                            'points': -5,
                            'reason': '主动放弃任务',
                            'time': datetime.now()
                        }
                        st.session_state.learning_records['penalties'].append(penalty)
                        st.warning("任务已放弃，扣除5积分")
                        st.rerun()
    
    with tab2:
        st.subheader("学习目标追踪")
        
        # 显示周/月目标完成情况
        weekly_completion = len([t for t in st.session_state.learning_records['completed_tasks'] 
                               if t['completed_at'] > datetime.now() - timedelta(days=7)])
        monthly_completion = len([t for t in st.session_state.learning_records['completed_tasks']
                                if t['completed_at'] > datetime.now() - timedelta(days=30)])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("本周完成任务", weekly_completion)
        with col2:
            st.metric("本月完成任务", monthly_completion)
        
        # 显示惩罚记录
        st.subheader("惩罚记录")
        if st.session_state.learning_records['penalties']:
            for penalty in st.session_state.learning_records['penalties']:
                st.error(
                    f"时间: {penalty['time'].strftime('%Y-%m-%d %H:%M')}\n"
                    f"任务: {penalty['task']}\n"
                    f"原因: {penalty['reason']}\n"
                    f"扣除积分: {penalty['points']}"
                )
    
    with tab3:
        st.subheader("学习数据分析")
        
        # 生成分析数据
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        completion_data = pd.DataFrame({
            'date': dates,
            'completed_tasks': np.random.randint(0, 8, size=30),
            'study_hours': np.random.uniform(1, 6, size=30)
        })
        
        # 绘制完成任务趋势
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=completion_data['date'],
            y=completion_data['completed_tasks'],
            mode='lines+markers',
            name='完成任务数',
            line=dict(color='#1E88E5', width=2)
        ))
        
        fig1.update_layout(
            title="每日完成任务数趋势",
            xaxis_title="日期",
            yaxis_title="任务数量"
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # 添加学习建议
        st.subheader("AI学习建议")
        if st.button("生成学习建议"):
            with st.spinner("AI分析中..."):
                try:
                    deepseek_ai = DeepSeekAI()
                    prompt = f"""
                    基于以下学习数据生成个性化学习建议：
                    1. 当前积分：{st.session_state.learning_records['points']}
                    2. 连续学习天数：{st.session_state.learning_records['streak_days']}
                    3. 本周完成任务数：{weekly_completion}
                    4. 本月完成任务数：{monthly_completion}
                    5. 是否有惩罚记录：{'是' if st.session_state.learning_records['penalties'] else '否'}
                    
                    请提供：
                    1. 学习表现分析
                    2. 需要改进的方面
                    3. 具体的改进建议
                    4. 鼓励性话语
                    """
                    
                    response = deepseek_ai.sync_generate_response(
                        [{"role": "user", "content": prompt}],
                        temperature=0.7
                    )
                    
                    if "error" not in response:
                        st.write(response["choices"][0]["message"]["content"])
                    else:
                        st.error("生成建议失败，请稍后再试")
                        
                except Exception as e:
                    st.error(f"生成建议时出错: {str(e)}")

def render_learning_behavior():
    """渲染学习行为分析页面"""
    st.title("学习行为分析")
    
    # 初始化学习行为数据
    if 'learning_behavior' not in st.session_state:
        st.session_state.learning_behavior = {
            'study_time': [],  # 学习时长记录
            'focus_rate': [],  # 专注度记录
            'completion_rate': [],  # 任务完成率
            'interaction_count': [],  # 互动次数
            'dates': []  # 对应日期
        }
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["📊 行为概览", "🔍 详细分析", "💡 改进建议"])
    
    with tab1:
        st.subheader("学习行为概览")
        
        # 显示关键指标
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="平均学习时长",
                value="2.5小时/天",
                delta="0.5小时",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                label="平均专注度",
                value="85%",
                delta="5%",
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                label="任务完成率",
                value="78%",
                delta="-2%",
                delta_color="inverse"
            )
        
        with col4:
            st.metric(
                label="知识点掌握度",
                value="82%",
                delta="3%",
                delta_color="normal"
            )
        
        # 添加行为趋势图
        st.subheader("学习行为趋势")
        
        # 生成示例数据
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'study_time': np.random.normal(2.5, 0.5, 30),  # 学习时长
            'focus_rate': np.random.normal(85, 5, 30),     # 专注度
            'completion_rate': np.random.normal(78, 8, 30), # 完成率
            'interaction': np.random.randint(10, 50, 30)    # 互动次数
        })
        
        # 绘制趋势图
        fig = go.Figure()
        
        # 添加学习时长曲线
        fig.add_trace(go.Scatter(
            x=data['date'],
            y=data['study_time'],
            name='学习时长(小时)',
            line=dict(color='#1E88E5', width=2)
        ))
        
        # 添加专注度曲线
        fig.add_trace(go.Scatter(
            x=data['date'],
            y=data['focus_rate'],
            name='专注度(%)',
            line=dict(color='#43A047', width=2)
        ))
        
        fig.update_layout(
            title="学习行为趋势分析",
            xaxis_title="日期",
            yaxis_title="数值",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("详细行为分析")
        
        # 时间分布分析
        st.write("##### 学习时间分布")
        time_data = pd.DataFrame({
            'hour': range(24),
            'study_count': np.random.poisson(lam=5, size=24)
        })
        
        fig_time = go.Figure(data=[
            go.Bar(
                x=time_data['hour'],
                y=time_data['study_count'],
                marker_color='#1E88E5'
            )
        ])
        
        fig_time.update_layout(
            title="每日学习时间分布",
            xaxis_title="小时",
            yaxis_title="学习次数"
        )
        
        st.plotly_chart(fig_time, use_container_width=True)
        
        # 学习行为模式分析
        st.write("##### 学习行为模式")
        col1, col2 = st.columns(2)
        
        with col1:
            # 学习方式分布
            labels = ['视频学习', '练习题', '阅读材料', '互动讨论']
            values = [40, 25, 20, 15]
            
            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig_pie.update_layout(title="学习方式分布")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # 知识点掌握情况
            subjects = ['数学', '物理', '化学', '生物', '英语']
            scores = [85, 78, 92, 88, 76]
            
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=scores,
                theta=subjects,
                fill='toself'
            ))
            
            fig_radar.update_layout(title="知识点掌握情况")
            st.plotly_chart(fig_radar, use_container_width=True)
    
    with tab3:
        st.subheader("学习改进建议")
        
        # 生成AI建议
        if st.button("生成个性化建议"):
            with st.spinner("AI分析中..."):
                try:
                    deepseek_ai = DeepSeekAI()
                    prompt = """
                    基于以下学习行为数据生成个性化学习建议：
                    1. 平均每日学习时长：2.5小时
                    2. 平均专注度：85%
                    3. 任务完成率：78%
                    4. 主要学习时间段：晚上8点-10点
                    5. 最常用学习方式：视频学习(40%)
                    
                    请从以下几个方面提供建议：
                    1. 时间管理
                    2. 学习效率提升
                    3. 知识巩固方法
                    4. 学习方式多样化
                    """
                    
                    response = deepseek_ai.sync_generate_response(
                        [{"role": "user", "content": prompt}],
                        temperature=0.7
                    )
                    
                    if "error" not in response:
                        st.write(response["choices"][0]["message"]["content"])
                    else:
                        st.error("生成建议失败，请稍后再试")
                        
                except Exception as e:
                    st.error(f"生成建议时出错: {str(e)}")
        
        # 添加手动建议
        st.write("##### 通用改进建议")
        st.info("""
        1. 建议增加每日学习时长至3-4小时
        2. 可以尝试番茄工作法提高专注度
        3. 建议增加练习题的比重
        4. 可以尝试早晨学习，提高学习效率
        5. 建议多参与互动讨论，加深理解
        """)

def render_learning_space():
    """渲染学习空间推荐页面"""
    st.title("学习空间推荐")
    
    # 添加AI推荐部分
    with st.expander("🤖 获取AI个性化空间推荐", expanded=True):
        st.write("请回答以下问题，AI将为您推荐最适合的学习空间")
        
        # 创建表单收集用户信息
        with st.form("space_recommendation_form"):
            # 学习目的
            learning_purpose = st.selectbox(
                "您的主要学习目的是什么？",
                ["课程学习", "自主学习", "小组讨论", "实验实践", "创新研究"]
            )
            
            # 学习方式偏好
            learning_style = st.multiselect(
                "您偏好的学习方式是？（可多选）",
                ["安静独立", "互动交流", "动手实践", "多媒体辅助", "沉浸式体验"],
                default=["安静独立"]
            )
            
            # 学习时间段
            time_preference = st.select_slider(
                "您计划的学习时间段是？",
                options=["早晨", "上午", "下午", "晚上", "深夜"],
                value="下午"
            )
            
            # 空间要求
            space_requirements = st.multiselect(
                "对学习空间有什么特殊要求？（可多选）",
                ["网络条件好", "设备齐全", "环境安静", "空间宽敞", "交通便利"],
                default=["环境安静"]
            )
            
            submit = st.form_submit_button("获取推荐")
        
        if submit:
            with st.spinner("AI正在分析最适合您的学习空间..."):
                # 构建提示信息
                prompt = f"""
                请根据以下学习者的需求特征，推荐最适合的学习空间（可以是物理空间、虚拟空间或泛在空间的组合）：
                
                学习目的：{learning_purpose}
                学习方式偏好：{', '.join(learning_style)}
                时间段：{time_preference}
                空间要求：{', '.join(space_requirements)}
                
                请提供：
                1. 推荐的具体空间组合
                2. 推荐理由
                3. 使用建议
                4. 注意事项
                
                回答要具体且有针对性，并考虑物理空间、虚拟空间和泛在空间的优势互补。
                """
                
                # 调用AI生成推荐
                ai = DouBaoAI()  # 或其他AI实现
                messages = [
                    {"role": "system", "content": "你是一个专业的学习空间推荐专家，擅长根据学习者的具体需求推荐最适合的学习空间组合。"},
                    {"role": "user", "content": prompt}
                ]
                
                response = ai.generate_response(messages)
                
                if "error" in response:
                    st.error(f"生成推荐时出现错误: {response['error']}")
                else:
                    try:
                        recommendation = response["choices"][0]["message"]["content"]
                        
                        # 使用卡片样式显示推荐结果
                        st.success("✨ AI已为您生成个性化的空间推荐")
                        
                        # 使用列布局展示推荐内容
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(recommendation)
                        
                        with col2:
                            st.info("""
                            💡 **小贴士**
                            
                            - 可以尝试不同空间的组合使用
                            - 根据实际情况灵活调整
                            - 定期评估空间使用效果
                            - 收集反馈持续优化
                            """)
                    
                    except (KeyError, IndexError):
                        st.error("处理AI响应时出现错误，请稍后再试。")
    
    # 原有的空间展示代码保持不变
    space_tabs = st.tabs(["🏫 物理空间", "🖥️ 虚拟空间", "🌐 泛在空间"])
    
    # 物理空间选项卡
    with space_tabs[0]:
        st.write("### 物理学习空间")
        
        # 校内学习空间
        st.write("#### 校内学习空间")
        indoor_cols = st.columns(3)
        
        # 将校内空间分组显示
        indoor_spaces = list(LearningSpaceModel.PHYSICAL_SPACES['indoor'].items())
        for i, (space_id, space_info) in enumerate(indoor_spaces):
            with indoor_cols[i % 3]:
                st.info(f"**{space_info['name']}**")
                st.write(space_info['description'])
                st.metric("使用人数", f"{random.randint(10, 100)}人")
                st.metric("空间面积", f"{random.randint(50, 200)}㎡")
                st.metric("设备完善度", f"{random.randint(70, 95)}%")
                st.write(f"推荐指数: {'⭐' * random.randint(3, 5)}")
        
        # 校外学习空间
        st.write("#### 校外学习空间")
        outdoor_cols = st.columns(3)
        
        # 将校外空间分组显示
        outdoor_spaces = list(LearningSpaceModel.PHYSICAL_SPACES['outdoor'].items())
        for i, (space_id, space_info) in enumerate(outdoor_spaces):
            with outdoor_cols[i % 3]:
                st.success(f"**{space_info['name']}**")
                st.write(space_info['description'])
                st.metric("距离校园", f"{random.randint(1, 10)}公里")
                st.metric("开放时间", f"{random.choice(['全天', '9:00-17:00', '8:00-22:00'])}")
                st.write(f"适用人群: {random.choice(['所有学生', '研究生', '本科生', '所有人'])}")
                st.write(f"推荐指数: {'⭐' * random.randint(3, 5)}")
        
        # 添加物理空间说明
        st.info("""
        **物理学习空间**是指具有实体形态的学习场所，包括校内的传统教室、图书馆、实验室等，
        以及校外的社区、家庭、企业等学习环境。这些空间为学习者提供了不同类型的学习体验和资源。
        """)
    
    # 虚拟空间选项卡
    with space_tabs[1]:
        st.write("### 虚拟学习空间")
        
        # 显示虚拟空间分类
        virtual_cols = st.columns(2)
        
        # 将虚拟空间分组显示
        virtual_spaces = list(LearningSpaceModel.VIRTUAL_SPACES.items())
        for i, (space_id, space_info) in enumerate(virtual_spaces):
            with virtual_cols[i % 2]:
                st.warning(f"**{space_info['name']}**")
                
                # 显示功能特点
                st.write("**功能特点:**")
                for feature in space_info['features']:
                    st.write(f"- {feature}")
                
                # 显示指标
                if 'active_users' in space_info:
                    st.metric("活跃用户", f"{space_info['active_users']}人")
                if 'course_count' in space_info:
                    st.metric("课程数量", f"{space_info['course_count']}个")
                if 'satisfaction' in space_info:
                    st.metric("满意度评分", f"{space_info['satisfaction']:.1f}/5.0")
                if 'resource_count' in space_info:
                    st.metric("资源数量", f"{space_info['resource_count']}个")
                if 'daily_visits' in space_info:
                    st.metric("日访问量", f"{space_info['daily_visits']}次")
                if 'experiment_count' in space_info:
                    st.metric("实验数量", f"{space_info['experiment_count']}个")
                if 'active_projects' in space_info:
                    st.metric("活跃项目", f"{space_info['active_projects']}个")
                if 'team_count' in space_info:
                    st.metric("团队数量", f"{space_info['team_count']}个")
                
                st.write(f"推荐指数: {'⭐' * random.randint(3, 5)}")
        
        # 添加虚拟空间说明
        st.info("""
        **虚拟学习空间**是指借助数字技术构建的在线学习环境，包括在线课堂、数字图书馆、虚拟实验室等。
        这些空间突破了时间和空间的限制，为学习者提供了更加灵活、个性化的学习体验。
        """)
    
    # 泛在空间选项卡
    with space_tabs[2]:
        st.write("### 泛在学习空间")
        
        # 数据层
        st.write("#### 数据层")
        data_cols = st.columns(4)
        
        # 物理空间数据
        with data_cols[0]:
            data_info = LearningSpaceModel.UBIQUITOUS_SPACES['data_layer']['physical_data']
            st.info(f"**{data_info['name']}**")
            st.metric("活跃学习者", f"{data_info['active_learners']}人")
            st.metric("空间利用率", f"{data_info['space_usage']*100:.1f}%")
        
        # 虚拟空间数据
        with data_cols[1]:
            data_info = LearningSpaceModel.UBIQUITOUS_SPACES['data_layer']['virtual_data']
            st.info(f"**{data_info['name']}**")
            st.metric("问答会话数", f"{data_info['qa_sessions']}次")
            st.metric("资源利用率", f"{data_info['resource_usage']*100:.1f}%")
        
        # 学习行为数据
        with data_cols[2]:
            data_info = LearningSpaceModel.UBIQUITOUS_SPACES['data_layer']['learning_behavior']
            st.info(f"**{data_info['name']}**")
            st.metric("个性化路径", f"{data_info['personalized_paths']}条")
            st.metric("参与度", f"{data_info['engagement_rate']*100:.1f}%")
        
        # 交互数据
        with data_cols[3]:
            data_info = LearningSpaceModel.UBIQUITOUS_SPACES['data_layer']['interaction_data']
            st.info(f"**{data_info['name']}**")
            st.metric("响应时间", data_info['response_time'])
            st.metric("交互次数", f"{data_info['interaction_count']}次")
        
        # 服务层
        st.write("#### 服务层")
        service_cols = st.columns(3)
        
        # 学习服务
        with service_cols[0]:
            service_info = LearningSpaceModel.UBIQUITOUS_SPACES['service_layer']['learning_services']
            st.success(f"**{service_info['name']}**")
            st.write("**功能特点:**")
            for feature in service_info['features']:
                st.write(f"- {feature}")
            st.metric("活跃用户", f"{service_info['active_users']}人")
        
        # 数据服务
        with service_cols[1]:
            service_info = LearningSpaceModel.UBIQUITOUS_SPACES['service_layer']['data_services']
            st.success(f"**{service_info['name']}**")
            st.write("**功能特点:**")
            for feature in service_info['features']:
                st.write(f"- {feature}")
            st.metric("数据点数", f"{service_info['data_points']}个")
        
        # 集成服务
        with service_cols[2]:
            service_info = LearningSpaceModel.UBIQUITOUS_SPACES['service_layer']['integration_services']
            st.success(f"**{service_info['name']}**")
            st.write("**功能特点:**")
            for feature in service_info['features']:
                st.write(f"- {feature}")
            st.metric("连接系统", f"{service_info['connected_systems']}个")
        
        # 应用层
        st.write("#### 应用层")
        app_cols = st.columns(3)
        
        # AI导师服务
        with app_cols[0]:
            app_info = LearningSpaceModel.UBIQUITOUS_SPACES['application_layer']['ai_tutor']
            st.warning(f"**{app_info['name']}**")
            st.write("**功能特点:**")
            for feature in app_info['features']:
                st.write(f"- {feature}")
            st.metric("活跃会话", f"{app_info['active_sessions']}个")
        
        # 资源访问服务
        with app_cols[1]:
            app_info = LearningSpaceModel.UBIQUITOUS_SPACES['application_layer']['resource_access']
            st.warning(f"**{app_info['name']}**")
            st.write("**功能特点:**")
            for feature in app_info['features']:
                st.write(f"- {feature}")
            st.metric("日请求量", f"{app_info['daily_requests']}次")
        
        # 学习分析服务
        with app_cols[2]:
            app_info = LearningSpaceModel.UBIQUITOUS_SPACES['application_layer']['learning_analytics']
            st.warning(f"**{app_info['name']}**")
            st.write("**功能特点:**")
            for feature in app_info['features']:
                st.write(f"- {feature}")
            st.metric("分析任务", f"{app_info['analysis_tasks']}个")
        
        # 添加泛在空间说明
        st.info("""
        **泛在学习空间**是一种无处不在的学习环境，它整合了物理和虚拟空间的数据和服务，
        通过三层架构（数据层、服务层、应用层）为学习者提供随时随地的智能学习支持。
        """)

def render_settings():
    """渲染设置页面"""
    st.title("系统设置")
    
    # 创建设置选项卡
    tab1, tab2, tab3 = st.tabs(["👤 账户设置", "🔑 API配置", "📊 使用统计"])
    
    with tab1:
        st.subheader("账户设置")
        
        # 个人信息设置
        with st.expander("个人信息", expanded=True):
            # 基本信息
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("用户名", value=st.session_state.get("username", ""))
                email = st.text_input("邮箱", value=st.session_state.get("email", ""))
            with col2:
                role = st.selectbox("角色", ["学生", "教师", "管理员"])
                department = st.text_input("所属院系")
        
            # 修改密码
            st.subheader("修改密码")
            old_password = st.text_input("当前密码", type="password")
            new_password = st.text_input("新密码", type="password")
            confirm_password = st.text_input("确认新密码", type="password")
            
            if st.button("更新密码"):
                if new_password != confirm_password:
                    st.error("新密码与确认密码不匹配！")
                elif not old_password:
                    st.error("请输入当前密码！")
                else:
                    # 这里应该添加实际的密码更新逻辑
                    st.success("密码更新成功！")
        
        # 通知设置
        with st.expander("通知设置"):
            st.checkbox("接收系统通知", value=True)
            st.checkbox("接收学习提醒", value=True)
            st.checkbox("接收活动通知", value=True)
            st.checkbox("接收周报", value=True)
            
            # 通知方式
            st.multiselect(
                "通知方式",
                ["邮件", "短信", "站内信"],
                ["邮件", "站内信"]
            )
    
    with tab2:
        st.subheader("API配置")
        
        # DeepSeek API设置
        with st.expander("DeepSeek API配置", expanded=True):
            api_key = st.text_input(
                "API密钥",
                type="password",
                value=st.session_state.get("api_key", ""),
                help="请输入您的DeepSeek API密钥"
            )
            
            model = st.selectbox(
                "选择模型",
                ["DeepSeek-7B", "DeepSeek-67B", "DeepSeek-Chat"],
                help="选择要使用的AI模型"
            )
            
            temperature = st.slider(
                "温度",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                help="控制AI回答的创造性程度"
            )
            
            if st.button("测试API连接"):
                if not api_key:
                    st.error("请输入API密钥！")
                else:
                    with st.spinner("正在测试连接..."):
                        try:
                            # 这里应该添加实际的API测试逻辑
                            st.success("API连接测试成功！")
                        except Exception as e:
                            st.error(f"API连接测试失败：{str(e)}")
        
        # 其他API设置
        with st.expander("其他API设置"):
            st.text_input("数据分析API地址")
            st.text_input("学习空间API地址")
            st.number_input("API请求超时时间（秒）", value=30)
    
    with tab3:
        st.subheader("使用统计")
        
        # 生成示例使用数据
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        usage_data = pd.DataFrame({
            'date': dates,
            'api_calls': np.random.randint(100, 1000, 30),
            'data_queries': np.random.randint(50, 500, 30)
        })
        
        # 显示使用统计图表
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=usage_data['date'],
            y=usage_data['api_calls'],
            name='API调用次数',
            line=dict(color='#1E88E5')
        ))
        
        fig.add_trace(go.Scatter(
            x=usage_data['date'],
            y=usage_data['data_queries'],
            name='数据查询次数',
            line=dict(color='#43A047')
        ))
        
        fig.update_layout(
            title="30天使用统计",
            xaxis_title="日期",
            yaxis_title="次数",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示使用限制
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="API调用限额",
                value="10,000次/月",
                delta="已用8,234次",
                delta_color="normal"
            )
        with col2:
            st.metric(
                label="数据存储限额",
                value="100GB",
                delta="已用65GB",
                delta_color="normal"
            )
        
        # 导出使用报告
        if st.button("导出使用报告"):
            st.success("报告已导出！")

def handle_logout():
    """处理用户注销"""
    # 清除所有session状态
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # 显示注销成功消息
    st.success("您已成功注销！")
    
    # 重定向到登录页面
    st.session_state.page = "login"
    st.rerun()

def render_logout_confirm():
    """渲染注销确认页面"""
    st.title("注销确认")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.write("### 确定要注销吗？")
        st.write("注销后需要重新登录才能继续使用系统。")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认注销", type="primary"):
                handle_logout()
        with col2:
            if st.button("取消", type="secondary"):
                st.session_state.sidebar_option = "dashboard"
                st.rerun()

# 在其他AI类的定义后添加豆包AI类
class DouBaoAI(BaseAI):
    """豆包AI实现"""
    def __init__(self):
        super().__init__()
        self.name = "豆包"
        # 使用正确的API密钥
        self.api_key = "ALTAK-wkA24WktBRKDpY6tDo8Lh"  # API Key
        self.secret_key = "1ce45e39bb90c1a26460babd8a719db3fa01cd56"  # Secret Key
        self.access_token = None
        self.base_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
        
        # 初始化时获取access token
        self._refresh_token()
        
        self.headers = {
            "Content-Type": "application/json"
        }

    def _refresh_token(self):
        """获取access token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        try:
            response = requests.post(url, params=params)
            result = response.json()
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                st.success("成功获取access token")
            else:
                st.error(f"获取access token失败: {result.get('error_description', '未知错误')}")
                
        except Exception as e:
            st.error(f"获取access token错误: {str(e)}")

    def generate_response(self, messages, **kwargs):
        """生成回复"""
        if not self.access_token:
            self._refresh_token()
            if not self.access_token:
                return {"error": "无法获取access token"}

        try:
            url = f"{self.base_url}?access_token={self.access_token}"
            
            data = {
                "messages": messages,
                "temperature": kwargs.get('temperature', 0.7)
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"豆包API调用失败({response.status_code}): {response.text}"
                st.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"豆包API错误: {str(e)}"
            st.error(error_msg)
            return {"error": error_msg}

def generate_diagnosis_data(subject):
    """生成模拟诊断数据"""
    # 知识点掌握情况
    knowledge_points = []
    if subject == "数学":
        points = ["代数基础", "几何概念", "函数应用", "概率统计", "微积分基础"]
    elif subject == "英语":
        points = ["词汇量", "语法规则", "阅读理解", "写作能力", "听力水平"]
    elif subject == "物理":
        points = ["力学", "热学", "光学", "电磁学", "量子物理"]
    else:
        points = ["基础概念", "核心理论", "实践应用", "综合分析", "创新思维"]
    
    for point in points:
        knowledge_points.append({
            "knowledge_point": point,
            "mastery": random.uniform(0.3, 0.95)
        })
    
    # 学习习惯分析
    learning_habits = {
        "专注度": random.uniform(3, 10),
        "计划性": random.uniform(3, 10),
        "持续性": random.uniform(3, 10),
        "主动性": random.uniform(3, 10),
        "反思能力": random.uniform(3, 10)
    }
    
    # 学习效率评估
    dates = pd.date_range(end=datetime.now(), periods=10, freq='D')
    efficiency = []
    for date in dates:
        efficiency.append({
            "date": date.strftime("%m-%d"),
            "efficiency": random.uniform(0.4, 0.9)
        })
    
    # 学习风格识别
    learning_style = {
        "视觉型": random.uniform(10, 40),
        "听觉型": random.uniform(10, 30),
        "读写型": random.uniform(10, 30),
        "动觉型": random.uniform(10, 30)
    }
    
    # 学习障碍识别
    obstacles = {
        "注意力分散": "学习过程中容易被外界干扰，难以长时间保持专注。",
        "知识断层": "部分基础知识掌握不牢固，影响后续学习。",
        "学习动力不足": "缺乏明确的学习目标和内在动力。"
    }
    
    return {
        "knowledge_points": knowledge_points,
        "learning_habits": learning_habits,
        "efficiency": efficiency,
        "learning_style": learning_style,
        "obstacles": obstacles
    }

def generate_diagnosis_report(student_name, subject, diagnosis_data, diagnosis_options):
    """生成诊断报告文本"""
    report = f"学习诊断报告\n"
    report += f"学生: {student_name}\n"
    report += f"学科: {subject}\n"
    report += f"诊断日期: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    if "知识点掌握情况" in diagnosis_options:
        report += "知识点掌握情况:\n"
        for point in diagnosis_data["knowledge_points"]:
            mastery = point["mastery"] * 100
            level = "优秀" if mastery >= 80 else "良好" if mastery >= 60 else "需要提升"
            report += f"- {point['knowledge_point']}: {mastery:.1f}% ({level})\n"
        report += "\n"
    
    if "学习习惯分析" in diagnosis_options:
        report += "学习习惯分析:\n"
        for habit, score in diagnosis_data["learning_habits"].items():
            level = "优秀" if score >= 8 else "良好" if score >= 6 else "需要提升"
            report += f"- {habit}: {score:.1f}/10 ({level})\n"
        report += "\n"
    
    if "学习效率评估" in diagnosis_options:
        avg_efficiency = sum(item["efficiency"] for item in diagnosis_data["efficiency"]) / len(diagnosis_data["efficiency"])
        report += f"学习效率评估: {avg_efficiency*100:.1f}%\n\n"
    
    if "学习风格识别" in diagnosis_options:
        report += "学习风格识别:\n"
        for style, percentage in diagnosis_data["learning_style"].items():
            report += f"- {style}: {percentage:.1f}%\n"
        
        # 确定主要学习风格
        main_style = max(diagnosis_data["learning_style"].items(), key=lambda x: x[1])[0]
        report += f"\n主要学习风格: {main_style}\n\n"
    
    if "学习障碍识别" in diagnosis_options:
        report += "学习障碍识别:\n"
        for obstacle, description in diagnosis_data["obstacles"].items():
            report += f"- {obstacle}: {description}\n"
        report += "\n"
    
    # 添加改进建议
    report += "改进建议:\n"
    report += "1. 制定明确的学习计划，将大目标分解为小任务\n"
    report += "2. 采用适合自己学习风格的学习方法\n"
    report += "3. 定期复习，巩固知识点\n"
    report += "4. 寻求老师或同学的帮助，解决难点问题\n"
    report += "5. 保持良好的学习习惯，提高学习效率\n"
    
    return report

# 从环境变量或Streamlit Secrets中读取API密钥
def get_api_key(key_name):
    # 首先尝试从Streamlit Secrets中读取
    if key_name in st.secrets:
        return st.secrets[key_name]
    # 然后尝试从环境变量中读取
    elif os.getenv(key_name):
        return os.getenv(key_name)
    else:
        return None

# 初始化DeepSeek API
DEEPSEEK_API_KEY = get_api_key("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    st.warning("DeepSeek API密钥未配置，请在Streamlit Secrets或.env文件中设置DEEPSEEK_API_KEY")

if __name__ == "__main__":
    main() 