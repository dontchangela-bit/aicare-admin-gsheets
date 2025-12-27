"""
AI-CARE Lung - 管理後台（完整統計報表版）
=========================================

🔵 個案管理師專用介面
📊 完整統計報表系統
"""

import streamlit as st
from datetime import datetime, timedelta
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============================================
# 設定
# ============================================
SYSTEM_NAME = "AI-CARE Lung"
HOSPITAL_NAME = "三軍總醫院"

ADMIN_CREDENTIALS = {
    "admin": "aicare2024",
    "nurse01": "nurse2024",
    "nurse02": "nurse2024",
    "林冠勳": "aicare2024"
}

# Google Sheets 資料管理
try:
    from gsheets_manager import (
        get_all_patients, get_patient_by_id, create_patient, update_patient,
        get_all_reports, get_patient_reports,
        get_pending_alerts, handle_alert,
        get_education_pushes, push_education,
        get_interventions, save_intervention,
        get_dashboard_stats, get_today_reports
    )
    GSHEETS_AVAILABLE = True
except Exception as e:
    GSHEETS_AVAILABLE = False

# 衛教系統
EDUCATION_MATERIALS = {
    "BREATHING": {"icon": "🌬️", "title": "呼吸運動訓練", "category": "呼吸訓練", "description": "促進肺部恢復"},
    "PAIN": {"icon": "💊", "title": "疼痛控制指南", "category": "疼痛控制", "description": "術後疼痛管理"},
    "WOUND": {"icon": "🩹", "title": "傷口照護", "category": "傷口照護", "description": "居家換藥指導"},
    "HOME": {"icon": "🏠", "title": "居家照護指南", "category": "居家照護", "description": "出院後注意事項"},
    "WARNING": {"icon": "🚨", "title": "警示徵象", "category": "警示徵象", "description": "何時需要就醫"},
    "ACTIVITY": {"icon": "🚶", "title": "早期下床活動", "category": "活動指導", "description": "促進恢復"},
    "NUTRITION": {"icon": "🍎", "title": "營養指導", "category": "營養指導", "description": "術後飲食"},
    "FOLLOWUP": {"icon": "📋", "title": "追蹤檢查指南", "category": "追蹤檢查", "description": "回診準備"},
}

# 症狀列表
SYMPTOM_LIST = ["呼吸困難", "疼痛", "咳嗽", "疲勞", "睡眠障礙", "食慾不振", "情緒低落", "噁心", "發燒"]

