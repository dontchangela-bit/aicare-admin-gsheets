"""
AI-CARE Lung - 管理後台（Google Sheets 整合版）
=============================================

🔵 個案管理師專用介面
📊 使用 Google Sheets 作為共享資料庫
"""

import streamlit as st
from datetime import datetime, timedelta
import json
import plotly.express as px
import plotly.graph_objects as go

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
        
        for page_id, icon, label in [
            ("dashboard", "📊", "儀表板"),
            ("alerts", "⚠️", "警示處理"),
            ("patients", "👥", "病人管理"),
            ("education", "📚", "衛教推送"),
            ("interventions", "📝", "介入紀錄"),
            ("reports", "📈", "報表統計"),
        ]:
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
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總收案數", stats.get("total_patients", 0))
    col2.metric("今日回報", stats.get("today_reports", 0), f"{stats.get('report_rate', 0)}%")
    col3.metric("黃色警示", stats.get("yellow_alerts", 0))
    col4.metric("紅色警示", stats.get("red_alerts", 0))
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚠️ 待處理警示")
        alerts = get_pending_alerts()
        if alerts:
            for alert in alerts[:5]:
                level = "🔴" if alert.get("alert_level") == "red" else "🟡"
                st.markdown(f"{level} **{alert.get('patient_name', '')}** - {alert.get('overall_score', 0)}分 ({alert.get('date', '')})")
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

# ============================================
# 警示處理
# ============================================
def render_alerts():
    st.markdown("## ⚠️ 警示處理")
    if not GSHEETS_AVAILABLE:
        st.error("⚠️ 連線失敗")
        return
    
    alerts = get_pending_alerts()
    
    for level_name, level_key, color in [("🔴 紅色警示", "red", "#ef4444"), ("🟡 黃色警示", "yellow", "#f59e0b")]:
        st.markdown(f"### {level_name}")
        level_alerts = [a for a in alerts if a.get("alert_level") == level_key]
        
        if level_alerts:
            for alert in level_alerts:
                col1, col2 = st.columns([4, 1])
                col1.markdown(f"**{alert.get('patient_name', '')}** - {alert.get('overall_score', 0)}分 | {alert.get('date', '')}")
                if col2.button("✅ 處理", key=f"h_{alert.get('report_id')}"):
                    handle_alert(alert.get('report_id'), st.session_state.username)
                    st.rerun()
        else:
            st.success(f"✅ 無{level_name[2:]}")
        st.markdown("---")

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
        search = st.text_input("🔍 搜尋", placeholder="姓名或ID")
        if search:
            patients = [p for p in patients if search in p.get("name", "") or search in p.get("patient_id", "")]
        
        st.markdown(f"共 **{len(patients)}** 位病人")
        for p in patients:
            status = "⏳" if p.get("status") == "pending_setup" else "✅" if p.get("status") == "normal" else "📤"
            st.markdown(f"{status} **{p.get('name', '')}** ({p.get('patient_id', '')}) - D+{p.get('post_op_day', 0)} | {p.get('surgery_type', '待設定')}")
    
    with tab2:
        st.markdown("### ⚙️ 設定病人資料")
        patients = get_all_patients()
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
                        medical_record = st.text_input("病歷號", value=patient.get("medical_record", "") or "")
                    with col2:
                        surgery_date = st.date_input("手術日期")
                        surgery_type = st.selectbox("手術類型", ["Wedge resection", "Segmentectomy", "Lobectomy", "Bilobectomy", "Pneumonectomy"])
                        status = st.selectbox("狀態", ["pending_setup", "normal", "discharged"])
                    
                    if st.form_submit_button("💾 儲存", type="primary"):
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
        patients = [p for p in get_all_patients() if p.get("status") == "normal"]
        patient_opts = {f"{p.get('name', '')}": p for p in patients}
        material_opts = {f"{m['icon']} {m['title']}": k for k, m in EDUCATION_MATERIALS.items()}
        
        col1, col2 = st.columns(2)
        selected_p = col1.selectbox("病人", ["--"] + list(patient_opts.keys()))
        selected_m = col2.selectbox("衛教", list(material_opts.keys()))
        
        if st.button("📤 推送", type="primary"):
            if selected_p != "--":
                p = patient_opts[selected_p]
                m_key = material_opts[selected_m]
                m = EDUCATION_MATERIALS[m_key]
                push_education(p["patient_id"], p["name"], m_key, m["title"], m["category"], "manual", st.session_state.username)
                st.success(f"✅ 已推送給 {p['name']}！")
    
    with tab2:
        pushes = get_education_pushes()
        for push in pushes[:15]:
            st.markdown(f"{'✅' if push.get('status')=='read' else '📤'} **{push.get('patient_name', '')}** - {push.get('material_title', '')} | {push.get('pushed_at', '')[:10]}")

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
        for i in get_interventions()[:15]:
            st.markdown(f"**{i.get('patient_name', '')}** | {i.get('method', '')} | {i.get('content', '')[:50]}... | {i.get('timestamp', '')[:10]}")
    
    with tab2:
        with st.form("new_int"):
            patients = get_all_patients()
            opts = {f"{p.get('name', '')}": p for p in patients}
            selected = st.selectbox("病人", ["--"] + list(opts.keys()))
            method = st.selectbox("方式", ["電話", "LINE", "門診"])
            content = st.text_area("內容")
            
            if st.form_submit_button("💾 儲存", type="primary") and selected != "--":
                p = opts[selected]
                save_intervention(p["patient_id"], p["name"], {"method": method, "content": content, "duration": ""}, st.session_state.username)
                st.success("✅ 已儲存！")

# ============================================
# 報表
# ============================================
def render_reports():
    st.markdown("## 📈 報表統計")
    if not GSHEETS_AVAILABLE:
        st.error("⚠️ 連線失敗")
        return
    
    patients = get_all_patients()
    reports = get_all_reports()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總病人", len(patients))
    col2.metric("總回報", len(reports))
    col3.metric("今日回報", len([r for r in reports if r.get("date") == datetime.now().strftime("%Y-%m-%d")]))
    col4.metric("待處理警示", len(get_pending_alerts()))

# ============================================
# 主程式
# ============================================
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        render_sidebar()
        page = st.session_state.admin_page
        if page == "dashboard": render_dashboard()
        elif page == "alerts": render_alerts()
        elif page == "patients": render_patients()
        elif page == "education": render_education()
        elif page == "interventions": render_interventions()
        elif page == "reports": render_reports()
        else: render_dashboard()

if __name__ == "__main__":
    main()
