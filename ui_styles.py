"""
AI-CARE Lung - UI 美化模組
==========================

包含：
1. 自訂 CSS 樣式
2. 品牌色彩系統
3. 卡片元件
4. 圖示與插圖
5. 動畫效果
6. Logo 整合
"""

import streamlit as st
import base64
from pathlib import Path

# 嘗試載入 Logo 模組
try:
    from logos import (
        render_tsgh_logo, render_dmc_logo, render_aicare_logo,
        render_sidebar_logo, render_combined_header, render_login_header,
        render_footer, SIDEBAR_LOGO_SVG
    )
    LOGOS_AVAILABLE = True
except:
    LOGOS_AVAILABLE = False
    SIDEBAR_LOGO_SVG = ""

# ============================================
# 品牌色彩系統
# ============================================

COLORS = {
    # 主色
    "primary": "#1E88E5",      # 藍色 - 專業、信任
    "secondary": "#26A69A",    # 青綠色 - 醫療、健康
    "accent": "#7C4DFF",       # 紫色 - 創新、AI
    
    # 警示色
    "danger": "#EF5350",       # 紅色
    "warning": "#FFA726",      # 橘色
    "success": "#66BB6A",      # 綠色
    "info": "#29B6F6",         # 淺藍
    
    # 中性色
    "dark": "#37474F",
    "gray": "#78909C",
    "light": "#ECEFF1",
    "white": "#FFFFFF",
    
    # 背景漸層
    "gradient_primary": "linear-gradient(135deg, #1E88E5 0%, #1565C0 100%)",
    "gradient_success": "linear-gradient(135deg, #66BB6A 0%, #43A047 100%)",
    "gradient_danger": "linear-gradient(135deg, #EF5350 0%, #E53935 100%)",
    "gradient_card": "linear-gradient(145deg, #ffffff 0%, #f5f7fa 100%)"
}

# ============================================
# 主要 CSS 樣式
# ============================================

def get_custom_css():
    """取得自訂 CSS"""
    return f"""
    <style>
    /* ===== 全局樣式 ===== */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
    
    .stApp {{
        font-family: 'Noto Sans TC', sans-serif;
    }}
    
    /* ===== 側邊欄美化 ===== */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #1E3A5F 0%, #0D253F 100%);
    }}
    
    [data-testid="stSidebar"] .stButton > button {{
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        color: white;
        border-radius: 10px;
        transition: all 0.3s ease;
    }}
    
    [data-testid="stSidebar"] .stButton > button:hover {{
        background: rgba(255,255,255,0.2);
        transform: translateX(5px);
    }}
    
    /* ===== 標題樣式 ===== */
    h1 {{
        color: {COLORS['primary']};
        font-weight: 700;
        padding-bottom: 10px;
        border-bottom: 3px solid {COLORS['primary']};
        margin-bottom: 20px;
    }}
    
    h2, h3 {{
        color: {COLORS['dark']};
        font-weight: 600;
    }}
    
    /* ===== 指標卡片 ===== */
    [data-testid="stMetric"] {{
        background: {COLORS['gradient_card']};
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }}
    
    [data-testid="stMetric"]:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }}
    
    [data-testid="stMetricLabel"] {{
        font-size: 14px;
        color: {COLORS['gray']};
        font-weight: 500;
    }}
    
    [data-testid="stMetricValue"] {{
        font-size: 32px;
        font-weight: 700;
        color: {COLORS['dark']};
    }}
    
    /* ===== 按鈕樣式 ===== */
    .stButton > button {{
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: none;
    }}
    
    .stButton > button[kind="primary"] {{
        background: {COLORS['gradient_primary']};
        color: white;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(30,136,229,0.4);
    }}
    
    /* ===== 表單樣式 ===== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {{
        border-radius: 10px;
        border: 2px solid {COLORS['light']};
        transition: border-color 0.3s ease;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {COLORS['primary']};
        box-shadow: 0 0 0 3px rgba(30,136,229,0.1);
    }}
    
    /* ===== 警示框樣式 ===== */
    .stAlert {{
        border-radius: 10px;
        border: none;
    }}
    
    /* ===== 展開器樣式 ===== */
    .streamlit-expanderHeader {{
        background: {COLORS['light']};
        border-radius: 10px;
        font-weight: 500;
    }}
    
    /* ===== 資料框樣式 ===== */
    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }}
    
    /* ===== 標籤頁樣式 ===== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        font-weight: 500;
    }}
    
    /* ===== 分隔線 ===== */
    hr {{
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, {COLORS['light']}, transparent);
        margin: 20px 0;
    }}
    
    /* ===== 動畫 ===== */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .animate-fade-in {{
        animation: fadeIn 0.5s ease-out;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
    }}
    
    .animate-pulse {{
        animation: pulse 2s infinite;
    }}
    
    /* ===== 自訂卡片類別 ===== */
    .custom-card {{
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }}
    
    .custom-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }}
    
    .card-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid {COLORS['light']};
    }}
    
    .card-icon {{
        font-size: 24px;
    }}
    
    .card-title {{
        font-size: 18px;
        font-weight: 600;
        color: {COLORS['dark']};
    }}
    
    /* ===== 警示卡片 ===== */
    .alert-card-red {{
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border-left: 5px solid {COLORS['danger']};
    }}
    
    .alert-card-yellow {{
        background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%);
        border-left: 5px solid {COLORS['warning']};
    }}
    
    .alert-card-green {{
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-left: 5px solid {COLORS['success']};
    }}
    
    /* ===== 狀態標籤 ===== */
    .status-badge {{
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }}
    
    .status-active {{ background: #E3F2FD; color: #1565C0; }}
    .status-completed {{ background: #E8F5E9; color: #2E7D32; }}
    .status-pending {{ background: #FFF3E0; color: #EF6C00; }}
    .status-critical {{ background: #FFEBEE; color: #C62828; }}
    
    /* ===== 進度條美化 ===== */
    .stProgress > div > div > div {{
        background: {COLORS['gradient_primary']};
        border-radius: 10px;
    }}
    
    /* ===== 圖表容器 ===== */
    .chart-container {{
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }}
    
    </style>
    """