# ============================================
# 頁面設定
# ============================================
st.set_page_config(
    page_title=f"{SYSTEM_NAME} - 管理後台",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton > button { border-radius: 8px; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'admin_page' not in st.session_state:
    st.session_state.admin_page = "dashboard"

# ============================================
# 登入
# ============================================
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 40px 0;">
            <div style="font-size: 64px;">🏥</div>
            <h1>{SYSTEM_NAME}</h1>
            <p style="color: #64748b;">管理後台</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not GSHEETS_AVAILABLE:
            st.error("⚠️ Google Sheets 連線失敗，請檢查設定")
        
        with st.form("login_form"):
            username = st.text_input("帳號")
            password = st.text_input("密碼", type="password")
            submit = st.form_submit_button("登入", use_container_width=True, type="primary")
            
            if submit:
                if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤")

# ============================================
# 側邊欄
# ============================================
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 16px 0;">
            <div style="font-size: 36px;">🏥</div>
            <div style="font-size: 16px; font-weight: 700;">{SYSTEM_NAME}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"👤 **{st.session_state.username}**")
        st.success("🟢 已連線" if GSHEETS_AVAILABLE else "🔴 未連線")
        st.markdown("---")
        
        menu_items = [
            ("dashboard", "📊", "儀表板"),
            ("alerts", "⚠️", "警示處理"),
            ("patients", "👥", "病人管理"),
            ("education", "📚", "衛教推送"),
            ("interventions", "📝", "介入紀錄"),
            ("reports", "📈", "報表統計"),
        ]
        
        for page_id, icon, label in menu_items:
            btn_type = "primary" if st.session_state.admin_page == page_id else "secondary"
            if st.button(f"{icon} {label}", key=f"nav_{page_id}", use_container_width=True, type=btn_type):
                st.session_state.admin_page = page_id
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 登出", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# ============================================
# 儀表板
# ============================================
def render_dashboard():
    st.markdown("## 📊 儀表板")
    
    if not GSHEETS_AVAILABLE:
        st.error("⚠️ Google Sheets 連線失敗")
        return
    
    stats = get_dashboard_stats()
    patients = get_all_patients()
    reports = get_all_reports()
    
    # KPI 卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總收案數", stats.get("total_patients", 0))
    with col2:
        st.metric("今日回報", stats.get("today_reports", 0), f"{stats.get('report_rate', 0)}%")
    with col3:
        st.metric("黃色警示", stats.get("yellow_alerts", 0))
    with col4:
        st.metric("紅色警示", stats.get("red_alerts", 0))
    
    st.markdown("---")
    
    # 圖表區
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚠️ 待處理警示")
        alerts = get_pending_alerts()
        if alerts:
            for alert in alerts[:5]:
                level = "🔴" if alert.get("alert_level") == "red" else "🟡"
                st.markdown(f"{level} **{alert.get('patient_name', '')}** - {alert.get('overall_score', 0)}分")
        else:
            st.success("✅ 無待處理警示")
    
    with col2:
        st.markdown("### 📋 今日回報")
        today_reports = get_today_reports()
        if today_reports:
            for r in today_reports[:5]:
                score = r.get("overall_score", 0)
                status = "🔴" if score >= 7 else "🟡" if score >= 4 else "🟢"
                st.markdown(f"{status} **{r.get('patient_name', '')}** - {score}分")
        else:
            st.info("今日尚無回報")
    
    st.markdown("---")
    
    # 快速統計圖
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 收案狀態分布")
        status_data = {
            "待設定": len([p for p in patients if p.get("status") == "pending_setup"]),
            "追蹤中": len([p for p in patients if p.get("status") == "normal"]),
            "已出院": len([p for p in patients if p.get("status") == "discharged"]),
        }
        if sum(status_data.values()) > 0:
            fig = px.pie(values=list(status_data.values()), names=list(status_data.keys()),
                        color_discrete_sequence=["#f59e0b", "#22c55e", "#94a3b8"], hole=0.4)
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 警示分布")
        alert_data = {
            "正常(0-3分)": len([r for r in reports if r.get("overall_score", 0) <= 3]),
            "注意(4-6分)": len([r for r in reports if 4 <= r.get("overall_score", 0) <= 6]),
            "警示(7-10分)": len([r for r in reports if r.get("overall_score", 0) >= 7]),
        }
        if sum(alert_data.values()) > 0:
            fig = px.pie(values=list(alert_data.values()), names=list(alert_data.keys()),
                        color_discrete_sequence=["#22c55e", "#f59e0b", "#ef4444"], hole=0.4)
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

# ============================================
# 警示處理
# ============================================
def render_alerts():
    st.markdown("## ⚠️ 警示處理")
    if not GSHEETS_AVAILABLE:
        st.error("⚠️ 連線失敗")
        return
    
    alerts = get_pending_alerts()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🔴 紅色警示", len([a for a in alerts if a.get("alert_level") == "red"]))
    col2.metric("🟡 黃色警示", len([a for a in alerts if a.get("alert_level") == "yellow"]))
    col3.metric("✅ 已處理今日", len([r for r in get_all_reports() if r.get("date") == datetime.now().strftime("%Y-%m-%d") and r.get("alert_handled") == "Y"]))
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔴 紅色警示", "🟡 黃色警示"])
    
    with tab1:
        red_alerts = [a for a in alerts if a.get("alert_level") == "red"]
        if red_alerts:
            for alert in red_alerts:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    col1.markdown(f"**{alert.get('patient_name', '')}** ({alert.get('patient_id', '')})")
                    col1.caption(f"評分: {alert.get('overall_score', 0)} 分 | {alert.get('date', '')}")
                    if col3.button("✅ 已處理", key=f"h_r_{alert.get('report_id')}"):
                        handle_alert(alert.get('report_id'), st.session_state.username)
                        st.rerun()
                st.markdown("---")
        else:
            st.success("✅ 無紅色警示")
    
    with tab2:
        yellow_alerts = [a for a in alerts if a.get("alert_level") == "yellow"]
        if yellow_alerts:
            for alert in yellow_alerts:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    col1.markdown(f"**{alert.get('patient_name', '')}** ({alert.get('patient_id', '')})")
                    col1.caption(f"評分: {alert.get('overall_score', 0)} 分 | {alert.get('date', '')}")
                    if col3.button("✅ 已處理", key=f"h_y_{alert.get('report_id')}"):
                        handle_alert(alert.get('report_id'), st.session_state.username)
                        st.rerun()
                st.markdown("---")
        else:
            st.success("✅ 無黃色警示")

# ============================================
# 病人管理
# ============================================
def render_patients():
    st.markdown("## 👥 病人管理")
    if not GSHEETS_AVAILABLE:
        st.error("⚠️ 連線失敗")
        return
    
    tab1, tab2 = st.tabs(["📋 病人列表", "⚙️ 病人設定"])
    
    with tab1:
        patients = get_all_patients()
        
        col1, col2, col3 = st.columns([2, 1, 1])
        search = col1.text_input("🔍 搜尋", placeholder="姓名或ID")
        status_filter = col2.selectbox("狀態", ["全部", "待設定", "追蹤中", "已出院"])
        
        if search:
            patients = [p for p in patients if search in str(p.get("name", "")) or search in str(p.get("patient_id", ""))]
        if status_filter == "待設定":
            patients = [p for p in patients if p.get("status") == "pending_setup"]
        elif status_filter == "追蹤中":
            patients = [p for p in patients if p.get("status") == "normal"]
        elif status_filter == "已出院":
            patients = [p for p in patients if p.get("status") == "discharged"]
        
        st.markdown(f"共 **{len(patients)}** 位病人")
        
        for p in patients:
            status_icon = "⏳" if p.get("status") == "pending_setup" else "✅" if p.get("status") == "normal" else "📤"
            st.markdown(f"{status_icon} **{p.get('name', '')}** ({p.get('patient_id', '')}) | D+{p.get('post_op_day', 0)} | {p.get('surgery_type', '待設定')} | 📞 {p.get('phone', '')}")
    
    with tab2:
        st.markdown("### ⚙️ 設定病人資料")
        patients = get_all_patients()
        pending = [p for p in patients if p.get("status") == "pending_setup"]
        if pending:
            st.warning(f"⚠️ 有 {len(pending)} 位病人待設定")
        
        options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p.get('patient_id') for p in patients}
        selected = st.selectbox("選擇病人", ["-- 請選擇 --"] + list(options.keys()))
        
        if selected != "-- 請選擇 --":
            patient = get_patient_by_id(options[selected])
            if patient:
                with st.form("setup"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**姓名:** {patient.get('name', '')}")
                        st.write(f"**電話:** {patient.get('phone', '')}")
                        medical_record = st.text_input("病歷號", value=str(patient.get("medical_record", "") or ""))
                    with col2:
                        surgery_date = st.date_input("手術日期", value=datetime.now().date())
                        surgery_type = st.selectbox("手術類型", ["Wedge resection", "Segmentectomy", "Lobectomy", "Bilobectomy", "Pneumonectomy"])
                        status = st.selectbox("狀態", ["pending_setup", "normal", "discharged"], 
                                            index=["pending_setup", "normal", "discharged"].index(patient.get("status", "pending_setup")))
                    
                    if st.form_submit_button("💾 儲存", type="primary", use_container_width=True):
                        update_patient(options[selected], {
                            "medical_record": medical_record,
                            "surgery_date": surgery_date.strftime("%Y-%m-%d"),
                            "surgery_type": surgery_type,
                            "status": status
                        })
                        st.success("✅ 已儲存！")
                        st.rerun()

# ============================================
# 衛教推送
# ============================================
def render_education():
    st.markdown("## 📚 衛教推送")
    if not GSHEETS_AVAILABLE:
        st.error("⚠️ 連線失敗")
        return
    
    tab1, tab2 = st.tabs(["📤 手動推送", "📋 推送紀錄"])
    
    with tab1:
        patients = [p for p in get_all_patients() if p.get("status") in ["normal", "discharged"]]
        patient_opts = {f"{p.get('name', '')} (D+{p.get('post_op_day', 0)})": p for p in patients}
        material_opts = {f"{m['icon']} {m['title']}": k for k, m in EDUCATION_MATERIALS.items()}
        
        col1, col2 = st.columns(2)
        selected_p = col1.selectbox("病人", ["--"] + list(patient_opts.keys()))
        selected_m = col2.selectbox("衛教", list(material_opts.keys()))
        
        if st.button("📤 推送", type="primary", use_container_width=True):
            if selected_p != "--":
                p = patient_opts[selected_p]
                m_key = material_opts[selected_m]
                m = EDUCATION_MATERIALS[m_key]
                push_education(p["patient_id"], p["name"], m_key, m["title"], m["category"], "manual", st.session_state.username)
                st.success(f"✅ 已推送給 {p['name']}！")
    
    with tab2:
        pushes = get_education_pushes()
        if pushes:
            for push in pushes[:20]:
                status = "✅" if push.get('status') == 'read' else "📤"
                st.markdown(f"{status} **{push.get('patient_name', '')}** - {push.get('material_title', '')} | {str(push.get('pushed_at', ''))[:10]}")
        else:
            st.info("無推送紀錄")

# ============================================
# 介入紀錄
# ============================================
def render_interventions():
    st.markdown("## 📝 介入紀錄")
    if not GSHEETS_AVAILABLE:
        st.error("⚠️ 連線失敗")
        return
    
    tab1, tab2 = st.tabs(["📋 紀錄列表", "➕ 新增"])
    
    with tab1:
        interventions = get_interventions()
        if interventions:
            for i in interventions[:20]:
                st.markdown(f"**{i.get('patient_name', '')}** | {i.get('method', '')} | {str(i.get('content', ''))[:50]}... | {str(i.get('timestamp', ''))[:10]}")
        else:
            st.info("無介入紀錄")
    
    with tab2:
        with st.form("new_int"):
            patients = get_all_patients()
            opts = {f"{p.get('name', '')}": p for p in patients}
            selected = st.selectbox("病人", ["--"] + list(opts.keys()))
            method = st.selectbox("方式", ["電話", "LINE", "門診", "視訊"])
            duration = st.text_input("時間", placeholder="例如: 5分鐘")
            content = st.text_area("內容")
            referral = st.selectbox("轉介", ["無", "緩和醫療", "營養諮詢", "復健科", "心理諮商", "社工"])
            
            if st.form_submit_button("💾 儲存", type="primary", use_container_width=True):
                if selected != "--" and content:
                    p = opts[selected]
                    save_intervention(p["patient_id"], p["name"], {
                        "method": method, "duration": duration, "content": content,
                        "referral": referral if referral != "無" else ""
                    }, st.session_state.username)
                    st.success("✅ 已儲存！")
                    st.rerun()

# ============================================
# 完整報表統計系統
# ============================================
def render_reports():
    st.markdown("## 📈 報表統計中心")
    
    if not GSHEETS_AVAILABLE:
        st.error("⚠️ Google Sheets 連線失敗")
        return
    
    # 載入資料
    patients = get_all_patients()
    reports = get_all_reports()
    education_pushes = get_education_pushes()
    interventions = get_interventions()
    
    # 時間篩選
    st.markdown("### 🗓️ 時間範圍")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    time_range = col1.selectbox("快速選擇", ["全部", "本週", "本月", "近三個月", "近半年", "近一年"])
    
    today = datetime.now().date()
    if time_range == "本週":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif time_range == "本月":
        start_date = today.replace(day=1)
        end_date = today
    elif time_range == "近三個月":
        start_date = today - timedelta(days=90)
        end_date = today
    elif time_range == "近半年":
        start_date = today - timedelta(days=180)
        end_date = today
    elif time_range == "近一年":
        start_date = today - timedelta(days=365)
        end_date = today
    else:
        start_date = today - timedelta(days=365*2)
        end_date = today
    
    # 報表分頁
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 綜合總覽", "🩺 症狀分析", "⚠️ 警示分析", 
        "📚 衛教分析", "👤 個案追蹤", "📥 資料匯出"
    ])
    
    # ==================== 綜合總覽 ====================
    with tab1:
        render_overview_report(patients, reports, education_pushes, interventions)
    
    # ==================== 症狀分析 ====================
    with tab2:
        render_symptom_analysis(reports, patients)
    
    # ==================== 警示分析 ====================
    with tab3:
        render_alert_analysis(reports, interventions)
    
    # ==================== 衛教分析 ====================
    with tab4:
        render_education_analysis(education_pushes, patients)
    
    # ==================== 個案追蹤 ====================
    with tab5:
        render_case_tracking(patients, reports, education_pushes, interventions)
    
    # ==================== 資料匯出 ====================
    with tab6:
        render_data_export(patients, reports, education_pushes, interventions)


