"""
AI-CARE Lung - 管理後台（修正版）
================================

修正內容：
1. 病人選擇器資料不同步問題
2. API 配額優化（加入快取）
3. 整體穩定性提升
"""

import streamlit as st
from datetime import datetime, timedelta
import json

# ============================================
# 設定
# ============================================
SYSTEM_NAME = "AI-CARE Lung"
HOSPITAL_NAME = "三軍總醫院"
DEPARTMENT_NAME = "胸腔外科"

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
    st.error(f"Google Sheets 模組載入失敗: {e}")

# ============================================
# 頁面設定
# ============================================
st.set_page_config(
    page_title=f"{SYSTEM_NAME} - 管理後台",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CSS
# ============================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton > button { border-radius: 8px; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# Session State
# ============================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'username' not in st.session_state:
    st.session_state.username = ""

if 'current_page' not in st.session_state:
    st.session_state.current_page = "dashboard"

if 'selected_patient_id' not in st.session_state:
    st.session_state.selected_patient_id = None

# ============================================
# 登入頁面
# ============================================
def render_login():
    """登入頁面"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 40px 0;">
            <div style="font-size: 64px; margin-bottom: 16px;">🏥</div>
            <h1 style="color: #1e293b; margin-bottom: 4px;">{SYSTEM_NAME}</h1>
            <p style="color: #64748b;">管理後台</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("帳號", placeholder="輸入帳號")
            password = st.text_input("密碼", type="password", placeholder="輸入密碼")
            
            submit = st.form_submit_button("🔑 登入", use_container_width=True, type="primary")
            
            if submit:
                if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("登入成功！")
                    st.rerun()
                else:
                    st.error("帳號或密碼錯誤")
        
        st.caption("測試帳號：admin / aicare2024")

# ============================================
# 側邊欄
# ============================================
def render_sidebar():
    """側邊欄"""
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        st.caption(f"{HOSPITAL_NAME} {DEPARTMENT_NAME}")
        
        st.divider()
        
        menu_items = [
            ("📊", "dashboard", "儀表板"),
            ("⚠️", "alerts", "警示處理"),
            ("👥", "patients", "病人管理"),
            ("📝", "interventions", "介入紀錄"),
            ("📈", "reports", "報表統計"),
        ]
        
        for icon, key, label in menu_items:
            if st.button(f"{icon} {label}", key=f"menu_{key}", use_container_width=True):
                st.session_state.current_page = key
                st.rerun()
        
        st.divider()
        
        if st.button("🚪 登出", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

# ============================================
# 儀表板
# ============================================
def render_dashboard():
    """儀表板"""
    st.title("📊 儀表板")
    
    if not GSHEETS_AVAILABLE:
        st.error("無法連線到資料庫")
        return
    
    try:
        stats = get_dashboard_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 收案人數", stats.get("total_patients", 0))
        with col2:
            st.metric("📋 今日回報", stats.get("today_reports", 0))
        with col3:
            st.metric("🔴 紅色警示", stats.get("red_alerts", 0))
        with col4:
            st.metric("🟡 黃色警示", stats.get("yellow_alerts", 0))
        
        st.divider()
        
        # 待處理警示
        st.subheader("⚠️ 待處理警示")
        alerts = get_pending_alerts()
        
        if alerts:
            for alert in alerts[:5]:
                alert_color = "🔴" if alert.get("alert_level") == "red" else "🟡"
                st.warning(f"{alert_color} {alert.get('patient_name', '未知')} - 分數: {alert.get('overall_score', 0)} ({alert.get('date', '')})")
        else:
            st.success("✅ 目前沒有待處理的警示")
        
        # 今日回報
        st.divider()
        st.subheader("📋 今日回報")
        today_reports = get_today_reports()
        
        if today_reports:
            for report in today_reports:
                level_icon = "🔴" if report.get("alert_level") == "red" else "🟡" if report.get("alert_level") == "yellow" else "✅"
                st.info(f"{level_icon} {report.get('patient_name', '未知')} - 整體評分: {report.get('overall_score', 0)}/10")
        else:
            st.info("今日尚無回報")
            
    except Exception as e:
        st.error(f"載入資料失敗: {e}")

# ============================================
# 警示處理
# ============================================
def render_alerts():
    """警示處理"""
    st.title("⚠️ 警示處理")
    
    if not GSHEETS_AVAILABLE:
        st.error("無法連線到資料庫")
        return
    
    try:
        alerts = get_pending_alerts()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            red_count = len([a for a in alerts if a.get("alert_level") == "red"])
            st.metric("🔴 紅色警示", red_count)
        with col2:
            yellow_count = len([a for a in alerts if a.get("alert_level") == "yellow"])
            st.metric("🟡 黃色警示", yellow_count)
        with col3:
            st.metric("✅ 已處理今日", 0)
        
        st.divider()
        
        tab1, tab2 = st.tabs(["🔴 紅色警示", "🟡 黃色警示"])
        
        with tab1:
            red_alerts = [a for a in alerts if a.get("alert_level") == "red"]
            if red_alerts:
                for alert in red_alerts:
                    with st.expander(f"🔴 {alert.get('patient_name', '未知')} - {alert.get('date', '')}"):
                        st.write(f"**整體評分**: {alert.get('overall_score', 0)}/10")
                        st.write(f"**回報時間**: {alert.get('timestamp', '')}")
                        
                        if st.button(f"✅ 標記為已處理", key=f"handle_red_{alert.get('report_id')}"):
                            if handle_alert(alert.get('report_id'), st.session_state.username):
                                st.success("已標記為處理完成")
                                st.rerun()
            else:
                st.success("✅ 無紅色警示")
        
        with tab2:
            yellow_alerts = [a for a in alerts if a.get("alert_level") == "yellow"]
            if yellow_alerts:
                for alert in yellow_alerts:
                    with st.expander(f"🟡 {alert.get('patient_name', '未知')} - {alert.get('date', '')}"):
                        st.write(f"**整體評分**: {alert.get('overall_score', 0)}/10")
                        st.write(f"**回報時間**: {alert.get('timestamp', '')}")
                        
                        if st.button(f"✅ 標記為已處理", key=f"handle_yellow_{alert.get('report_id')}"):
                            if handle_alert(alert.get('report_id'), st.session_state.username):
                                st.success("已標記為處理完成")
                                st.rerun()
            else:
                st.success("✅ 無黃色警示")
                
    except Exception as e:
        st.error(f"讀取回報資料失敗: {e}")

# ============================================
# 病人管理（修正版）
# ============================================
def render_patients():
    """病人管理"""
    st.title("👥 病人管理")
    
    if not GSHEETS_AVAILABLE:
        st.error("無法連線到資料庫")
        return
    
    tab1, tab2, tab3 = st.tabs(["📋 病人列表", "📈 追蹤歷程", "⚙️ 病人設定"])
    
    # === 病人列表 ===
    with tab1:
        try:
            patients = get_all_patients()
            
            if patients:
                # 搜尋
                search = st.text_input("🔍 搜尋病人", placeholder="輸入姓名或病歷號")
                
                if search:
                    patients = [p for p in patients if search.lower() in str(p.get("name", "")).lower() or search in str(p.get("medical_record", ""))]
                
                # 顯示列表
                for patient in patients:
                    status_icon = "🟢" if patient.get("status") == "normal" else "🟡" if patient.get("status") == "pending_setup" else "🏥" if patient.get("status") == "hospitalized" else "⚪"
                    
                    with st.expander(f"{status_icon} {patient.get('name', '未知')} ({patient.get('patient_id', '')})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**電話**: {patient.get('phone', '')}")
                            st.write(f"**病歷號**: {patient.get('medical_record', '')}")
                            st.write(f"**年齡**: {patient.get('age', '')}")
                        with col2:
                            st.write(f"**手術日期**: {patient.get('surgery_date', '待設定')}")
                            st.write(f"**手術類型**: {patient.get('surgery_type', '待設定')}")
                            st.write(f"**術後天數**: D+{patient.get('post_op_day', 0)}")
                            st.write(f"**狀態**: {patient.get('status', '')}")
            else:
                st.info("尚無病人資料")
                
        except Exception as e:
            st.error(f"載入病人資料失敗: {e}")
    
    # === 追蹤歷程（新增）===
    with tab2:
        st.subheader("📈 病人追蹤歷程")
        
        try:
            patients = get_all_patients()
            
            if patients:
                # 選擇病人
                patient_options = {f"{p.get('name', '未知')} ({p.get('patient_id', '')}) - D+{p.get('post_op_day', 0)}": p.get('patient_id') for p in patients}
                
                selected_label = st.selectbox(
                    "選擇病人查看追蹤歷程",
                    options=list(patient_options.keys()),
                    key="history_patient_selector"
                )
                
                if selected_label:
                    selected_patient_id = patient_options[selected_label]
                    
                    # 找到病人資料
                    selected_patient = None
                    for p in patients:
                        if p.get("patient_id") == selected_patient_id:
                            selected_patient = p
                            break
                    
                    if selected_patient:
                        # 顯示病人基本資訊
                        st.markdown("---")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("姓名", selected_patient.get("name", ""))
                        with col2:
                            st.metric("術後天數", f"D+{selected_patient.get('post_op_day', 0)}")
                        with col3:
                            st.metric("手術類型", selected_patient.get("surgery_type", ""))
                        with col4:
                            st.metric("狀態", selected_patient.get("status", ""))
                        
                        # 取得該病人的所有回報
                        reports = get_patient_reports(selected_patient_id)
                        
                        if reports:
                            # 依日期排序
                            reports_sorted = sorted(reports, key=lambda x: x.get("date", ""), reverse=False)
                            
                            st.markdown("---")
                            st.subheader(f"📊 回報趨勢圖（共 {len(reports_sorted)} 筆回報）")
                            
                            # 準備圖表資料
                            import pandas as pd
                            
                            chart_data = []
                            for r in reports_sorted:
                                chart_data.append({
                                    "日期": r.get("date", ""),
                                    "整體評分": r.get("overall_score", 0),
                                    "警示等級": r.get("alert_level", "green")
                                })
                            
                            df = pd.DataFrame(chart_data)
                            
                            if not df.empty:
                                # 繪製折線圖
                                st.line_chart(df.set_index("日期")["整體評分"])
                                
                                # 統計摘要
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    avg_score = df["整體評分"].mean()
                                    st.metric("平均評分", f"{avg_score:.1f}")
                                with col2:
                                    red_count = len([r for r in reports_sorted if r.get("alert_level") == "red"])
                                    st.metric("🔴 紅色警示", f"{red_count} 次")
                                with col3:
                                    yellow_count = len([r for r in reports_sorted if r.get("alert_level") == "yellow"])
                                    st.metric("🟡 黃色警示", f"{yellow_count} 次")
                                with col4:
                                    green_count = len([r for r in reports_sorted if r.get("alert_level") == "green"])
                                    st.metric("✅ 正常", f"{green_count} 次")
                            
                            # 詳細回報列表
                            st.markdown("---")
                            st.subheader("📋 詳細回報紀錄")
                            
                            # 顯示選項
                            show_all = st.checkbox("顯示所有回報（預設只顯示最近 30 筆）")
                            
                            display_reports = reports_sorted if show_all else reports_sorted[-30:]
                            display_reports = sorted(display_reports, key=lambda x: x.get("date", ""), reverse=True)
                            
                            for report in display_reports:
                                alert_level = report.get("alert_level", "green")
                                if alert_level == "red":
                                    alert_icon = "🔴"
                                    alert_color = "red"
                                elif alert_level == "yellow":
                                    alert_icon = "🟡"
                                    alert_color = "orange"
                                else:
                                    alert_icon = "✅"
                                    alert_color = "green"
                                
                                handled = "已處理" if report.get("alert_handled") == "Y" else "未處理"
                                
                                with st.expander(f"{alert_icon} {report.get('date', '')} - 評分: {report.get('overall_score', 0)}/10 ({handled})"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**日期**: {report.get('date', '')}")
                                        st.write(f"**時間**: {report.get('timestamp', '')[:19] if report.get('timestamp') else ''}")
                                        st.write(f"**整體評分**: {report.get('overall_score', 0)}/10")
                                        st.write(f"**警示等級**: {alert_icon} {alert_level}")
                                    with col2:
                                        st.write(f"**處理狀態**: {handled}")
                                        st.write(f"**處理人**: {report.get('handled_by', '-')}")
                                        st.write(f"**對話輪數**: {report.get('messages_count', 0)}")
                                    
                                    # 顯示症狀詳情
                                    symptoms_str = report.get("symptoms", "{}")
                                    try:
                                        import json
                                        symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
                                        if symptoms:
                                            st.write("**症狀評分:**")
                                            symptom_names = {
                                                "dyspnea": "呼吸困難",
                                                "pain": "疼痛",
                                                "cough": "咳嗽",
                                                "fatigue": "疲勞",
                                                "sleep": "睡眠",
                                                "appetite": "食慾",
                                                "mood": "情緒"
                                            }
                                            cols = st.columns(4)
                                            for i, (key, value) in enumerate(symptoms.items()):
                                                with cols[i % 4]:
                                                    display_name = symptom_names.get(key, key)
                                                    st.write(f"- {display_name}: {value}/10")
                                    except:
                                        pass
                        else:
                            st.info("此病人尚無回報紀錄")
                        
                        # 介入紀錄
                        st.markdown("---")
                        st.subheader("📝 介入紀錄")
                        
                        interventions = get_interventions(selected_patient_id)
                        
                        if interventions:
                            for inv in interventions[:10]:
                                with st.expander(f"📝 {inv.get('date', '')} - {inv.get('method', '')}"):
                                    st.write(f"**聯繫方式**: {inv.get('method', '')}")
                                    st.write(f"**時長**: {inv.get('duration', '')} 分鐘")
                                    st.write(f"**內容**: {inv.get('content', '')}")
                                    st.write(f"**記錄者**: {inv.get('created_by', '')}")
                                    if inv.get('referral'):
                                        st.write(f"**轉介**: {inv.get('referral', '')}")
                        else:
                            st.info("此病人尚無介入紀錄")
            else:
                st.info("尚無病人資料")
                
        except Exception as e:
            st.error(f"載入追蹤歷程失敗: {e}")
    
    # === 病人設定（修正版）===
    with tab3:
        st.subheader("⚙️ 設定病人資料")
        
        try:
            patients = get_all_patients()
            
            # 篩選出待設定的病人
            pending_patients = [p for p in patients if p.get("status") == "pending_setup"]
            
            if pending_patients:
                st.warning(f"⚠️ 有 {len(pending_patients)} 位病人待設定")
            
            if patients:
                # 建立病人選項（ID: 姓名）
                patient_options = {f"{p.get('name', '未知')} ({p.get('patient_id', '')})": p.get('patient_id') for p in patients}
                
                selected_label = st.selectbox(
                    "選擇病人",
                    options=list(patient_options.keys()),
                    key="patient_selector"
                )
                
                if selected_label:
                    # 根據選擇的標籤找到對應的 patient_id
                    selected_patient_id = patient_options[selected_label]
                    
                    # 根據 patient_id 找到完整的病人資料
                    selected_patient = None
                    for p in patients:
                        if p.get("patient_id") == selected_patient_id:
                            selected_patient = p
                            break
                    
                    if selected_patient:
                        # 使用表單來編輯
                        with st.form(key="edit_patient_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.text_input("姓名", value=selected_patient.get("name", ""), disabled=True)
                                st.text_input("電話", value=str(selected_patient.get("phone", "")), disabled=True)
                                new_medical_record = st.text_input("病歷號", value=str(selected_patient.get("medical_record", "")))
                            
                            with col2:
                                # 手術日期
                                current_surgery_date = selected_patient.get("surgery_date", "")
                                if current_surgery_date:
                                    try:
                                        default_date = datetime.strptime(str(current_surgery_date), "%Y-%m-%d").date()
                                    except:
                                        default_date = datetime.now().date()
                                else:
                                    default_date = datetime.now().date()
                                
                                new_surgery_date = st.date_input("手術日期", value=default_date)
                                
                                # 手術類型
                                surgery_types = [
                                    "Lobectomy",
                                    "Wedge resection", 
                                    "Segmentectomy",
                                    "Pneumonectomy",
                                    "VATS",
                                    "其他"
                                ]
                                current_surgery_type = selected_patient.get("surgery_type", "")
                                if current_surgery_type in surgery_types:
                                    default_index = surgery_types.index(current_surgery_type)
                                else:
                                    default_index = 0
                                
                                new_surgery_type = st.selectbox("手術類型", surgery_types, index=default_index)
                                
                                # 狀態
                                status_options = ["pending_setup", "normal", "active", "discharged", "completed"]
                                current_status = selected_patient.get("status", "pending_setup")
                                if current_status in status_options:
                                    status_index = status_options.index(current_status)
                                else:
                                    status_index = 0
                                
                                new_status = st.selectbox("狀態", status_options, index=status_index)
                            
                            # 儲存按鈕
                            submit_button = st.form_submit_button("💾 儲存", use_container_width=True, type="primary")
                            
                            if submit_button:
                                updates = {
                                    "surgery_date": new_surgery_date.strftime("%Y-%m-%d"),
                                    "surgery_type": new_surgery_type,
                                    "status": new_status,
                                    "medical_record": new_medical_record
                                }
                                
                                if update_patient(selected_patient_id, updates):
                                    st.success(f"✅ 已更新 {selected_patient.get('name')} 的資料")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("更新失敗，請稍後再試")
                    else:
                        st.error("找不到選擇的病人資料")
            else:
                st.info("尚無病人資料")
                
        except Exception as e:
            st.error(f"載入病人資料失敗: {e}")

# ============================================
# 介入紀錄
# ============================================
def render_interventions():
    """介入紀錄"""
    st.title("📝 介入紀錄")
    
    if not GSHEETS_AVAILABLE:
        st.error("無法連線到資料庫")
        return
    
    tab1, tab2 = st.tabs(["📋 紀錄列表", "➕ 新增紀錄"])
    
    with tab1:
        try:
            interventions = get_interventions()
            
            if interventions:
                for inv in interventions[:20]:  # 只顯示最近 20 筆
                    with st.expander(f"📝 {inv.get('patient_name', '未知')} - {inv.get('date', '')}"):
                        st.write(f"**聯繫方式**: {inv.get('method', '')}")
                        st.write(f"**時長**: {inv.get('duration', '')} 分鐘")
                        st.write(f"**內容**: {inv.get('content', '')}")
                        st.write(f"**記錄者**: {inv.get('created_by', '')}")
            else:
                st.info("尚無介入紀錄")
                
        except Exception as e:
            st.error(f"載入介入紀錄失敗: {e}")
    
    with tab2:
        st.subheader("➕ 新增介入紀錄")
        
        try:
            patients = get_all_patients()
            
            if patients:
                with st.form("intervention_form"):
                    patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p for p in patients}
                    selected = st.selectbox("選擇病人", list(patient_options.keys()))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        method = st.selectbox("聯繫方式", ["電話", "LINE", "門診", "視訊", "其他"])
                    with col2:
                        duration = st.number_input("時長（分鐘）", min_value=1, max_value=120, value=10)
                    
                    content = st.text_area("紀錄內容", placeholder="請輸入介入紀錄內容...")
                    referral = st.text_input("轉介", placeholder="如有轉介請填寫")
                    
                    submit = st.form_submit_button("💾 儲存紀錄", use_container_width=True, type="primary")
                    
                    if submit:
                        if not content:
                            st.error("請填寫紀錄內容")
                        else:
                            patient = patient_options[selected]
                            intervention_id = save_intervention({
                                "patient_id": patient.get("patient_id"),
                                "patient_name": patient.get("name"),
                                "method": method,
                                "duration": duration,
                                "content": content,
                                "referral": referral,
                                "created_by": st.session_state.username
                            })
                            
                            if intervention_id:
                                st.success("✅ 紀錄已儲存")
                                st.rerun()
                            else:
                                st.error("儲存失敗")
            else:
                st.info("尚無病人資料")
                
        except Exception as e:
            st.error(f"載入資料失敗: {e}")

# ============================================
# 報表統計（進階版）
# ============================================
def render_reports():
    """報表統計"""
    try:
        from reports_module import render_advanced_reports
        render_advanced_reports(get_all_patients, get_all_reports, get_interventions, get_education_pushes)
    except ImportError as e:
        st.warning(f"進階報表模組未載入: {e}")
        st.info("請確認 reports_module.py 已上傳到 GitHub")
        render_simple_reports()
    except Exception as e:
        st.error(f"報表載入錯誤: {e}")
        render_simple_reports()

def render_simple_reports():
    """簡化版報表統計"""
    st.title("📈 報表統計")
    
    if not GSHEETS_AVAILABLE:
        st.error("無法連線到資料庫")
        return
    
    try:
        patients = get_all_patients()
        reports = get_all_reports()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 收案統計")
            st.metric("總收案數", len(patients))
            
            status_counts = {}
            for p in patients:
                status = p.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                st.write(f"- {status}: {count} 人")
        
        with col2:
            st.subheader("📋 回報統計")
            st.metric("總回報數", len(reports))
            
            alert_counts = {"green": 0, "yellow": 0, "red": 0}
            for r in reports:
                level = r.get("alert_level", "green")
                alert_counts[level] = alert_counts.get(level, 0) + 1
            
            st.write(f"- ✅ 綠色: {alert_counts['green']} 筆")
            st.write(f"- 🟡 黃色: {alert_counts['yellow']} 筆")
            st.write(f"- 🔴 紅色: {alert_counts['red']} 筆")
        
        st.divider()
        
        # 匯出功能
        st.subheader("📥 資料匯出")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 匯出病人資料 (CSV)", use_container_width=True):
                import pandas as pd
                df = pd.DataFrame(patients)
                csv = df.to_csv(index=False)
                st.download_button(
                    "⬇️ 下載 CSV",
                    csv,
                    "patients.csv",
                    "text/csv"
                )
        
        with col2:
            if st.button("📥 匯出回報資料 (CSV)", use_container_width=True):
                import pandas as pd
                df = pd.DataFrame(reports)
                csv = df.to_csv(index=False)
                st.download_button(
                    "⬇️ 下載 CSV",
                    csv,
                    "reports.csv",
                    "text/csv"
                )
                
    except Exception as e:
        st.error(f"載入統計資料失敗: {e}")

# ============================================
# 主程式
# ============================================
def main():
    """主程式"""
    if not st.session_state.logged_in:
        render_login()
    else:
        render_sidebar()
        
        page = st.session_state.current_page
        
        if page == "dashboard":
            render_dashboard()
        elif page == "alerts":
            render_alerts()
        elif page == "patients":
            render_patients()
        elif page == "interventions":
            render_interventions()
        elif page == "reports":
            render_reports()
        else:
            render_dashboard()

if __name__ == "__main__":
    main()
