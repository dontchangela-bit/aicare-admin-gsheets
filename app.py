"""
AI-CARE Lung - 管理後台（美化版）
================================

修正內容：
1. 病人選擇器資料不同步問題
2. API 配額優化（加入快取）
3. 整體穩定性提升
4. UI 美化與品牌視覺
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
        get_dashboard_stats, get_today_reports,
        get_schedules, save_schedule, update_schedule,
        get_lab_results, save_lab_result,
        get_functional_assessments, save_functional_assessment,
        get_problems, save_problem, update_problem
    )
    GSHEETS_AVAILABLE = True
except Exception as e:
    GSHEETS_AVAILABLE = False
    st.error(f"Google Sheets 模組載入失敗: {e}")

# 病人管理模組
try:
    from patient_module import render_patient_management
    PATIENT_MODULE_AVAILABLE = True
except:
    PATIENT_MODULE_AVAILABLE = False

# 視訊介入模組
try:
    from video_module import render_video_consultation
    VIDEO_MODULE_AVAILABLE = True
except:
    VIDEO_MODULE_AVAILABLE = False

# UI 美化模組
try:
    from ui_styles import (
        init_page_style, render_header, render_logo_sidebar,
        render_info_card, render_alert_card, render_stat_card,
        render_empty_state, render_progress_steps, COLORS
    )
    UI_STYLES_AVAILABLE = True
except:
    UI_STYLES_AVAILABLE = False

# ============================================
# 頁面設定
# ============================================
st.set_page_config(
    page_title=f"{SYSTEM_NAME} - 管理後台",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 套用自訂樣式
if UI_STYLES_AVAILABLE:
    init_page_style()

# ============================================
# CSS（備用，如果 ui_styles 未載入）
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
    """側邊欄（美化版）"""
    with st.sidebar:
        # Logo 區塊
        if UI_STYLES_AVAILABLE:
            render_logo_sidebar()
        else:
            st.markdown("""
            <div style="text-align: center; padding: 20px; margin-bottom: 20px;">
                <div style="font-size: 50px;">🫁</div>
                <div style="font-size: 18px; font-weight: 700; color: white;">AI-CARE Lung</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 使用者資訊
        st.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            text-align: center;
        ">
            <div style="font-size: 14px; color: rgba(255,255,255,0.7);">👤 目前登入</div>
            <div style="font-size: 16px; font-weight: 600; color: white;">{st.session_state.username}</div>
            <div style="font-size: 12px; color: rgba(255,255,255,0.5);">{HOSPITAL_NAME}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # 主選單
        menu_items = [
            ("📊", "dashboard", "儀表板"),
            ("⚠️", "alerts", "警示處理"),
            ("👥", "patients", "病人管理"),
            ("📹", "video", "視訊介入"),
            ("📚", "education", "衛教管理"),
            ("📝", "interventions", "介入紀錄"),
            ("📈", "reports", "報表統計"),
        ]
        
        for icon, key, label in menu_items:
            is_active = st.session_state.get("current_page") == key
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon} {label}", key=f"menu_{key}", use_container_width=True, type=btn_type if is_active else "secondary"):
                st.session_state.current_page = key
                st.rerun()
        
        st.divider()
        
        # 快速統計（如果有資料）
        if GSHEETS_AVAILABLE:
            try:
                alerts = get_pending_alerts()
                red_count = len([a for a in alerts if a.get("alert_level") == "red"])
                yellow_count = len([a for a in alerts if a.get("alert_level") == "yellow"])
                
                if red_count > 0 or yellow_count > 0:
                    st.markdown(f"""
                    <div style="
                        background: rgba(255,82,82,0.2);
                        border: 1px solid rgba(255,82,82,0.5);
                        border-radius: 10px;
                        padding: 10px;
                        margin-bottom: 15px;
                    ">
                        <div style="color: white; font-size: 12px; text-align: center;">
                            ⚠️ 待處理警示<br>
                            <span style="font-size: 20px; font-weight: bold;">🔴 {red_count} | 🟡 {yellow_count}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            except:
                pass
        
        # 登出按鈕
        if st.button("🚪 登出", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
        
        # 版本資訊
        st.markdown("""
        <div style="
            position: fixed;
            bottom: 20px;
            left: 20px;
            font-size: 10px;
            color: rgba(255,255,255,0.3);
        ">
            v1.5.0 | © 2024 AI-CARE
        </div>
        """, unsafe_allow_html=True)

# ============================================
# 儀表板
# ============================================
def render_dashboard():
    """儀表板（美化版）"""
    
    # 頁首
    if UI_STYLES_AVAILABLE:
        render_header("AI-CARE Lung", "智慧肺癌術後照護管理系統")
    else:
        st.title("📊 AI-CARE Lung 管理儀表板")
    
    if not GSHEETS_AVAILABLE:
        if UI_STYLES_AVAILABLE:
            render_empty_state("無法連線到資料庫", "❌")
        else:
            st.error("無法連線到資料庫")
        return
    
    try:
        # 取得所有資料
        patients = get_all_patients()
        reports = get_all_reports()
        alerts = get_pending_alerts()
        interventions = get_interventions()
        schedules = get_schedules()
        
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today_reports = [r for r in reports if r.get("date") == today]
        yesterday_reports = [r for r in reports if r.get("date") == yesterday]
        
        # ============================================
        # 第一行：核心 KPI（8 個指標）
        # ============================================
        st.markdown("### 📈 核心指標")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            active_patients = len([p for p in patients if p.get("status") not in ["discharged", "withdrawn", "completed"]])
            new_this_week = len([p for p in patients if p.get("post_op_day", 0) <= 7])
            st.metric("👥 收案中", active_patients, 
                     delta=f"+{new_this_week} 本週新" if new_this_week else None)
        
        with col2:
            today_delta = len(today_reports) - len(yesterday_reports)
            st.metric("📋 今日回報", len(today_reports),
                     delta=f"{today_delta:+d} vs 昨日" if yesterday_reports else None,
                     delta_color="normal" if today_delta >= 0 else "inverse")
        
        with col3:
            adherence = len(today_reports) / active_patients * 100 if active_patients else 0
            st.metric("✅ 今日依從率", f"{adherence:.0f}%",
                     delta="🎯 達標" if adherence >= 70 else "⚠️ 待加強",
                     delta_color="normal" if adherence >= 70 else "inverse")
        
        with col4:
            red_count = len([a for a in alerts if a.get("alert_level") == "red"])
            yellow_count = len([a for a in alerts if a.get("alert_level") == "yellow"])
            st.metric("⚠️ 待處理警示", red_count + yellow_count,
                     delta=f"🔴{red_count} 🟡{yellow_count}" if alerts else "✅ 無警示",
                     delta_color="inverse" if alerts else "off")
        
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            # 今日待辦
            today_schedules = [s for s in schedules if s.get("scheduled_date") == today and s.get("status") != "completed"]
            st.metric("📅 今日待辦", len(today_schedules))
        
        with col6:
            # 今日視訊
            today_videos = [s for s in today_schedules if "視訊" in s.get("schedule_type", "")]
            st.metric("📹 今日視訊", len(today_videos))
        
        with col7:
            # 本週介入
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            week_interventions = len([i for i in interventions if i.get("date", "") >= week_ago])
            st.metric("📝 本週介入", week_interventions)
        
        with col8:
            # 高風險病人
            high_risk = len([p for p in patients if p.get("risk_level") == "高風險"])
            st.metric("🔴 高風險", high_risk,
                     delta="需密切追蹤" if high_risk > 0 else None,
                     delta_color="inverse" if high_risk > 0 else "off")
        
        st.divider()
        
        # ============================================
        # 第二行：警示與今日待辦
        # ============================================
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### ⚠️ 待處理警示")
            
            if alerts:
                # 優先顯示紅色警示
                red_alerts = [a for a in alerts if a.get("alert_level") == "red"]
                yellow_alerts = [a for a in alerts if a.get("alert_level") == "yellow"]
                
                for alert in (red_alerts + yellow_alerts)[:5]:
                    alert_icon = "🔴" if alert.get("alert_level") == "red" else "🟡"
                    patient = next((p for p in patients if p.get("patient_id") == alert.get("patient_id")), {})
                    
                    # 計算等待時間
                    try:
                        timestamp = alert.get("timestamp", "")
                        if timestamp:
                            report_time = datetime.fromisoformat(timestamp.split(".")[0])
                            wait_hours = (datetime.now() - report_time).total_seconds() / 3600
                            if wait_hours > 24:
                                wait_text = f"⏰ {wait_hours:.0f}h"
                            else:
                                wait_text = f"{wait_hours:.0f}h"
                        else:
                            wait_text = ""
                    except:
                        wait_text = ""
                    
                    bg_color = '#ffebee' if alert.get('alert_level') == 'red' else '#fff8e1'
                    st.markdown(f"""
                    <div style="background-color: {bg_color}; 
                                padding: 10px; border-radius: 5px; margin-bottom: 8px;">
                    <b>{alert_icon} {alert.get('patient_name', '')}</b> | 
                    D+{patient.get('post_op_day', 0)} | 
                    評分 {alert.get('overall_score', 0)}/10 | 
                    {wait_text}
                    </div>
                    """, unsafe_allow_html=True)
                
                if len(alerts) > 5:
                    st.caption(f"... 還有 {len(alerts) - 5} 筆待處理")
                
                if st.button("🔍 前往警示處理", key="goto_alerts", type="primary"):
                    st.session_state.current_page = "alerts"
                    st.rerun()
            else:
                st.success("✅ 目前沒有待處理的警示")
        
        with col_right:
            st.markdown("### 📅 今日待辦事項")
            
            # 合併視訊和其他排程
            today_videos = [s for s in today_schedules if "視訊" in s.get("schedule_type", "")]
            today_others = [s for s in today_schedules if "視訊" not in s.get("schedule_type", "")]
            
            if today_videos:
                st.markdown("**📹 視訊諮詢**")
                for s in sorted(today_videos, key=lambda x: x.get("scheduled_time", ""))[:3]:
                    st.markdown(f"""
                    <div style="background-color: #e3f2fd; padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                    🎥 {s.get('scheduled_time', '')} | <b>{s.get('patient_name', '')}</b>
                    </div>
                    """, unsafe_allow_html=True)
            
            if today_others:
                st.markdown("**📋 其他排程**")
                for s in sorted(today_others, key=lambda x: x.get("scheduled_time", ""))[:3]:
                    st.info(f"📌 {s.get('scheduled_time', '')} | {s.get('patient_name', '')} | {s.get('schedule_type', '')}")
            
            if not today_schedules:
                st.info("今日無排程")
            
            # 逾期提醒
            overdue = [s for s in schedules if s.get("scheduled_date", "") < today and s.get("status") != "completed"]
            if overdue:
                st.error(f"⏰ 有 {len(overdue)} 筆逾期排程需要處理")
            
            if today_videos and st.button("📹 前往視訊介入", key="goto_video"):
                st.session_state.current_page = "video"
                st.rerun()
        
        st.divider()
        
        # ============================================
        # 第三行：今日回報摘要
        # ============================================
        st.markdown("### 📋 今日回報摘要")
        
        if today_reports:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # 警示分布
                red = len([r for r in today_reports if r.get("alert_level") == "red"])
                yellow = len([r for r in today_reports if r.get("alert_level") == "yellow"])
                green = len([r for r in today_reports if r.get("alert_level") == "green"])
                
                st.markdown("**警示分布**")
                st.markdown(f"🔴 {red} | 🟡 {yellow} | 🟢 {green}")
            
            with col2:
                # 平均分數
                scores = [r.get("overall_score", 0) for r in today_reports if r.get("overall_score")]
                avg_score = sum(scores) / len(scores) if scores else 0
                st.markdown("**平均症狀評分**")
                score_color = "🔴" if avg_score >= 7 else "🟡" if avg_score >= 4 else "🟢"
                st.markdown(f"{score_color} {avg_score:.1f} / 10")
            
            with col3:
                # 已處理
                handled = len([r for r in today_reports if r.get("alert_handled") == "Y"])
                need_handle = red + yellow
                st.markdown("**警示處理**")
                st.markdown(f"✅ {handled} / {need_handle} 已處理")
            
            with col4:
                # AI 對話摘要數
                with_summary = len([r for r in today_reports if r.get("ai_summary")])
                st.markdown("**AI 摘要**")
                st.markdown(f"🤖 {with_summary} / {len(today_reports)} 筆")
            
            # 回報列表
            st.markdown("---")
            st.markdown("**最新回報**")
            
            for report in sorted(today_reports, key=lambda x: x.get("timestamp", ""), reverse=True)[:8]:
                level_icon = "🔴" if report.get("alert_level") == "red" else "🟡" if report.get("alert_level") == "yellow" else "✅"
                handled_icon = "✔️" if report.get("alert_handled") == "Y" else ""
                patient = next((p for p in patients if p.get("patient_id") == report.get("patient_id")), {})
                
                col_a, col_b, col_c, col_d = st.columns([3, 2, 2, 1])
                with col_a:
                    st.write(f"{level_icon} **{report.get('patient_name', '')}** D+{patient.get('post_op_day', 0)}")
                with col_b:
                    st.write(f"評分: {report.get('overall_score', 0)}/10")
                with col_c:
                    time_str = report.get("timestamp", "")[:16].split("T")[-1] if report.get("timestamp") else ""
                    st.write(f"🕐 {time_str}")
                with col_d:
                    st.write(handled_icon)
        else:
            st.warning("⚠️ 今日尚無回報，請提醒病人進行每日症狀回報")
            
            # 未回報病人清單
            reported_ids = set([r.get("patient_id") for r in today_reports])
            not_reported = [p for p in patients 
                          if p.get("patient_id") not in reported_ids 
                          and p.get("status") not in ["discharged", "withdrawn", "completed"]]
            
            if not_reported:
                with st.expander(f"📋 今日未回報病人 ({len(not_reported)} 人)"):
                    for p in not_reported[:10]:
                        st.write(f"• {p.get('name', '')} | D+{p.get('post_op_day', 0)} | 📱 {p.get('phone', '')}")
        
        st.divider()
        
        # ============================================
        # 第四行：趨勢圖表
        # ============================================
        st.markdown("### 📈 近期趨勢")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**每日回報數與警示數（近 14 天）**")
            
            # 最近 14 天統計
            daily_stats = {}
            for i in range(14):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                daily_stats[date] = {"回報數": 0, "警示數": 0, "紅色": 0, "黃色": 0}
            
            for r in reports:
                date = r.get("date", "")
                if date in daily_stats:
                    daily_stats[date]["回報數"] += 1
                    if r.get("alert_level") == "red":
                        daily_stats[date]["紅色"] += 1
                        daily_stats[date]["警示數"] += 1
                    elif r.get("alert_level") == "yellow":
                        daily_stats[date]["黃色"] += 1
                        daily_stats[date]["警示數"] += 1
            
            import plotly.graph_objects as go
            
            dates = sorted(daily_stats.keys())
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=dates,
                y=[daily_stats[d]["回報數"] for d in dates],
                name="回報數",
                marker_color="#2196F3"
            ))
            fig.add_trace(go.Scatter(
                x=dates,
                y=[daily_stats[d]["紅色"] for d in dates],
                name="🔴 紅色",
                mode="lines+markers",
                line=dict(color="#dc3545", width=2)
            ))
            fig.add_trace(go.Scatter(
                x=dates,
                y=[daily_stats[d]["黃色"] for d in dates],
                name="🟡 黃色",
                mode="lines+markers",
                line=dict(color="#ffc107", width=2)
            ))
            fig.update_layout(
                height=280, 
                margin=dict(l=0, r=0, t=30, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**症狀分布（近 7 天中度以上）**")
            
            # 統計症狀
            symptom_counts = {}
            symptom_names = {
                "pain": "疼痛", "dyspnea": "呼吸困難", "cough": "咳嗽",
                "fatigue": "疲勞", "sleep": "睡眠", "appetite": "食慾", "mood": "情緒"
            }
            
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            recent_reports = [r for r in reports if r.get("date", "") >= week_ago]
            
            for r in recent_reports:
                symptoms_str = r.get("symptoms", "{}")
                try:
                    symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
                    for key, value in symptoms.items():
                        if int(value) >= 4:  # 中度以上
                            name = symptom_names.get(key, key)
                            symptom_counts[name] = symptom_counts.get(name, 0) + 1
                except:
                    pass
            
            if symptom_counts:
                sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
                
                import plotly.express as px
                fig = px.bar(
                    x=[s[0] for s in sorted_symptoms],
                    y=[s[1] for s in sorted_symptoms],
                    color=[s[1] for s in sorted_symptoms],
                    color_continuous_scale="Reds"
                )
                fig.update_layout(
                    height=280, 
                    margin=dict(l=0, r=0, t=30, b=0),
                    showlegend=False,
                    xaxis_title="",
                    yaxis_title="次數",
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("近 7 天無中度以上症狀")
        
        # ============================================
        # 第五行：快速操作
        # ============================================
        st.divider()
        st.markdown("### ⚡ 快速操作")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("➕ 新增病人", use_container_width=True):
                st.session_state.current_page = "patients"
                st.rerun()
        
        with col2:
            if st.button("📹 排程視訊", use_container_width=True):
                st.session_state.current_page = "video"
                st.rerun()
        
        with col3:
            if st.button("📝 新增介入", use_container_width=True):
                st.session_state.current_page = "interventions"
                st.rerun()
        
        with col4:
            if st.button("📚 推播衛教", use_container_width=True):
                st.session_state.current_page = "education"
                st.rerun()
        
        with col5:
            if st.button("📈 查看報表", use_container_width=True):
                st.session_state.current_page = "reports"
                st.rerun()
                
    except Exception as e:
        st.error(f"載入儀表板失敗: {e}")
        import traceback
        st.code(traceback.format_exc())

# ============================================
# 警示處理
# ============================================
def render_alerts():
    """警示處理（完整版）"""
    st.title("⚠️ 警示處理中心")
    
    if not GSHEETS_AVAILABLE:
        st.error("無法連線到資料庫")
        return
    
    # 警示嚴重度定義
    ALERT_SEVERITY = {
        "red": {
            "name": "紅色警示",
            "icon": "🔴",
            "color": "#dc3545",
            "criteria": "嚴重症狀 (≥7分) 或多項中度症狀",
            "action": "24小時內主動聯繫",
            "priority": 1
        },
        "yellow": {
            "name": "黃色警示",
            "icon": "🟡", 
            "color": "#ffc107",
            "criteria": "中度症狀 (4-6分)",
            "action": "48小時內追蹤",
            "priority": 2
        },
        "green": {
            "name": "正常",
            "icon": "✅",
            "color": "#28a745",
            "criteria": "症狀輕微 (≤3分)",
            "action": "持續監測",
            "priority": 3
        }
    }
    
    # 處理選項
    HANDLING_OPTIONS = [
        "電話關懷",
        "LINE 訊息追蹤",
        "視訊評估",
        "安排提前回診",
        "轉介疼痛科",
        "轉介營養師",
        "轉介心理師",
        "轉介急診評估",
        "衛教指導",
        "藥物調整建議",
        "持續觀察",
        "其他"
    ]
    
    try:
        alerts = get_pending_alerts()
        all_reports = get_all_reports()
        patients = get_all_patients()
        
        # === KPI 指標 ===
        col1, col2, col3, col4, col5 = st.columns(5)
        
        red_alerts = [a for a in alerts if a.get("alert_level") == "red"]
        yellow_alerts = [a for a in alerts if a.get("alert_level") == "yellow"]
        
        # 計算今日已處理
        today = datetime.now().strftime("%Y-%m-%d")
        today_handled = len([r for r in all_reports if 
                           r.get("alert_handled") == "Y" and 
                           r.get("handled_time", "").startswith(today)])
        
        # 計算平均處理時間（簡化版）
        avg_response = "< 24h"  # 實際應計算
        
        with col1:
            st.metric("🔴 紅色警示", len(red_alerts), 
                     delta=f"需 24h 內處理" if red_alerts else None,
                     delta_color="inverse" if red_alerts else "off")
        with col2:
            st.metric("🟡 黃色警示", len(yellow_alerts),
                     delta=f"需 48h 內追蹤" if yellow_alerts else None,
                     delta_color="inverse" if yellow_alerts else "off")
        with col3:
            st.metric("📊 待處理總數", len(alerts))
        with col4:
            st.metric("✅ 今日已處理", today_handled)
        with col5:
            st.metric("⏱️ 平均回應", avg_response)
        
        st.divider()
        
        # === 標籤頁 ===
        tab1, tab2, tab3, tab4 = st.tabs([
            f"🔴 紅色警示 ({len(red_alerts)})", 
            f"🟡 黃色警示 ({len(yellow_alerts)})",
            "📊 警示統計",
            "📋 處理紀錄"
        ])
        
        # === 紅色警示 ===
        with tab1:
            if red_alerts:
                st.error(f"⚠️ 有 {len(red_alerts)} 位病人需要立即關注！")
                
                for alert in sorted(red_alerts, key=lambda x: x.get("timestamp", ""), reverse=True):
                    render_alert_card(alert, patients, HANDLING_OPTIONS, "red")
            else:
                st.success("✅ 目前沒有紅色警示")
        
        # === 黃色警示 ===
        with tab2:
            if yellow_alerts:
                st.warning(f"⚠️ 有 {len(yellow_alerts)} 位病人需要追蹤")
                
                for alert in sorted(yellow_alerts, key=lambda x: x.get("timestamp", ""), reverse=True):
                    render_alert_card(alert, patients, HANDLING_OPTIONS, "yellow")
            else:
                st.success("✅ 目前沒有黃色警示")
        
        # === 警示統計 ===
        with tab3:
            render_alert_statistics(all_reports, patients)
        
        # === 處理紀錄 ===
        with tab4:
            render_handling_history(all_reports)
                
    except Exception as e:
        st.error(f"讀取資料失敗: {e}")


def render_alert_card(alert, patients, handling_options, alert_type):
    """渲染警示卡片"""
    patient_id = alert.get("patient_id")
    patient = next((p for p in patients if p.get("patient_id") == patient_id), {})
    
    # 計算等待時間
    timestamp = alert.get("timestamp", "")
    if timestamp:
        try:
            report_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00").split(".")[0])
            wait_hours = (datetime.now() - report_time).total_seconds() / 3600
            wait_text = f"{wait_hours:.1f} 小時前"
            urgent = wait_hours > 24 if alert_type == "red" else wait_hours > 48
        except:
            wait_text = timestamp[:16]
            urgent = False
    else:
        wait_text = "未知"
        urgent = False
    
    icon = "🔴" if alert_type == "red" else "🟡"
    urgent_badge = "⏰ 超時！" if urgent else ""
    
    with st.expander(f"{icon} {alert.get('patient_name', '未知')} - D+{patient.get('post_op_day', 0)} - 評分 {alert.get('overall_score', 0)}/10 {urgent_badge}", expanded=urgent):
        # === 病人資訊 ===
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**👤 病人資訊**")
            st.write(f"姓名: {alert.get('patient_name', '')}")
            st.write(f"電話: {patient.get('phone', '')}")
            st.write(f"術後: D+{patient.get('post_op_day', 0)}")
            st.write(f"手術: {patient.get('surgery_type', '')}")
        
        with col2:
            st.markdown("**📊 回報摘要**")
            st.write(f"日期: {alert.get('date', '')}")
            st.write(f"時間: {wait_text}")
            st.write(f"整體評分: {alert.get('overall_score', 0)}/10")
            st.write(f"對話輪數: {alert.get('messages_count', 0)}")
        
        with col3:
            st.markdown("**⚠️ 警示資訊**")
            st.write(f"等級: {icon} {alert_type.upper()}")
            if alert_type == "red":
                st.write("建議: 24小時內主動聯繫")
            else:
                st.write("建議: 48小時內追蹤")
        
        # === 症狀詳情 ===
        st.markdown("**🩺 症狀詳情**")
        symptoms_str = alert.get("symptoms", "{}")
        try:
            symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
            if symptoms:
                symptom_names = {
                    "dyspnea": "呼吸困難", "pain": "疼痛", "cough": "咳嗽",
                    "fatigue": "疲勞", "sleep": "睡眠", "appetite": "食慾", "mood": "情緒"
                }
                
                cols = st.columns(7)
                for i, (key, value) in enumerate(symptoms.items()):
                    score = int(value) if str(value).isdigit() else 0
                    name = symptom_names.get(key, key)
                    
                    # 顏色編碼
                    if score >= 7:
                        color = "🔴"
                    elif score >= 4:
                        color = "🟡"
                    else:
                        color = "🟢"
                    
                    with cols[i % 7]:
                        st.write(f"{color} {name}: {score}")
        except:
            st.write("無法解析症狀資料")
        
        # === AI 對話摘要 ===
        ai_summary = alert.get("ai_summary", "")
        if ai_summary:
            st.markdown("**🤖 AI 對話摘要**")
            st.info(ai_summary)
        
        # === 對話內容 ===
        conversation_str = alert.get("conversation", "")
        if conversation_str:
            with st.expander("💬 查看完整對話內容"):
                try:
                    conversation = json.loads(conversation_str) if isinstance(conversation_str, str) else conversation_str
                    if conversation:
                        for msg in conversation:
                            role = msg.get("role", "")
                            content = msg.get("content", "")
                            if role == "user":
                                st.markdown(f"**🧑 病人**: {content}")
                            elif role == "assistant":
                                st.markdown(f"**🤖 AI**: {content}")
                            st.markdown("---")
                except:
                    st.write("無法解析對話內容")
        
        # === 處理表單 ===
        st.markdown("---")
        st.markdown("**📝 處理紀錄**")
        
        with st.form(key=f"handle_form_{alert.get('report_id')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                handling_action = st.selectbox(
                    "處理方式 *",
                    handling_options,
                    key=f"action_{alert.get('report_id')}"
                )
            
            with col2:
                handling_result = st.selectbox(
                    "處理結果",
                    ["已聯繫病人", "已留言待回覆", "病人無接聽", "已完成指導", "已安排回診", "已轉介", "持續追蹤"],
                    key=f"result_{alert.get('report_id')}"
                )
            
            handling_notes = st.text_area(
                "處理備註",
                placeholder="請記錄處理內容、病人反應、後續計畫...",
                key=f"notes_{alert.get('report_id')}"
            )
            
            col_a, col_b, col_c = st.columns([2, 2, 1])
            
            with col_a:
                create_intervention = st.checkbox("同時建立介入紀錄", value=True, key=f"int_{alert.get('report_id')}")
            
            with col_b:
                need_followup = st.checkbox("需要後續追蹤", key=f"followup_{alert.get('report_id')}")
            
            submitted = st.form_submit_button("✅ 完成處理", type="primary", use_container_width=True)
            
            if submitted:
                # 更新警示狀態
                success = handle_alert(
                    alert.get('report_id'), 
                    st.session_state.username,
                    handling_action,
                    handling_notes
                )
                
                if success:
                    # 如果勾選建立介入紀錄
                    if create_intervention:
                        intervention_data = {
                            "patient_id": patient_id,
                            "patient_name": alert.get("patient_name"),
                            "intervention_type": handling_action,
                            "intervention_category": "警示處理",
                            "method": handling_action.split()[0] if handling_action else "電話",
                            "duration": 10,
                            "problem_addressed": f"警示處理: {alert_type}色警示, 評分{alert.get('overall_score')}/10",
                            "content": f"處理方式: {handling_action}\n處理結果: {handling_result}\n備註: {handling_notes}",
                            "outcome": "待評估",
                            "created_by": st.session_state.username
                        }
                        save_intervention(intervention_data)
                    
                    st.success("✅ 警示已處理完成！")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("處理失敗，請重試")


def render_alert_statistics(all_reports, patients):
    """警示統計分析"""
    st.subheader("📊 警示統計分析")
    
    if not all_reports:
        st.info("尚無回報資料")
        return
    
    import pandas as pd
    
    # === 時間範圍篩選 ===
    col1, col2 = st.columns(2)
    with col1:
        date_range = st.selectbox("時間範圍", ["最近 7 天", "最近 30 天", "最近 90 天", "全部"])
    
    # 篩選資料
    today = datetime.now().date()
    if date_range == "最近 7 天":
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    elif date_range == "最近 30 天":
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    elif date_range == "最近 90 天":
        start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    else:
        start_date = "2000-01-01"
    
    filtered_reports = [r for r in all_reports if r.get("date", "") >= start_date]
    
    if not filtered_reports:
        st.info("此期間無回報資料")
        return
    
    # === KPI ===
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(filtered_reports)
    red = len([r for r in filtered_reports if r.get("alert_level") == "red"])
    yellow = len([r for r in filtered_reports if r.get("alert_level") == "yellow"])
    green = len([r for r in filtered_reports if r.get("alert_level") == "green"])
    
    col1.metric("總回報數", total)
    col2.metric("🔴 紅色警示", red, delta=f"{red/total*100:.1f}%" if total else "0%")
    col3.metric("🟡 黃色警示", yellow, delta=f"{yellow/total*100:.1f}%" if total else "0%")
    col4.metric("✅ 正常", green, delta=f"{green/total*100:.1f}%" if total else "0%")
    
    st.divider()
    
    # === 圖表 ===
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📈 警示等級分布")
        try:
            import plotly.express as px
            
            alert_counts = {"紅色": red, "黃色": yellow, "綠色": green}
            fig = px.pie(
                values=list(alert_counts.values()),
                names=list(alert_counts.keys()),
                color=list(alert_counts.keys()),
                color_discrete_map={"紅色": "#dc3545", "黃色": "#ffc107", "綠色": "#28a745"},
                hole=0.4
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.bar_chart({"紅色": red, "黃色": yellow, "綠色": green})
    
    with col2:
        st.markdown("##### 📊 每日警示趨勢")
        
        # 按日期統計
        daily_stats = {}
        for r in filtered_reports:
            date = r.get("date", "")
            if date not in daily_stats:
                daily_stats[date] = {"red": 0, "yellow": 0, "green": 0}
            level = r.get("alert_level", "green")
            daily_stats[date][level] = daily_stats[date].get(level, 0) + 1
        
        if daily_stats:
            df = pd.DataFrame([
                {"日期": k, "紅色": v.get("red", 0), "黃色": v.get("yellow", 0)}
                for k, v in sorted(daily_stats.items())
            ])
            if not df.empty:
                st.line_chart(df.set_index("日期"))
    
    # === 高頻警示病人 ===
    st.markdown("##### 🔔 高頻警示病人")
    
    patient_alerts = {}
    for r in filtered_reports:
        if r.get("alert_level") in ["red", "yellow"]:
            pid = r.get("patient_id")
            pname = r.get("patient_name")
            if pid not in patient_alerts:
                patient_alerts[pid] = {"name": pname, "red": 0, "yellow": 0, "total": 0}
            patient_alerts[pid][r.get("alert_level")] += 1
            patient_alerts[pid]["total"] += 1
    
    if patient_alerts:
        # 排序並取前 10
        sorted_patients = sorted(patient_alerts.items(), key=lambda x: x[1]["total"], reverse=True)[:10]
        
        alert_df = pd.DataFrame([
            {
                "病人": v["name"],
                "🔴 紅色": v["red"],
                "🟡 黃色": v["yellow"],
                "總計": v["total"]
            }
            for pid, v in sorted_patients
        ])
        
        st.dataframe(alert_df, hide_index=True, use_container_width=True)
    else:
        st.success("此期間無警示紀錄")
    
    # === 常見警示症狀 ===
    st.markdown("##### 🩺 常見警示症狀")
    
    symptom_counts = {}
    symptom_names = {
        "dyspnea": "呼吸困難", "pain": "疼痛", "cough": "咳嗽",
        "fatigue": "疲勞", "sleep": "睡眠", "appetite": "食慾", "mood": "情緒"
    }
    
    for r in filtered_reports:
        if r.get("alert_level") in ["red", "yellow"]:
            symptoms_str = r.get("symptoms", "{}")
            try:
                symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
                for key, value in symptoms.items():
                    if int(value) >= 4:  # 中度以上
                        name = symptom_names.get(key, key)
                        symptom_counts[name] = symptom_counts.get(name, 0) + 1
            except:
                pass
    
    if symptom_counts:
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        symptom_df = pd.DataFrame(sorted_symptoms, columns=["症狀", "次數"])
        
        try:
            import plotly.express as px
            fig = px.bar(symptom_df, x="症狀", y="次數", color="次數",
                        color_continuous_scale="Reds")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.bar_chart(symptom_df.set_index("症狀"))


def render_handling_history(all_reports):
    """處理紀錄"""
    st.subheader("📋 警示處理紀錄")
    
    # 篩選已處理的警示
    handled = [r for r in all_reports if r.get("alert_handled") == "Y" and r.get("alert_level") in ["red", "yellow"]]
    
    if not handled:
        st.info("尚無處理紀錄")
        return
    
    # 篩選
    col1, col2 = st.columns(2)
    with col1:
        handler_filter = st.selectbox("處理人", ["全部"] + list(set([r.get("handled_by", "") for r in handled if r.get("handled_by")])))
    with col2:
        level_filter = st.selectbox("警示等級", ["全部", "red", "yellow"])
    
    filtered = handled
    if handler_filter != "全部":
        filtered = [r for r in filtered if r.get("handled_by") == handler_filter]
    if level_filter != "全部":
        filtered = [r for r in filtered if r.get("alert_level") == level_filter]
    
    st.info(f"共 {len(filtered)} 筆處理紀錄")
    
    for r in sorted(filtered, key=lambda x: x.get("handled_time", ""), reverse=True)[:50]:
        icon = "🔴" if r.get("alert_level") == "red" else "🟡"
        
        with st.expander(f"{icon} {r.get('patient_name', '')} - {r.get('date', '')} - 由 {r.get('handled_by', '')} 處理"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**病人**: {r.get('patient_name', '')}")
                st.write(f"**回報日期**: {r.get('date', '')}")
                st.write(f"**警示等級**: {r.get('alert_level', '')}")
                st.write(f"**評分**: {r.get('overall_score', '')}/10")
            
            with col2:
                st.write(f"**處理人**: {r.get('handled_by', '')}")
                st.write(f"**處理時間**: {r.get('handled_time', '')}")
                if r.get("handling_action"):
                    st.write(f"**處理方式**: {r.get('handling_action', '')}")
            
            if r.get("handling_notes"):
                st.write(f"**處理備註**: {r.get('handling_notes', '')}")

# ============================================
# 病人管理（修正版）
# ============================================
def render_patients():
    """病人管理 - 使用新模組"""
    if not GSHEETS_AVAILABLE:
        st.error("無法連線到資料庫")
        return
    
    try:
        if PATIENT_MODULE_AVAILABLE:
            render_patient_management(
                get_all_patients=get_all_patients,
                get_patient_by_id=get_patient_by_id,
                update_patient=update_patient,
                get_patient_reports=get_patient_reports,
                get_interventions=get_interventions,
                get_schedules=get_schedules,
                save_schedule=save_schedule,
                update_schedule=update_schedule,
                get_lab_results=get_lab_results,
                save_lab_result=save_lab_result,
                get_functional_assessments=get_functional_assessments,
                save_functional_assessment=save_functional_assessment,
                username=st.session_state.username
            )
        else:
            render_patients_simple()
    except Exception as e:
        st.error(f"病人管理模組載入失敗: {e}")
        render_patients_simple()

def render_patients_simple():
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
# 衛教管理
# ============================================

# 衛教材料庫
EDUCATION_MATERIALS = {
    "BREATHING": {
        "id": "BREATHING",
        "title": "呼吸運動訓練",
        "category": "呼吸訓練",
        "description": "術後呼吸訓練指導，包含深呼吸、咳嗽技巧、誘發性肺活量計使用",
        "timing": "D+1~D+7"
    },
    "PAIN": {
        "id": "PAIN",
        "title": "疼痛控制指南",
        "category": "疼痛控制",
        "description": "術後疼痛管理，包含藥物使用、非藥物緩解方法",
        "timing": "D+1~D+14"
    },
    "WOUND": {
        "id": "WOUND",
        "title": "傷口照護",
        "category": "傷口照護",
        "description": "傷口清潔、換藥、感染徵兆辨識",
        "timing": "D+3~D+14"
    },
    "HOME": {
        "id": "HOME",
        "title": "居家照護指南",
        "category": "居家照護",
        "description": "出院後居家生活注意事項、活動建議",
        "timing": "出院前"
    },
    "WARNING": {
        "id": "WARNING",
        "title": "警示徵象",
        "category": "警示徵象",
        "description": "需立即就醫的警示徵象：發燒、呼吸困難、傷口異常等",
        "timing": "全程"
    },
    "EXERCISE": {
        "id": "EXERCISE",
        "title": "術後運動建議",
        "category": "復健運動",
        "description": "漸進式活動、肩關節運動、步行訓練",
        "timing": "D+7~D+30"
    },
    "NUTRITION": {
        "id": "NUTRITION",
        "title": "營養補充指南",
        "category": "營養照護",
        "description": "術後飲食建議、蛋白質攝取、維生素補充",
        "timing": "全程"
    },
    "MEDICATION": {
        "id": "MEDICATION",
        "title": "藥物使用指南",
        "category": "藥物衛教",
        "description": "出院藥物使用說明、副作用注意事項",
        "timing": "出院前"
    },
    "FOLLOWUP": {
        "id": "FOLLOWUP",
        "title": "門診追蹤須知",
        "category": "追蹤照護",
        "description": "回診時間、檢查項目、注意事項",
        "timing": "出院前"
    }
}

# 自動推播規則
AUTO_PUSH_RULES = [
    {"day": 1, "materials": ["BREATHING", "PAIN"], "description": "術後第1天：呼吸訓練、疼痛控制"},
    {"day": 3, "materials": ["WOUND"], "description": "術後第3天：傷口照護"},
    {"day": 5, "materials": ["WARNING"], "description": "術後第5天：警示徵象"},
    {"day": 7, "materials": ["EXERCISE", "HOME"], "description": "術後第7天：運動建議、居家照護"},
    {"day": 14, "materials": ["NUTRITION"], "description": "術後第14天：營養指南"},
    {"day": 30, "materials": ["FOLLOWUP"], "description": "術後第30天：門診追蹤"},
]

def render_education():
    """衛教管理"""
    st.title("📚 衛教管理")
    
    if not GSHEETS_AVAILABLE:
        st.error("無法連線到資料庫")
        return
    
    tab1, tab2, tab3, tab4 = st.tabs(["📤 手動推播", "🤖 自動推播規則", "📋 推播紀錄", "📖 衛教材料庫"])
    
    # === 手動推播 ===
    with tab1:
        st.subheader("📤 手動推播衛教")
        
        try:
            patients = get_all_patients()
            
            if patients:
                col1, col2 = st.columns(2)
                
                with col1:
                    # 選擇推播對象
                    push_target = st.radio(
                        "推播對象",
                        ["單一病人", "依術後天數", "依手術類型", "全部病人"],
                        horizontal=True
                    )
                    
                    selected_patients = []
                    
                    if push_target == "單一病人":
                        patient_options = {f"{p.get('name', '未知')} ({p.get('patient_id')}) D+{p.get('post_op_day', 0)}": p for p in patients}
                        selected_label = st.selectbox("選擇病人", list(patient_options.keys()))
                        if selected_label:
                            selected_patients = [patient_options[selected_label]]
                    
                    elif push_target == "依術後天數":
                        col_a, col_b = st.columns(2)
                        with col_a:
                            min_day = st.number_input("最小天數", min_value=0, value=0)
                        with col_b:
                            max_day = st.number_input("最大天數", min_value=0, value=30)
                        selected_patients = [p for p in patients if min_day <= p.get("post_op_day", 0) <= max_day]
                        st.info(f"符合條件：{len(selected_patients)} 人")
                    
                    elif push_target == "依手術類型":
                        surgery_types = list(set([p.get("surgery_type", "未知") for p in patients]))
                        selected_type = st.selectbox("選擇手術類型", surgery_types)
                        selected_patients = [p for p in patients if p.get("surgery_type") == selected_type]
                        st.info(f"符合條件：{len(selected_patients)} 人")
                    
                    else:  # 全部病人
                        selected_patients = patients
                        st.info(f"全部病人：{len(selected_patients)} 人")
                
                with col2:
                    # 選擇衛教材料
                    st.markdown("**選擇衛教材料**")
                    
                    selected_materials = []
                    for mat_id, mat in EDUCATION_MATERIALS.items():
                        if st.checkbox(f"{mat['title']} ({mat['category']})", key=f"mat_{mat_id}"):
                            selected_materials.append(mat)
                
                # 推播按鈕
                st.divider()
                
                if selected_patients and selected_materials:
                    st.success(f"準備推播 **{len(selected_materials)}** 項衛教給 **{len(selected_patients)}** 位病人")
                    
                    if st.button("📤 確認推播", type="primary", use_container_width=True):
                        success_count = 0
                        for patient in selected_patients:
                            for mat in selected_materials:
                                push_data = {
                                    "patient_id": patient.get("patient_id"),
                                    "patient_name": patient.get("name"),
                                    "material_id": mat["id"],
                                    "material_title": mat["title"],
                                    "category": mat["category"],
                                    "push_type": "manual",
                                    "pushed_by": st.session_state.username
                                }
                                result = push_education(push_data)
                                if result:
                                    success_count += 1
                        
                        st.success(f"✅ 成功推播 {success_count} 則衛教！")
                        st.balloons()
                else:
                    st.warning("請選擇推播對象和衛教材料")
            else:
                st.info("尚無病人資料")
                
        except Exception as e:
            st.error(f"載入資料失敗: {e}")
    
    # === 自動推播規則 ===
    with tab2:
        st.subheader("🤖 自動推播規則")
        
        st.info("""
        **自動推播機制說明**：
        系統會根據病人的術後天數，自動推播對應的衛教材料。
        個管師可以在此查看規則，並手動觸發推播。
        """)
        
        for rule in AUTO_PUSH_RULES:
            with st.expander(f"📅 D+{rule['day']}：{rule['description']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write("**推播內容：**")
                    for mat_id in rule["materials"]:
                        mat = EDUCATION_MATERIALS.get(mat_id, {})
                        st.write(f"- {mat.get('title', mat_id)}：{mat.get('description', '')}")
                
                with col2:
                    # 計算符合條件的病人
                    try:
                        patients = get_all_patients()
                        eligible = [p for p in patients if p.get("post_op_day", 0) == rule["day"]]
                        
                        if eligible:
                            st.metric("符合病人", len(eligible))
                            if st.button(f"推播 D+{rule['day']}", key=f"auto_push_{rule['day']}"):
                                success = 0
                                for patient in eligible:
                                    for mat_id in rule["materials"]:
                                        mat = EDUCATION_MATERIALS.get(mat_id, {})
                                        push_data = {
                                            "patient_id": patient.get("patient_id"),
                                            "patient_name": patient.get("name"),
                                            "material_id": mat_id,
                                            "material_title": mat.get("title", ""),
                                            "category": mat.get("category", ""),
                                            "push_type": "rule",
                                            "pushed_by": st.session_state.username
                                        }
                                        if push_education(push_data):
                                            success += 1
                                st.success(f"已推播 {success} 則")
                        else:
                            st.write("目前無符合")
                    except:
                        pass
        
        st.divider()
        
        # 批次執行自動推播
        st.markdown("##### ⚡ 批次執行")
        if st.button("🚀 執行今日所有自動推播", type="primary"):
            try:
                patients = get_all_patients()
                total_pushed = 0
                
                for patient in patients:
                    post_op_day = patient.get("post_op_day", 0)
                    
                    # 檢查是否有對應規則
                    for rule in AUTO_PUSH_RULES:
                        if rule["day"] == post_op_day:
                            for mat_id in rule["materials"]:
                                mat = EDUCATION_MATERIALS.get(mat_id, {})
                                push_data = {
                                    "patient_id": patient.get("patient_id"),
                                    "patient_name": patient.get("name"),
                                    "material_id": mat_id,
                                    "material_title": mat.get("title", ""),
                                    "category": mat.get("category", ""),
                                    "push_type": "auto",
                                    "pushed_by": "system"
                                }
                                if push_education(push_data):
                                    total_pushed += 1
                
                if total_pushed > 0:
                    st.success(f"✅ 完成！共推播 {total_pushed} 則衛教")
                else:
                    st.info("今日沒有需要自動推播的病人")
            except Exception as e:
                st.error(f"執行失敗: {e}")
    
    # === 推播紀錄 ===
    with tab3:
        st.subheader("📋 推播紀錄")
        
        try:
            education = get_education_pushes()
            
            if education:
                # 篩選
                col1, col2 = st.columns(2)
                with col1:
                    filter_status = st.selectbox("狀態", ["全部", "已讀", "未讀"])
                with col2:
                    filter_type = st.selectbox("推播類型", ["全部", "手動", "自動", "規則"])
                
                # 篩選資料
                filtered = education
                if filter_status == "已讀":
                    filtered = [e for e in filtered if e.get("status") == "read"]
                elif filter_status == "未讀":
                    filtered = [e for e in filtered if e.get("status") != "read"]
                
                if filter_type == "手動":
                    filtered = [e for e in filtered if e.get("push_type") == "manual"]
                elif filter_type == "自動":
                    filtered = [e for e in filtered if e.get("push_type") == "auto"]
                elif filter_type == "規則":
                    filtered = [e for e in filtered if e.get("push_type") == "rule"]
                
                st.info(f"共 {len(filtered)} 筆紀錄")
                
                # 顯示紀錄
                for edu in sorted(filtered, key=lambda x: x.get("pushed_at", ""), reverse=True)[:50]:
                    status_icon = "✅" if edu.get("status") == "read" else "📤"
                    push_type_label = {"manual": "手動", "auto": "自動", "rule": "規則"}.get(edu.get("push_type", ""), "")
                    
                    with st.expander(f"{status_icon} {edu.get('patient_name', '')} - {edu.get('material_title', '')} [{push_type_label}]"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**病人**: {edu.get('patient_name', '')}")
                            st.write(f"**衛教**: {edu.get('material_title', '')}")
                            st.write(f"**類別**: {edu.get('category', '')}")
                        with col2:
                            st.write(f"**推播時間**: {edu.get('pushed_at', '')[:19] if edu.get('pushed_at') else ''}")
                            st.write(f"**推播者**: {edu.get('pushed_by', '')}")
                            st.write(f"**狀態**: {'已讀 ✅' if edu.get('status') == 'read' else '未讀'}")
                            if edu.get("read_at"):
                                st.write(f"**閱讀時間**: {edu.get('read_at', '')[:19]}")
            else:
                st.info("尚無推播紀錄")
                
        except Exception as e:
            st.error(f"載入紀錄失敗: {e}")
    
    # === 衛教材料庫 ===
    with tab4:
        st.subheader("📖 衛教材料庫")
        
        for mat_id, mat in EDUCATION_MATERIALS.items():
            with st.expander(f"📄 {mat['title']} - {mat['category']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**說明**: {mat['description']}")
                    st.write(f"**建議時機**: {mat['timing']}")
                with col2:
                    st.write(f"**ID**: {mat['id']}")

# ============================================
# 介入紀錄（完整版）
# ============================================

# 介入類型標準化定義
INTERVENTION_TYPES = {
    "communication": {
        "name": "溝通聯繫",
        "icon": "📞",
        "items": ["電話關懷", "LINE訊息", "視訊諮詢", "面談", "家屬聯繫"]
    },
    "symptom": {
        "name": "症狀處理",
        "icon": "🩺",
        "items": ["疼痛管理", "呼吸指導", "營養諮詢", "睡眠指導", "噁心處理", "傷口評估"]
    },
    "education": {
        "name": "衛教指導",
        "icon": "📚",
        "items": ["藥物衛教", "傷口照護", "活動指導", "自我監測", "飲食指導", "復健運動"]
    },
    "coordination": {
        "name": "照護協調",
        "icon": "🔄",
        "items": ["轉介安排", "回診提醒", "檢查協調", "多團隊溝通", "出院準備", "居家照護"]
    },
    "psychosocial": {
        "name": "心理支持",
        "icon": "💚",
        "items": ["情緒支持", "焦慮處理", "憂鬱評估", "家屬支持", "壓力調適", "靈性關懷"]
    },
    "resource": {
        "name": "資源連結",
        "icon": "🔗",
        "items": ["社工轉介", "居家照護", "長照資源", "經濟補助", "病友團體", "志工服務"]
    }
}

# 問題類別定義
PROBLEM_CATEGORIES = {
    "physical": {"name": "生理問題", "icon": "🩺", "items": ["疼痛", "呼吸困難", "疲勞", "營養不良", "睡眠障礙", "活動受限", "傷口問題"]},
    "psychological": {"name": "心理問題", "icon": "🧠", "items": ["焦慮", "憂鬱", "恐懼", "失眠", "適應障礙", "認知改變"]},
    "social": {"name": "社會問題", "icon": "👥", "items": ["家庭支持不足", "經濟困難", "照顧者負荷", "社交隔離", "工作問題"]},
    "spiritual": {"name": "靈性問題", "icon": "✨", "items": ["生命意義", "宗教需求", "臨終議題"]},
    "self_care": {"name": "自我照顧", "icon": "🏠", "items": ["服藥遵從", "回診遵從", "自我監測", "生活調適"]}
}

def render_interventions():
    """介入紀錄"""
    st.title("📝 介入紀錄")
    
    if not GSHEETS_AVAILABLE:
        st.error("無法連線到資料庫")
        return
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 新增介入", "📋 介入紀錄", "🎯 問題清單", "📊 介入統計"])
    
    # === 新增介入 ===
    with tab1:
        render_new_intervention()
    
    # === 介入紀錄列表 ===
    with tab2:
        render_intervention_list()
    
    # === 問題清單 ===
    with tab3:
        render_problem_list()
    
    # === 介入統計 ===
    with tab4:
        render_intervention_stats()

def render_new_intervention():
    """新增介入紀錄"""
    st.subheader("📝 新增介入紀錄")
    
    try:
        patients = get_all_patients()
        
        if not patients:
            st.warning("尚無病人資料")
            return
        
        with st.form("intervention_form"):
            # === 基本資訊 ===
            st.markdown("##### 📋 基本資訊")
            col1, col2 = st.columns(2)
            
            with col1:
                patient_options = {f"{p.get('name', '未知')} ({p.get('patient_id')}) D+{p.get('post_op_day', 0)}": p for p in patients}
                selected_patient_label = st.selectbox("選擇病人 *", list(patient_options.keys()))
                selected_patient = patient_options.get(selected_patient_label, {})
                
                intervention_date = st.date_input("介入日期", value=datetime.now().date())
            
            with col2:
                method = st.selectbox("聯繫方式 *", ["電話", "LINE", "視訊", "門診", "病房訪視", "其他"])
                duration = st.number_input("介入時長（分鐘）", min_value=1, max_value=180, value=15)
            
            st.divider()
            
            # === 介入類型 ===
            st.markdown("##### 🏷️ 介入類型")
            
            col1, col2 = st.columns(2)
            
            with col1:
                category_options = {f"{v['icon']} {v['name']}": k for k, v in INTERVENTION_TYPES.items()}
                selected_category_label = st.selectbox("介入類別 *", list(category_options.keys()))
                selected_category = category_options[selected_category_label]
            
            with col2:
                category_items = INTERVENTION_TYPES[selected_category]["items"]
                intervention_type = st.selectbox("介入項目 *", category_items)
            
            problem_addressed = st.text_input("處理的問題", placeholder="描述此次介入要處理的問題")
            
            st.divider()
            
            # === 介入內容 ===
            st.markdown("##### 📄 介入內容")
            
            content = st.text_area(
                "介入內容描述 *",
                placeholder="詳細描述介入內容、病人反應、提供的建議等...",
                height=150
            )
            
            # === 成效評估 ===
            st.markdown("##### 📊 成效評估")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pre_score = st.slider("介入前症狀評分", 0, 10, 5, help="0=無症狀, 10=最嚴重")
            
            with col2:
                post_score = st.slider("介入後症狀評分", 0, 10, 3, help="0=無症狀, 10=最嚴重")
            
            with col3:
                outcome = st.selectbox("介入成效", ["改善", "部分改善", "無變化", "惡化", "待評估"])
            
            satisfaction = st.select_slider(
                "病人滿意度",
                options=["非常不滿意", "不滿意", "普通", "滿意", "非常滿意"],
                value="滿意"
            )
            
            st.divider()
            
            # === 轉介與追蹤 ===
            st.markdown("##### 🔄 轉介與追蹤")
            
            col1, col2 = st.columns(2)
            
            with col1:
                referral = st.selectbox("轉介", ["無", "疼痛科", "營養師", "心理師", "社工", "復健科", "安寧團隊", "其他"])
            
            with col2:
                need_follow_up = st.checkbox("需要追蹤")
                follow_up_date = None
                if need_follow_up:
                    follow_up_date = st.date_input("追蹤日期", value=datetime.now().date() + timedelta(days=3))
            
            notes = st.text_area("備註", placeholder="其他補充說明...")
            
            submitted = st.form_submit_button("💾 儲存介入紀錄", type="primary", use_container_width=True)
            
            if submitted:
                if not selected_patient or not content:
                    st.error("請填寫必填欄位（病人、介入內容）")
                else:
                    intervention_data = {
                        "patient_id": selected_patient.get("patient_id"),
                        "patient_name": selected_patient.get("name"),
                        "date": intervention_date.strftime("%Y-%m-%d"),
                        "intervention_type": intervention_type,
                        "intervention_category": INTERVENTION_TYPES[selected_category]["name"],
                        "method": method,
                        "duration": duration,
                        "problem_addressed": problem_addressed,
                        "content": content,
                        "pre_symptom_score": pre_score,
                        "post_symptom_score": post_score,
                        "outcome": outcome,
                        "satisfaction": satisfaction,
                        "referral": referral if referral != "無" else "",
                        "referral_status": "pending" if referral != "無" else "",
                        "follow_up_date": follow_up_date.strftime("%Y-%m-%d") if follow_up_date else "",
                        "created_by": st.session_state.username,
                        "notes": notes
                    }
                    
                    result = save_intervention(intervention_data)
                    
                    if result:
                        st.success(f"✅ 介入紀錄已儲存！（ID: {result}）")
                        st.balloons()
                    else:
                        st.error("儲存失敗，請重試")
                        
    except Exception as e:
        st.error(f"載入資料失敗: {e}")

def render_intervention_list():
    """介入紀錄列表"""
    st.subheader("📋 介入紀錄列表")
    
    try:
        interventions = get_interventions()
        
        if not interventions:
            st.info("尚無介入紀錄")
            return
        
        # 篩選
        col1, col2, col3 = st.columns(3)
        
        with col1:
            patients = get_all_patients()
            patient_filter_options = ["全部"] + [f"{p.get('name')} ({p.get('patient_id')})" for p in patients]
            patient_filter = st.selectbox("篩選病人", patient_filter_options, key="int_patient_filter")
        
        with col2:
            category_filter_options = ["全部"] + [v["name"] for v in INTERVENTION_TYPES.values()]
            category_filter = st.selectbox("篩選類別", category_filter_options)
        
        with col3:
            outcome_filter = st.selectbox("篩選成效", ["全部", "改善", "部分改善", "無變化", "惡化", "待評估"])
        
        # 篩選資料
        filtered = interventions
        
        if patient_filter != "全部":
            pid = patient_filter.split("(")[-1].replace(")", "")
            filtered = [i for i in filtered if i.get("patient_id") == pid]
        
        if category_filter != "全部":
            filtered = [i for i in filtered if i.get("intervention_category") == category_filter]
        
        if outcome_filter != "全部":
            filtered = [i for i in filtered if i.get("outcome") == outcome_filter]
        
        st.info(f"共 {len(filtered)} 筆紀錄")
        
        # 顯示紀錄
        for inv in sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)[:50]:
            outcome = inv.get("outcome", "")
            outcome_icon = {"改善": "✅", "部分改善": "🟡", "無變化": "➖", "惡化": "🔴", "待評估": "⏳"}.get(outcome, "")
            
            with st.expander(f"{outcome_icon} {inv.get('date', '')} | {inv.get('patient_name', '')} | {inv.get('intervention_category', '')} - {inv.get('intervention_type', '')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**病人**: {inv.get('patient_name', '')}")
                    st.write(f"**日期**: {inv.get('date', '')}")
                    st.write(f"**類別**: {inv.get('intervention_category', '')} - {inv.get('intervention_type', '')}")
                    st.write(f"**方式**: {inv.get('method', '')} ({inv.get('duration', '')} 分鐘)")
                    if inv.get("problem_addressed"):
                        st.write(f"**處理問題**: {inv.get('problem_addressed', '')}")
                
                with col2:
                    pre = inv.get("pre_symptom_score", "")
                    post = inv.get("post_symptom_score", "")
                    if pre != "" and post != "":
                        st.write(f"**症狀評分**: {pre} → {post}")
                    st.write(f"**成效**: {outcome_icon} {outcome}")
                    st.write(f"**滿意度**: {inv.get('satisfaction', '')}")
                    if inv.get("referral"):
                        st.write(f"**轉介**: {inv.get('referral', '')}")
                    st.write(f"**記錄者**: {inv.get('created_by', '')}")
                
                st.markdown("**介入內容:**")
                st.write(inv.get("content", ""))
                
                if inv.get("follow_up_date"):
                    st.warning(f"📅 追蹤日期: {inv.get('follow_up_date')}")
                    
    except Exception as e:
        st.error(f"載入紀錄失敗: {e}")

def render_problem_list():
    """問題清單管理"""
    st.subheader("🎯 問題清單")
    
    sub_tab1, sub_tab2 = st.tabs(["📋 問題列表", "➕ 新增問題"])
    
    with sub_tab1:
        try:
            from gsheets_manager import get_problems
            problems = get_problems()
            patients = get_all_patients()
            
            # 篩選
            col1, col2 = st.columns(2)
            with col1:
                patient_filter_options = ["全部"] + [f"{p.get('name')} ({p.get('patient_id')})" for p in patients]
                patient_filter = st.selectbox("篩選病人", patient_filter_options, key="prob_patient_filter")
            with col2:
                status_filter = st.selectbox("篩選狀態", ["全部", "active", "resolved", "monitoring"])
            
            filtered = problems
            if patient_filter != "全部":
                pid = patient_filter.split("(")[-1].replace(")", "")
                filtered = [p for p in filtered if p.get("patient_id") == pid]
            if status_filter != "全部":
                filtered = [p for p in filtered if p.get("status") == status_filter]
            
            # 統計
            active_count = len([p for p in filtered if p.get("status") == "active"])
            resolved_count = len([p for p in filtered if p.get("status") == "resolved"])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🔴 進行中", active_count)
            col2.metric("✅ 已解決", resolved_count)
            col3.metric("📊 總數", len(filtered))
            
            if not filtered:
                st.info("尚無問題紀錄")
            else:
                for prob in filtered:
                    status = prob.get("status", "active")
                    status_icon = {"active": "🔴", "resolved": "✅", "monitoring": "👁️"}.get(status, "")
                    
                    with st.expander(f"{status_icon} {prob.get('patient_name', '')} | {prob.get('problem_description', '')[:30]}..."):
                        st.write(f"**問題類別**: {prob.get('problem_category', '')}")
                        st.write(f"**問題描述**: {prob.get('problem_description', '')}")
                        st.write(f"**嚴重度**: {prob.get('severity', '')}")
                        st.write(f"**目標**: {prob.get('goal', '')}")
                        st.write(f"**狀態**: {status}")
                        
        except Exception as e:
            st.error(f"載入問題清單失敗: {e}")
    
    with sub_tab2:
        st.markdown("##### ➕ 新增問題")
        
        try:
            patients = get_all_patients()
            
            with st.form("problem_form"):
                patient_options = {f"{p.get('name', '未知')} ({p.get('patient_id')})": p for p in patients}
                selected_patient_label = st.selectbox("選擇病人 *", list(patient_options.keys()))
                selected_patient = patient_options.get(selected_patient_label, {})
                
                col1, col2 = st.columns(2)
                with col1:
                    category_options = {f"{v['icon']} {v['name']}": k for k, v in PROBLEM_CATEGORIES.items()}
                    selected_cat_label = st.selectbox("問題類別 *", list(category_options.keys()))
                    selected_cat = category_options[selected_cat_label]
                with col2:
                    problem_items = PROBLEM_CATEGORIES[selected_cat]["items"]
                    problem_item = st.selectbox("問題項目", problem_items)
                    severity = st.selectbox("嚴重度 *", ["高", "中", "低"])
                
                problem_description = st.text_area("問題描述 *", value=problem_item)
                goal = st.text_area("照護目標", placeholder="預期達成的目標...")
                target_date = st.date_input("目標日期", value=datetime.now().date() + timedelta(days=14))
                
                submitted = st.form_submit_button("💾 新增問題", type="primary", use_container_width=True)
                
                if submitted:
                    if not selected_patient or not problem_description:
                        st.error("請填寫必填欄位")
                    else:
                        from gsheets_manager import save_problem
                        problem_data = {
                            "patient_id": selected_patient.get("patient_id"),
                            "patient_name": selected_patient.get("name"),
                            "problem_category": PROBLEM_CATEGORIES[selected_cat]["name"],
                            "problem_description": problem_description,
                            "severity": severity,
                            "goal": goal,
                            "target_date": target_date.strftime("%Y-%m-%d"),
                            "created_by": st.session_state.username
                        }
                        
                        result = save_problem(problem_data)
                        if result:
                            st.success(f"✅ 問題已新增！")
                        else:
                            st.error("新增失敗")
                            
        except Exception as e:
            st.error(f"載入失敗: {e}")

def render_intervention_stats():
    """介入統計分析"""
    st.subheader("📊 介入統計分析")
    
    try:
        interventions = get_interventions()
        
        if not interventions:
            st.info("尚無介入紀錄")
            return
        
        # KPI
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 總介入次數", len(interventions))
        
        with col2:
            improved = len([i for i in interventions if i.get("outcome") in ["改善", "部分改善"]])
            improve_rate = improved / len(interventions) * 100 if interventions else 0
            st.metric("✅ 改善率", f"{improve_rate:.1f}%")
        
        with col3:
            total_duration = sum([int(i.get("duration", 0)) for i in interventions if str(i.get("duration", "0")).isdigit()])
            st.metric("⏱️ 總介入時間", f"{total_duration} 分鐘")
        
        with col4:
            unique_patients = len(set([i.get("patient_id") for i in interventions]))
            st.metric("👥 介入病人數", unique_patients)
        
        st.divider()
        
        # 圖表
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📂 各類別介入次數")
            category_counts = {}
            for inv in interventions:
                cat = inv.get("intervention_category", "未分類")
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            if category_counts:
                import plotly.express as px
                fig = px.pie(values=list(category_counts.values()), names=list(category_counts.keys()), hole=0.4)
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("##### 📈 介入成效分布")
            outcome_counts = {}
            for inv in interventions:
                outcome = inv.get("outcome", "未記錄")
                outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
            
            if outcome_counts:
                import plotly.express as px
                fig = px.bar(x=list(outcome_counts.keys()), y=list(outcome_counts.values()))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        # 個管師工作量
        st.markdown("##### 👩‍⚕️ 個管師工作量")
        
        staff_stats = {}
        for inv in interventions:
            staff = inv.get("created_by", "未知")
            if staff not in staff_stats:
                staff_stats[staff] = {"介入次數": 0, "總時間": 0, "改善": 0}
            staff_stats[staff]["介入次數"] += 1
            staff_stats[staff]["總時間"] += int(inv.get("duration", 0)) if str(inv.get("duration", "0")).isdigit() else 0
            if inv.get("outcome") in ["改善", "部分改善"]:
                staff_stats[staff]["改善"] += 1
        
        staff_df = pd.DataFrame([
            {"個管師": k, "介入次數": v["介入次數"], "總時間(分)": v["總時間"],
             "改善率": f"{v['改善']/v['介入次數']*100:.1f}%" if v["介入次數"] > 0 else "0%"}
            for k, v in staff_stats.items()
        ])
        
        if not staff_df.empty:
            st.dataframe(staff_df, hide_index=True, use_container_width=True)
            
    except Exception as e:
        st.error(f"載入統計失敗: {e}")

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
        elif page == "video":
            render_video()
        elif page == "education":
            render_education()
        elif page == "interventions":
            render_interventions()
        elif page == "reports":
            render_reports()
        else:
            render_dashboard()

def render_video():
    """視訊介入頁面"""
    if not GSHEETS_AVAILABLE:
        st.error("無法連線到資料庫")
        return
    
    try:
        if VIDEO_MODULE_AVAILABLE:
            render_video_consultation(
                get_all_patients=get_all_patients,
                get_schedules=get_schedules,
                save_schedule=save_schedule,
                update_schedule=update_schedule,
                save_intervention=save_intervention,
                username=st.session_state.username
            )
        else:
            st.warning("視訊模組未載入")
            st.info("請確認 video_module.py 已正確部署")
    except Exception as e:
        st.error(f"視訊模組載入失敗: {e}")

if __name__ == "__main__":
    main()