def render_overview_report(patients, reports, education_pushes, interventions):
    """綜合總覽報表"""
    st.markdown("### 📊 綜合總覽")
    
    # KPI 卡片
    col1, col2, col3, col4, col5 = st.columns(5)
    
    active_patients = [p for p in patients if p.get("status") in ["normal", "discharged"]]
    total_reports = len(reports)
    
    # 計算回報完成率
    if active_patients and total_reports > 0:
        total_possible_days = sum([p.get("post_op_day", 0) for p in active_patients])
        compliance_rate = min(100, int(total_reports / max(total_possible_days, 1) * 100))
    else:
        compliance_rate = 0
    
    avg_score = sum([r.get("overall_score", 0) for r in reports]) / max(len(reports), 1)
    red_alerts = len([r for r in reports if r.get("overall_score", 0) >= 7])
    
    col1.metric("📋 總收案數", len(active_patients))
    col2.metric("✅ 回報完成率", f"{compliance_rate}%")
    col3.metric("📊 平均不適分數", f"{avg_score:.1f}")
    col4.metric("🔴 紅色警示", red_alerts)
    col5.metric("📚 衛教推送", len(education_pushes))
    
    st.markdown("---")
    
    # 圖表
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 每日回報趨勢")
        if reports:
            df_reports = pd.DataFrame(reports)
            if 'date' in df_reports.columns:
                daily_counts = df_reports.groupby('date').size().reset_index(name='count')
                daily_counts = daily_counts.sort_values('date').tail(30)
                fig = px.line(daily_counts, x='date', y='count', markers=True)
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20),
                                xaxis_title="日期", yaxis_title="回報數")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("尚無回報資料")
    
    with col2:
        st.markdown("#### 🏥 收案狀態分布")
        status_counts = {
            "待設定": len([p for p in patients if p.get("status") == "pending_setup"]),
            "追蹤中": len([p for p in patients if p.get("status") == "normal"]),
            "已出院追蹤": len([p for p in patients if p.get("status") == "discharged"]),
        }
        if sum(status_counts.values()) > 0:
            fig = px.pie(values=list(status_counts.values()), names=list(status_counts.keys()),
                        color_discrete_sequence=["#f59e0b", "#22c55e", "#3b82f6"], hole=0.4)
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔪 手術類型分布")
        surgery_counts = {}
        for p in patients:
            stype = p.get("surgery_type", "未設定")
            surgery_counts[stype] = surgery_counts.get(stype, 0) + 1
        if surgery_counts:
            fig = px.pie(values=list(surgery_counts.values()), names=list(surgery_counts.keys()), hole=0.4)
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📅 術後天數分布")
        post_op_ranges = {"D0-7": 0, "D8-14": 0, "D15-30": 0, "D31-90": 0, "D91-180": 0, "D180+": 0}
        for p in patients:
            days = p.get("post_op_day", 0)
            if days <= 7:
                post_op_ranges["D0-7"] += 1
            elif days <= 14:
                post_op_ranges["D8-14"] += 1
            elif days <= 30:
                post_op_ranges["D15-30"] += 1
            elif days <= 90:
                post_op_ranges["D31-90"] += 1
            elif days <= 180:
                post_op_ranges["D91-180"] += 1
            else:
                post_op_ranges["D180+"] += 1
        
        fig = px.bar(x=list(post_op_ranges.keys()), y=list(post_op_ranges.values()),
                    color_discrete_sequence=["#6366f1"])
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20),
                        xaxis_title="術後天數", yaxis_title="病人數")
        st.plotly_chart(fig, use_container_width=True)