# ============================================
# 卡片元件
# ============================================

def render_info_card(title, value, icon="📊", subtitle="", color="primary"):
    """渲染資訊卡片"""
    gradient = COLORS.get(f"gradient_{color}", COLORS["gradient_primary"])
    
    st.markdown(f"""
    <div class="custom-card" style="text-align: center;">
        <div style="font-size: 40px; margin-bottom: 10px;">{icon}</div>
        <div style="font-size: 32px; font-weight: 700; color: {COLORS['dark']};">{value}</div>
        <div style="font-size: 14px; color: {COLORS['gray']}; margin-top: 5px;">{title}</div>
        {f'<div style="font-size: 12px; color: {COLORS["success"]}; margin-top: 5px;">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def render_alert_card(patient_name, score, alert_level, wait_time, post_op_day, symptoms=""):
    """渲染警示卡片"""
    card_class = f"alert-card-{alert_level}"
    icon = "🔴" if alert_level == "red" else "🟡" if alert_level == "yellow" else "🟢"
    
    st.markdown(f"""
    <div class="custom-card {card_class}">
        <div class="card-header">
            <span class="card-icon">{icon}</span>
            <span class="card-title">{patient_name}</span>
            <span class="status-badge status-{'critical' if alert_level == 'red' else 'pending'}">{wait_time}</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
            <div>
                <div style="color: {COLORS['gray']}; font-size: 12px;">術後天數</div>
                <div style="font-weight: 600;">D+{post_op_day}</div>
            </div>
            <div>
                <div style="color: {COLORS['gray']}; font-size: 12px;">整體評分</div>
                <div style="font-weight: 600; color: {COLORS['danger'] if score >= 7 else COLORS['warning'] if score >= 4 else COLORS['success']};">{score}/10</div>
            </div>
            <div>
                <div style="color: {COLORS['gray']}; font-size: 12px;">主要症狀</div>
                <div style="font-weight: 600;">{symptoms or '-'}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_stat_card(title, value, change="", trend="up", icon="📈"):
    """渲染統計卡片"""
    trend_color = COLORS["success"] if trend == "up" else COLORS["danger"]
    trend_icon = "↑" if trend == "up" else "↓"
    
    st.markdown(f"""
    <div class="custom-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 14px; color: {COLORS['gray']};">{title}</div>
                <div style="font-size: 28px; font-weight: 700; color: {COLORS['dark']};">{value}</div>
                {f'<div style="font-size: 12px; color: {trend_color};">{trend_icon} {change}</div>' if change else ''}
            </div>
            <div style="font-size: 40px; opacity: 0.8;">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# 頁首與 Logo
# ============================================

def render_header(title="AI-CARE Lung", subtitle="智慧肺癌術後照護系統"):
    """渲染頁首"""
    if LOGOS_AVAILABLE:
        render_combined_header()
    else:
        st.markdown(f"""
        <div style="
            background: {COLORS['gradient_primary']};
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            color: white;
            text-align: center;
        ">
            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">🏥 三軍總醫院 胸腔外科</div>
            <div style="font-size: 32px; font-weight: 700;">{title}</div>
            <div style="font-size: 16px; opacity: 0.9; margin-top: 5px;">{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)


def render_logo_sidebar():
    """渲染側邊欄 Logo"""
    if LOGOS_AVAILABLE:
        render_sidebar_logo()
    else:
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 20px;
            margin-bottom: 20px;
        ">
            <div style="
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #4FC3F7 0%, #1E88E5 100%);
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 15px;
                font-size: 40px;
            ">🫁</div>
            <div style="color: white; font-size: 18px; font-weight: 700;">AI-CARE</div>
            <div style="color: rgba(255,255,255,0.7); font-size: 12px;">Lung</div>
        </div>
        """, unsafe_allow_html=True)


# ============================================
# SVG 插圖
# ============================================

def get_illustration(name):
    """取得 SVG 插圖"""
    illustrations = {
        "empty_state": """
        <svg width="200" height="150" viewBox="0 0 200 150" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="40" y="30" width="120" height="80" rx="10" fill="#E3F2FD"/>
            <rect x="55" y="45" width="90" height="8" rx="4" fill="#90CAF9"/>
            <rect x="55" y="60" width="70" height="8" rx="4" fill="#90CAF9"/>
            <rect x="55" y="75" width="80" height="8" rx="4" fill="#90CAF9"/>
            <circle cx="100" cy="130" r="15" fill="#1E88E5"/>
            <path d="M95 130L99 134L105 126" stroke="white" stroke-width="2" stroke-linecap="round"/>
        </svg>
        """,
        
        "success": """
        <svg width="100" height="100" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="45" fill="#E8F5E9"/>
            <circle cx="50" cy="50" r="35" fill="#66BB6A"/>
            <path d="M35 50L45 60L65 40" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """,
        
        "warning": """
        <svg width="100" height="100" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="45" fill="#FFF3E0"/>
            <circle cx="50" cy="50" r="35" fill="#FFA726"/>
            <rect x="47" y="30" width="6" height="25" rx="3" fill="white"/>
            <circle cx="50" cy="65" r="4" fill="white"/>
        </svg>
        """,
        
        "doctor": """
        <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="45" r="25" fill="#FFCCBC"/>
            <ellipse cx="60" cy="100" rx="35" ry="20" fill="#1E88E5"/>
            <circle cx="52" cy="42" r="3" fill="#37474F"/>
            <circle cx="68" cy="42" r="3" fill="#37474F"/>
            <path d="M55 52C55 52 60 57 65 52" stroke="#37474F" stroke-width="2" stroke-linecap="round"/>
            <rect x="50" y="80" width="20" height="5" rx="2.5" fill="white"/>
        </svg>
        """,
        
        "patient": """
        <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="45" r="25" fill="#FFCCBC"/>
            <ellipse cx="60" cy="100" rx="35" ry="20" fill="#78909C"/>
            <circle cx="52" cy="42" r="3" fill="#37474F"/>
            <circle cx="68" cy="42" r="3" fill="#37474F"/>
            <path d="M55 52C55 52 60 57 65 52" stroke="#37474F" stroke-width="2" stroke-linecap="round"/>
        </svg>
        """
    }
    
    return illustrations.get(name, "")


def render_illustration(name, width=200):
    """渲染 SVG 插圖"""
    svg = get_illustration(name)
    if svg:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            {svg}
        </div>
        """, unsafe_allow_html=True)


def render_empty_state(message="目前沒有資料", icon="📋"):
    """渲染空狀態"""
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 40px;
        background: {COLORS['light']};
        border-radius: 15px;
        margin: 20px 0;
    ">
        <div style="font-size: 60px; margin-bottom: 15px;">{icon}</div>
        <div style="font-size: 18px; color: {COLORS['gray']};">{message}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# 進度指示器
# ============================================

def render_progress_steps(steps, current_step):
    """渲染進度步驟"""
    html = '<div style="display: flex; justify-content: space-between; margin: 20px 0;">'
    
    for i, step in enumerate(steps):
        is_completed = i < current_step
        is_current = i == current_step
        
        color = COLORS['success'] if is_completed else COLORS['primary'] if is_current else COLORS['light']
        text_color = 'white' if (is_completed or is_current) else COLORS['gray']
        
        html += f"""
        <div style="flex: 1; text-align: center;">
            <div style="
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: {color};
                color: {text_color};
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 10px;
                font-weight: 600;
            ">{'✓' if is_completed else i + 1}</div>
            <div style="font-size: 12px; color: {COLORS['dark'] if is_current else COLORS['gray']};">{step}</div>
        </div>
        """
        
        if i < len(steps) - 1:
            line_color = COLORS['success'] if is_completed else COLORS['light']
            html += f'<div style="flex: 0.5; height: 2px; background: {line_color}; margin-top: 20px;"></div>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ============================================
# 初始化函數
# ============================================

def init_page_style():
    """初始化頁面樣式"""
    st.markdown(get_custom_css(), unsafe_allow_html=True)


def apply_theme():
    """套用主題（在 app.py 最開始呼叫）"""
    init_page_style()