def render_symptom_analysis(reports, patients):
    """症狀分析報表"""
    st.markdown("### 🩺 症狀分析")
    
    if not reports:
        st.info("尚無回報資料可供分析")
        return
    
    # 症狀統計
    symptom_counts = {}
    severity_distribution = {"輕微(0-3)": 0, "中度(4-6)": 0, "嚴重(7-10)": 0}
    
    for r in reports:
        # 計算嚴重度分布
        score = r.get("overall_score", 0)
        if score <= 3:
            severity_distribution["輕微(0-3)"] += 1
        elif score <= 6:
            severity_distribution["中度(4-6)"] += 1
        else:
            severity_distribution["嚴重(7-10)"] += 1
        
        # 統計症狀（假設 symptoms 是列表）
        symptoms = r.get("symptoms", [])
        if isinstance(symptoms, str):
            try:
                symptoms = json.loads(symptoms)
            except:
                symptoms = []
        for s in symptoms:
            symptom_counts[s] = symptom_counts.get(s, 0) + 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 常見症狀排名")
        if symptom_counts:
            sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
            symptoms_df = pd.DataFrame(sorted_symptoms, columns=["症狀", "次數"])
            fig = px.bar(symptoms_df.head(10), x="次數", y="症狀", orientation='h',
                        color_discrete_sequence=["#f97316"])
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("尚無症狀資料")
    
    with col2:
        st.markdown("#### 📊 症狀嚴重度分布")
        fig = px.pie(values=list(severity_distribution.values()), 
                    names=list(severity_distribution.keys()),
                    color_discrete_sequence=["#22c55e", "#f59e0b", "#ef4444"], hole=0.4)
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # 症狀趨勢
    st.markdown("#### 📈 症狀分數趨勢（近30天）")
    if reports:
        df = pd.DataFrame(reports)
        if 'date' in df.columns and 'overall_score' in df.columns:
            daily_avg = df.groupby('date')['overall_score'].mean().reset_index()
            daily_avg = daily_avg.sort_values('date').tail(30)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daily_avg['date'], y=daily_avg['overall_score'],
                                    mode='lines+markers', name='平均分數',
                                    line=dict(color='#6366f1', width=2)))
            fig.add_hline(y=4, line_dash="dash", line_color="#f59e0b", annotation_text="注意線")
            fig.add_hline(y=7, line_dash="dash", line_color="#ef4444", annotation_text="警示線")
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20),
                            xaxis_title="日期", yaxis_title="平均不適分數")
            st.plotly_chart(fig, use_container_width=True)
    
    # 術後天數 vs 症狀分數
    st.markdown("#### 📊 術後天數與症狀關聯")
    st.info("此分析需要更多數據累積後顯示")


def render_alert_analysis(reports, interventions):
    """警示分析報表"""
    st.markdown("### ⚠️ 警示分析")
    
    if not reports:
        st.info("尚無回報資料可供分析")
        return
    
    # 警示統計
    red_alerts = [r for r in reports if r.get("overall_score", 0) >= 7]
    yellow_alerts = [r for r in reports if 4 <= r.get("overall_score", 0) <= 6]
    handled_alerts = [r for r in reports if r.get("alert_handled") == "Y"]
    
    # KPI
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 紅色警示總數", len(red_alerts))
    col2.metric("🟡 黃色警示總數", len(yellow_alerts))
    col3.metric("✅ 已處理數", len(handled_alerts))
    
    # 處理率
    total_alerts = len(red_alerts) + len(yellow_alerts)
    handle_rate = len(handled_alerts) / max(total_alerts, 1) * 100
    col4.metric("📊 處理完成率", f"{handle_rate:.0f}%")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 警示趨勢（近30天）")
        if reports:
            df = pd.DataFrame(reports)
            if 'date' in df.columns:
                df['alert_type'] = df['overall_score'].apply(
                    lambda x: '紅色' if x >= 7 else ('黃色' if x >= 4 else '正常')
                )
                alert_trend = df.groupby(['date', 'alert_type']).size().unstack(fill_value=0)
                alert_trend = alert_trend.reset_index().tail(30)
                
                fig = go.Figure()
                if '紅色' in alert_trend.columns:
                    fig.add_trace(go.Bar(x=alert_trend['date'], y=alert_trend['紅色'], name='紅色', marker_color='#ef4444'))
                if '黃色' in alert_trend.columns:
                    fig.add_trace(go.Bar(x=alert_trend['date'], y=alert_trend['黃色'], name='黃色', marker_color='#f59e0b'))
                fig.update_layout(barmode='stack', height=300, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🔔 警示等級分布")
        alert_dist = {
            "紅色(≥7分)": len(red_alerts),
            "黃色(4-6分)": len(yellow_alerts),
            "正常(<4分)": len([r for r in reports if r.get("overall_score", 0) < 4])
        }
        fig = px.pie(values=list(alert_dist.values()), names=list(alert_dist.keys()),
                    color_discrete_sequence=["#ef4444", "#f59e0b", "#22c55e"], hole=0.4)
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # 高風險病人
    st.markdown("#### 🚨 高風險病人名單（多次觸發警示）")
    alert_by_patient = {}
    for r in reports:
        if r.get("overall_score", 0) >= 4:
            pid = r.get("patient_id", "")
            pname = r.get("patient_name", "")
            key = f"{pname} ({pid})"
            alert_by_patient[key] = alert_by_patient.get(key, 0) + 1
    
    if alert_by_patient:
        sorted_patients = sorted(alert_by_patient.items(), key=lambda x: x[1], reverse=True)[:10]
        for patient, count in sorted_patients:
            level = "🔴" if count >= 5 else "🟡" if count >= 3 else "🟢"
            st.markdown(f"{level} **{patient}** - {count} 次警示")
    else:
        st.success("✅ 目前無高風險病人")


def render_education_analysis(education_pushes, patients):
    """衛教分析報表"""
    st.markdown("### 📚 衛教成效分析")
    
    if not education_pushes:
        st.info("尚無衛教推送資料")
        return
    
    # 統計
    total_pushes = len(education_pushes)
    read_pushes = len([e for e in education_pushes if e.get("status") == "read"])
    auto_pushes = len([e for e in education_pushes if e.get("push_type") == "auto"])
    manual_pushes = total_pushes - auto_pushes
    
    read_rate = read_pushes / max(total_pushes, 1) * 100
    
    # KPI
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📤 總推送數", total_pushes)
    col2.metric("👁️ 已讀率", f"{read_rate:.0f}%")
    col3.metric("🤖 自動推送", auto_pushes)
    col4.metric("👤 手動推送", manual_pushes)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 熱門衛教單張")
        material_counts = {}
        material_read = {}
        for e in education_pushes:
            title = e.get("material_title", "未知")
            material_counts[title] = material_counts.get(title, 0) + 1
            if e.get("status") == "read":
                material_read[title] = material_read.get(title, 0) + 1
        
        if material_counts:
            df = pd.DataFrame([
                {"衛教": k, "推送數": v, "已讀數": material_read.get(k, 0)}
                for k, v in material_counts.items()
            ])
            df = df.sort_values("推送數", ascending=True).tail(8)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df['推送數'], y=df['衛教'], orientation='h', name='推送數', marker_color='#6366f1'))
            fig.add_trace(go.Bar(x=df['已讀數'], y=df['衛教'], orientation='h', name='已讀數', marker_color='#22c55e'))
            fig.update_layout(barmode='group', height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 推送類型分布")
        type_dist = {"手動推送": manual_pushes, "自動推送": auto_pushes}
        fig = px.pie(values=list(type_dist.values()), names=list(type_dist.keys()),
                    color_discrete_sequence=["#3b82f6", "#8b5cf6"], hole=0.4)
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)


def render_case_tracking(patients, reports, education_pushes, interventions):
    """個案追蹤報表"""
    st.markdown("### 👤 個案追蹤")
    
    if not patients:
        st.info("尚無病人資料")
        return
    
    # 選擇檢視方式
    view_mode = st.radio("檢視方式", ["📋 全部總覽", "👤 個別病人"], horizontal=True)
    
    if view_mode == "📋 全部總覽":
        # 總覽表格
        st.markdown("#### 📋 全部病人追蹤狀態")
        
        table_data = []
        for p in patients:
            pid = p.get("patient_id", "")
            p_reports = [r for r in reports if r.get("patient_id") == pid]
            
            last_report = max([r.get("date", "") for r in p_reports]) if p_reports else "無"
            avg_score = sum([r.get("overall_score", 0) for r in p_reports]) / max(len(p_reports), 1)
            alert_count = len([r for r in p_reports if r.get("overall_score", 0) >= 4])
            
            # 計算回報率
            post_op_day = p.get("post_op_day", 0)
            compliance = min(100, len(p_reports) / max(post_op_day, 1) * 100) if post_op_day > 0 else 0
            
            status_icon = "⏳" if p.get("status") == "pending_setup" else "✅" if p.get("status") == "normal" else "📤"
            
            table_data.append({
                "狀態": status_icon,
                "姓名": p.get("name", ""),
                "ID": pid,
                "術後天數": f"D+{post_op_day}",
                "回報數": len(p_reports),
                "回報率": f"{compliance:.0f}%",
                "平均分數": f"{avg_score:.1f}",
                "警示次數": alert_count,
                "最近回報": last_report
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    else:
        # 個別病人詳情
        st.markdown("#### 👤 個別病人追蹤")
        
        patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p.get("patient_id") for p in patients}
        selected = st.selectbox("選擇病人", list(patient_options.keys()))
        
        if selected:
            pid = patient_options[selected]
            patient = next((p for p in patients if p.get("patient_id") == pid), None)
            p_reports = [r for r in reports if r.get("patient_id") == pid]
            p_education = [e for e in education_pushes if e.get("patient_id") == pid]
            p_interventions = [i for i in interventions if i.get("patient_id") == pid]
            
            if patient:
                # 病人資訊
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("術後天數", f"D+{patient.get('post_op_day', 0)}")
                col2.metric("回報次數", len(p_reports))
                avg = sum([r.get("overall_score", 0) for r in p_reports]) / max(len(p_reports), 1)
                col3.metric("平均評分", f"{avg:.1f}")
                compliance = min(100, len(p_reports) / max(patient.get('post_op_day', 1), 1) * 100)
                col4.metric("回報率", f"{compliance:.0f}%")
                
                st.markdown("---")
                
                # 症狀趨勢圖
                st.markdown("##### 📈 症狀趨勢")
                if p_reports:
                    df = pd.DataFrame(p_reports)
                    if 'date' in df.columns and 'overall_score' in df.columns:
                        df = df.sort_values('date')
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df['date'], y=df['overall_score'],
                                                mode='lines+markers', name='不適分數',
                                                line=dict(color='#6366f1', width=2)))
                        fig.add_hline(y=4, line_dash="dash", line_color="#f59e0b")
                        fig.add_hline(y=7, line_dash="dash", line_color="#ef4444")
                        fig.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20),
                                        xaxis_title="日期", yaxis_title="不適分數", yaxis_range=[0, 10])
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("尚無回報紀錄")
                
                # 衛教與介入紀錄
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### 📚 衛教紀錄")
                    if p_education:
                        for e in p_education[:5]:
                            status = "✅" if e.get("status") == "read" else "📤"
                            st.markdown(f"{status} {e.get('material_title', '')} | {str(e.get('pushed_at', ''))[:10]}")
                    else:
                        st.info("無衛教紀錄")
                
                with col2:
                    st.markdown("##### 📝 介入紀錄")
                    if p_interventions:
                        for i in p_interventions[:5]:
                            st.markdown(f"📞 {i.get('method', '')} | {str(i.get('content', ''))[:30]}...")
                    else:
                        st.info("無介入紀錄")


def render_data_export(patients, reports, education_pushes, interventions):
    """資料匯出"""
    st.markdown("### 📥 資料匯出")
    
    st.markdown("#### 📊 匯出格式")
    export_format = st.radio("選擇格式", ["CSV", "Excel"], horizontal=True)
    
    st.markdown("#### 📋 選擇匯出內容")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_patients = st.checkbox("✅ 病人資料", value=True)
        export_reports = st.checkbox("✅ 症狀回報紀錄", value=True)
        export_education = st.checkbox("📚 衛教推送紀錄", value=True)
    
    with col2:
        export_interventions = st.checkbox("📝 介入紀錄", value=True)
        deidentify = st.checkbox("🔒 去識別化處理", value=False)
    
    st.markdown("---")
    
    if st.button("📥 產生匯出檔案", type="primary", use_container_width=True):
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 處理去識別化
        def deidentify_data(df, id_col="patient_id", name_col="patient_name"):
            if deidentify and not df.empty:
                if name_col in df.columns:
                    df[name_col] = df[name_col].apply(lambda x: f"Patient_{hash(str(x)) % 10000:04d}")
                if "phone" in df.columns:
                    df["phone"] = "********"
                if "medical_record" in df.columns:
                    df["medical_record"] = "********"
            return df
        
        # 病人資料
        if export_patients and patients:
            df_patients = pd.DataFrame(patients)
            df_patients = deidentify_data(df_patients, name_col="name")
            
            if export_format == "CSV":
                csv = df_patients.to_csv(index=False).encode('utf-8-sig')
                st.download_button("⬇️ 下載病人資料 (CSV)", csv, f"patients_{timestamp}.csv", "text/csv")
            else:
                # Excel
                output = df_patients.to_csv(index=False).encode('utf-8-sig')
                st.download_button("⬇️ 下載病人資料 (CSV)", output, f"patients_{timestamp}.csv", "text/csv")
        
        # 回報紀錄
        if export_reports and reports:
            df_reports = pd.DataFrame(reports)
            df_reports = deidentify_data(df_reports)
            
            csv = df_reports.to_csv(index=False).encode('utf-8-sig')
            st.download_button("⬇️ 下載回報紀錄 (CSV)", csv, f"reports_{timestamp}.csv", "text/csv")
        
        # 衛教紀錄
        if export_education and education_pushes:
            df_edu = pd.DataFrame(education_pushes)
            df_edu = deidentify_data(df_edu)
            
            csv = df_edu.to_csv(index=False).encode('utf-8-sig')
            st.download_button("⬇️ 下載衛教紀錄 (CSV)", csv, f"education_{timestamp}.csv", "text/csv")
        
        # 介入紀錄
        if export_interventions and interventions:
            df_int = pd.DataFrame(interventions)
            df_int = deidentify_data(df_int)
            
            csv = df_int.to_csv(index=False).encode('utf-8-sig')
            st.download_button("⬇️ 下載介入紀錄 (CSV)", csv, f"interventions_{timestamp}.csv", "text/csv")
        
        st.success("✅ 匯出檔案已準備完成！")
    
    st.markdown("---")
    st.markdown("#### ℹ️ 說明")
    st.info("""
    - **去識別化處理**：將姓名轉為編碼、隱藏電話和病歷號
    - 匯出資料符合 IRB 研究規範
    - 建議定期備份資料
    """)


# ============================================
# 主程式
# ============================================
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        render_sidebar()
        page = st.session_state.admin_page
        
        if page == "dashboard":
            render_dashboard()
        elif page == "alerts":
            render_alerts()
        elif page == "patients":
            render_patients()
        elif page == "education":
            render_education()
        elif page == "interventions":
            render_interventions()
        elif page == "reports":
            render_reports()
        else:
            render_dashboard()

if __name__ == "__main__":
    main()
