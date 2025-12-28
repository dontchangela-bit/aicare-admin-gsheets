"""
AI-CARE Lung - 視訊介入模組
============================

功能：
1. 視訊諮詢排程管理
2. 視訊連結產生與發送
3. 視訊紀錄追蹤
4. 視訊統計分析
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import secrets
import string

# ============================================
# 視訊平台設定
# ============================================

VIDEO_PLATFORMS = {
    "google_meet": {
        "name": "Google Meet",
        "icon": "🟢",
        "color": "#00897B",
        "url_prefix": "https://meet.google.com/",
        "instructions": "點擊連結直接加入視訊會議",
        "supports_scheduling": True
    },
    "zoom": {
        "name": "Zoom",
        "icon": "🔵",
        "color": "#2D8CFF",
        "url_prefix": "https://zoom.us/j/",
        "instructions": "點擊連結或輸入會議 ID 加入",
        "supports_scheduling": True
    },
    "line": {
        "name": "LINE 視訊",
        "icon": "💚",
        "color": "#00C300",
        "url_prefix": "",
        "instructions": "個管師將透過 LINE 發起視訊通話",
        "supports_scheduling": False
    },
    "teams": {
        "name": "Microsoft Teams",
        "icon": "🟣",
        "color": "#6264A7",
        "url_prefix": "https://teams.microsoft.com/l/meetup-join/",
        "instructions": "點擊連結加入 Teams 會議",
        "supports_scheduling": True
    },
    "jitsi": {
        "name": "Jitsi Meet (免費)",
        "icon": "🟠",
        "color": "#location",
        "url_prefix": "https://meet.jit.si/",
        "instructions": "點擊連結直接加入，無需帳號",
        "supports_scheduling": True,
        "auto_generate": True
    }
}

# 視訊諮詢類型
VIDEO_CONSULTATION_TYPES = {
    "routine": {"name": "例行追蹤", "duration": 15, "icon": "📅"},
    "symptom": {"name": "症狀評估", "duration": 20, "icon": "🩺"},
    "education": {"name": "衛教指導", "duration": 30, "icon": "📚"},
    "wound": {"name": "傷口檢視", "duration": 15, "icon": "🩹"},
    "medication": {"name": "用藥諮詢", "duration": 20, "icon": "💊"},
    "psycho": {"name": "心理支持", "duration": 30, "icon": "💚"},
    "family": {"name": "家屬會談", "duration": 30, "icon": "👨‍👩‍👧"},
    "emergency": {"name": "緊急諮詢", "duration": 15, "icon": "🚨"}
}


# ============================================
# 主要渲染函數
# ============================================

def render_video_consultation(get_all_patients, get_schedules, save_schedule, 
                               update_schedule, save_intervention, username):
    """視訊介入管理頁面"""
    
    st.title("📹 視訊介入管理")
    
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
    <b>📹 視訊諮詢功能</b><br>
    提供遠端視訊追蹤服務，讓病人在家也能接受專業照護指導。
    </div>
    """, unsafe_allow_html=True)
    
    # 4 個標籤頁
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 排程視訊", 
        "🎥 進行中/待開始",
        "📋 視訊紀錄",
        "📊 視訊統計"
    ])
    
    # === 排程視訊 ===
    with tab1:
        render_schedule_video(get_all_patients, save_schedule, username)
    
    # === 進行中/待開始 ===
    with tab2:
        render_upcoming_videos(get_all_patients, get_schedules, update_schedule, save_intervention, username)
    
    # === 視訊紀錄 ===
    with tab3:
        render_video_history(get_schedules)
    
    # === 視訊統計 ===
    with tab4:
        render_video_statistics(get_schedules)


# ============================================
# 排程視訊
# ============================================

def render_schedule_video(get_all_patients, save_schedule, username):
    """排程新視訊"""
    st.subheader("📅 排程視訊諮詢")
    
    try:
        patients = get_all_patients()
        
        if not patients:
            st.warning("尚無病人資料")
            return
        
        with st.form("video_schedule_form"):
            # === 基本資訊 ===
            st.markdown("##### 👤 病人資訊")
            col1, col2 = st.columns(2)
            
            with col1:
                patient_options = {
                    f"{p.get('name', '')} ({p.get('patient_id', '')}) D+{p.get('post_op_day', 0)}": p 
                    for p in patients
                }
                selected_label = st.selectbox("選擇病人 *", list(patient_options.keys()))
                patient = patient_options.get(selected_label, {})
            
            with col2:
                consultation_type = st.selectbox(
                    "諮詢類型 *",
                    list(VIDEO_CONSULTATION_TYPES.keys()),
                    format_func=lambda x: f"{VIDEO_CONSULTATION_TYPES[x]['icon']} {VIDEO_CONSULTATION_TYPES[x]['name']}"
                )
            
            st.markdown("##### 📅 時間設定")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                scheduled_date = st.date_input(
                    "視訊日期 *",
                    value=datetime.now().date() + timedelta(days=1),
                    min_value=datetime.now().date()
                )
            
            with col2:
                scheduled_time = st.time_input(
                    "視訊時間 *",
                    value=datetime.strptime("10:00", "%H:%M").time()
                )
            
            with col3:
                duration = st.number_input(
                    "預計時長（分鐘）",
                    min_value=5,
                    max_value=60,
                    value=VIDEO_CONSULTATION_TYPES[consultation_type]["duration"]
                )
            
            st.markdown("##### 🎥 視訊設定")
            col1, col2 = st.columns(2)
            
            with col1:
                platform = st.selectbox(
                    "視訊平台 *",
                    list(VIDEO_PLATFORMS.keys()),
                    format_func=lambda x: f"{VIDEO_PLATFORMS[x]['icon']} {VIDEO_PLATFORMS[x]['name']}"
                )
            
            with col2:
                # 根據平台決定是否自動產生連結
                if VIDEO_PLATFORMS[platform].get("auto_generate"):
                    st.info("✅ 系統將自動產生視訊連結")
                    video_link = ""
                else:
                    video_link = st.text_input(
                        "視訊連結",
                        placeholder=f"貼上 {VIDEO_PLATFORMS[platform]['name']} 連結"
                    )
            
            st.markdown("##### 📝 備註")
            purpose = st.text_area(
                "諮詢目的/議題",
                placeholder="描述本次視訊的主要目的或要討論的議題..."
            )
            
            # 提醒設定
            col1, col2 = st.columns(2)
            with col1:
                send_reminder = st.checkbox("發送提醒給病人", value=True)
            with col2:
                reminder_time = st.selectbox(
                    "提前多久提醒",
                    ["30 分鐘前", "1 小時前", "2 小時前", "1 天前"],
                    index=1
                )
            
            # 提交
            submitted = st.form_submit_button("📅 建立視訊排程", type="primary", use_container_width=True)
            
            if submitted:
                if not patient:
                    st.error("請選擇病人")
                else:
                    # 自動產生 Jitsi 連結
                    if VIDEO_PLATFORMS[platform].get("auto_generate"):
                        room_id = generate_room_id(patient.get("patient_id"), scheduled_date)
                        video_link = f"{VIDEO_PLATFORMS[platform]['url_prefix']}AICARE-{room_id}"
                    
                    schedule_data = {
                        "patient_id": patient.get("patient_id"),
                        "patient_name": patient.get("name"),
                        "schedule_type": f"📹 視訊諮詢 - {VIDEO_CONSULTATION_TYPES[consultation_type]['name']}",
                        "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
                        "scheduled_time": scheduled_time.strftime("%H:%M"),
                        "location": f"{VIDEO_PLATFORMS[platform]['name']}",
                        "provider": username,
                        "notes": json.dumps({
                            "consultation_type": consultation_type,
                            "platform": platform,
                            "video_link": video_link,
                            "duration": duration,
                            "purpose": purpose,
                            "send_reminder": send_reminder,
                            "reminder_time": reminder_time
                        }, ensure_ascii=False),
                        "created_by": username
                    }
                    
                    result = save_schedule(schedule_data)
                    
                    if result:
                        st.success("✅ 視訊諮詢已排程！")
                        
                        # 顯示視訊連結
                        if video_link:
                            st.markdown(f"""
                            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; margin-top: 15px;">
                            <h4>🎥 視訊連結</h4>
                            <p><a href="{video_link}" target="_blank">{video_link}</a></p>
                            <p><small>{VIDEO_PLATFORMS[platform]['instructions']}</small></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 複製連結按鈕
                            st.code(video_link)
                            st.caption("👆 點擊上方連結複製")
                        
                        st.balloons()
                    else:
                        st.error("排程失敗，請重試")
                        
    except Exception as e:
        st.error(f"載入失敗: {e}")


# ============================================
# 進行中/待開始視訊
# ============================================

def render_upcoming_videos(get_all_patients, get_schedules, update_schedule, save_intervention, username):
    """待開始/進行中視訊"""
    st.subheader("🎥 待開始/進行中視訊")
    
    try:
        schedules = get_schedules()
        patients = get_all_patients()
        
        # 篩選視訊排程
        video_schedules = [s for s in schedules if "視訊" in s.get("schedule_type", "")]
        
        # 分類
        today = datetime.now().date()
        now = datetime.now()
        
        today_videos = []
        upcoming_videos = []
        
        for s in video_schedules:
            if s.get("status") == "completed":
                continue
            
            try:
                sched_date = datetime.strptime(s.get("scheduled_date", ""), "%Y-%m-%d").date()
                sched_time = datetime.strptime(s.get("scheduled_time", "00:00"), "%H:%M").time()
                sched_datetime = datetime.combine(sched_date, sched_time)
                
                if sched_date == today:
                    today_videos.append((s, sched_datetime))
                elif sched_date > today:
                    upcoming_videos.append((s, sched_datetime))
            except:
                pass
        
        # === 今日視訊 ===
        st.markdown("##### 📅 今日視訊")
        
        if today_videos:
            for s, sched_datetime in sorted(today_videos, key=lambda x: x[1]):
                render_video_card(s, sched_datetime, patients, update_schedule, save_intervention, username, is_today=True)
        else:
            st.info("今日無視訊排程")
        
        # === 即將到來 ===
        st.markdown("---")
        st.markdown("##### 📆 即將到來")
        
        if upcoming_videos:
            for s, sched_datetime in sorted(upcoming_videos, key=lambda x: x[1])[:10]:
                render_video_card(s, sched_datetime, patients, update_schedule, save_intervention, username, is_today=False)
        else:
            st.info("無即將到來的視訊排程")
            
    except Exception as e:
        st.error(f"載入失敗: {e}")


def render_video_card(schedule, sched_datetime, patients, update_schedule, save_intervention, username, is_today=False):
    """渲染視訊卡片"""
    
    # 解析 notes
    try:
        notes = json.loads(schedule.get("notes", "{}"))
    except:
        notes = {}
    
    platform = notes.get("platform", "")
    video_link = notes.get("video_link", "")
    consultation_type = notes.get("consultation_type", "")
    duration = notes.get("duration", 15)
    purpose = notes.get("purpose", "")
    
    # 找病人資料
    patient = next((p for p in patients if p.get("patient_id") == schedule.get("patient_id")), {})
    
    # 計算時間差
    now = datetime.now()
    time_diff = sched_datetime - now
    
    if time_diff.total_seconds() < 0:
        time_status = "🔴 已超過預定時間"
        card_color = "#ffebee"
    elif time_diff.total_seconds() < 900:  # 15 分鐘內
        time_status = "🟢 即將開始"
        card_color = "#e8f5e9"
    elif time_diff.total_seconds() < 3600:  # 1 小時內
        time_status = f"🟡 {int(time_diff.total_seconds() / 60)} 分鐘後"
        card_color = "#fffde7"
    else:
        time_status = f"⏰ {sched_datetime.strftime('%m/%d %H:%M')}"
        card_color = "#f5f5f5"
    
    platform_info = VIDEO_PLATFORMS.get(platform, {})
    
    with st.expander(f"{platform_info.get('icon', '🎥')} {schedule.get('patient_name', '')} - {sched_datetime.strftime('%H:%M')} {time_status}", expanded=is_today):
        
        st.markdown(f"""
        <div style="background-color: {card_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**病人**: {schedule.get('patient_name', '')} (D+{patient.get('post_op_day', 0)})")
            st.write(f"**電話**: {patient.get('phone', '')}")
            st.write(f"**類型**: {VIDEO_CONSULTATION_TYPES.get(consultation_type, {}).get('name', consultation_type)}")
            st.write(f"**時長**: {duration} 分鐘")
        
        with col2:
            st.write(f"**日期**: {schedule.get('scheduled_date', '')}")
            st.write(f"**時間**: {schedule.get('scheduled_time', '')}")
            st.write(f"**平台**: {platform_info.get('name', platform)}")
            st.write(f"**負責人**: {schedule.get('provider', '')}")
        
        if purpose:
            st.write(f"**諮詢目的**: {purpose}")
        
        # 視訊連結
        if video_link:
            st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0;">
            <b>🔗 視訊連結</b><br>
            <a href="{video_link}" target="_blank">{video_link}</a>
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if st.button("🎥 開始視訊", key=f"start_{schedule.get('schedule_id')}", type="primary"):
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={video_link}">', unsafe_allow_html=True)
                    st.info(f"正在開啟視訊連結...")
            
            with col_b:
                if st.button("📋 複製連結", key=f"copy_{schedule.get('schedule_id')}"):
                    st.code(video_link)
        
        # 完成視訊
        st.markdown("---")
        
        with st.form(key=f"complete_video_{schedule.get('schedule_id')}"):
            st.markdown("**📝 完成視訊紀錄**")
            
            col1, col2 = st.columns(2)
            with col1:
                actual_duration = st.number_input("實際時長（分鐘）", min_value=1, max_value=120, value=duration)
                outcome = st.selectbox("視訊結果", ["順利完成", "病人未接聽", "技術問題中斷", "病人取消", "改期"])
            
            with col2:
                patient_condition = st.selectbox("病人狀況評估", ["穩定良好", "需要關注", "需要介入", "建議回診"])
                follow_up = st.selectbox("後續追蹤", ["無需追蹤", "電話追蹤", "下次視訊", "安排回診"])
            
            video_notes = st.text_area("視訊紀錄", placeholder="記錄視訊內容、病人狀況、討論事項...")
            
            create_intervention = st.checkbox("同時建立介入紀錄", value=True)
            
            submitted = st.form_submit_button("✅ 完成視訊", use_container_width=True)
            
            if submitted:
                # 更新排程狀態
                update_schedule(schedule.get("schedule_id"), {
                    "status": "completed",
                    "result": f"{outcome} | {actual_duration}分鐘 | {patient_condition}"
                })
                
                # 建立介入紀錄
                if create_intervention:
                    intervention_data = {
                        "patient_id": schedule.get("patient_id"),
                        "patient_name": schedule.get("patient_name"),
                        "intervention_type": "視訊諮詢",
                        "intervention_category": "溝通聯繫",
                        "method": "視訊",
                        "duration": actual_duration,
                        "problem_addressed": purpose,
                        "content": f"視訊平台: {platform_info.get('name', platform)}\n結果: {outcome}\n病人狀況: {patient_condition}\n後續追蹤: {follow_up}\n\n紀錄:\n{video_notes}",
                        "outcome": "待評估" if patient_condition == "需要介入" else "改善",
                        "follow_up_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d") if follow_up != "無需追蹤" else "",
                        "created_by": username
                    }
                    save_intervention(intervention_data)
                
                st.success("✅ 視訊紀錄已儲存！")
                st.rerun()


# ============================================
# 視訊紀錄
# ============================================

def render_video_history(get_schedules):
    """視訊紀錄"""
    st.subheader("📋 視訊紀錄")
    
    try:
        schedules = get_schedules()
        
        # 篩選已完成的視訊
        video_completed = [s for s in schedules 
                         if "視訊" in s.get("schedule_type", "") 
                         and s.get("status") == "completed"]
        
        if not video_completed:
            st.info("尚無視訊紀錄")
            return
        
        # 篩選
        col1, col2 = st.columns(2)
        with col1:
            date_filter = st.selectbox("時間範圍", ["全部", "最近 7 天", "最近 30 天", "最近 90 天"])
        with col2:
            outcome_filter = st.selectbox("結果", ["全部", "順利完成", "病人未接聽", "技術問題", "取消/改期"])
        
        # 篩選資料
        filtered = video_completed
        
        today = datetime.now().date()
        if date_filter == "最近 7 天":
            start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            filtered = [s for s in filtered if s.get("scheduled_date", "") >= start]
        elif date_filter == "最近 30 天":
            start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            filtered = [s for s in filtered if s.get("scheduled_date", "") >= start]
        elif date_filter == "最近 90 天":
            start = (today - timedelta(days=90)).strftime("%Y-%m-%d")
            filtered = [s for s in filtered if s.get("scheduled_date", "") >= start]
        
        if outcome_filter != "全部":
            filtered = [s for s in filtered if outcome_filter in s.get("result", "")]
        
        st.info(f"共 {len(filtered)} 筆視訊紀錄")
        
        for s in sorted(filtered, key=lambda x: x.get("scheduled_date", ""), reverse=True)[:50]:
            result = s.get("result", "")
            result_icon = "✅" if "順利" in result else "❌" if "未接聽" in result or "取消" in result else "⚠️"
            
            with st.expander(f"{result_icon} {s.get('scheduled_date', '')} | {s.get('patient_name', '')} | {result[:20]}..."):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**病人**: {s.get('patient_name', '')}")
                    st.write(f"**日期**: {s.get('scheduled_date', '')} {s.get('scheduled_time', '')}")
                    st.write(f"**類型**: {s.get('schedule_type', '')}")
                with col2:
                    st.write(f"**平台**: {s.get('location', '')}")
                    st.write(f"**結果**: {result}")
                    st.write(f"**負責人**: {s.get('provider', '')}")
                    
    except Exception as e:
        st.error(f"載入失敗: {e}")


# ============================================
# 視訊統計
# ============================================

def render_video_statistics(get_schedules):
    """視訊統計"""
    st.subheader("📊 視訊統計分析")
    
    try:
        schedules = get_schedules()
        
        # 篩選視訊排程
        video_schedules = [s for s in schedules if "視訊" in s.get("schedule_type", "")]
        
        if not video_schedules:
            st.info("尚無視訊資料")
            return
        
        # 統計
        total = len(video_schedules)
        completed = len([s for s in video_schedules if s.get("status") == "completed"])
        successful = len([s for s in video_schedules if "順利" in s.get("result", "")])
        
        # KPI
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📹 總視訊數", total)
        col2.metric("✅ 已完成", completed)
        col3.metric("🎯 成功率", f"{successful/completed*100:.1f}%" if completed else "0%")
        col4.metric("⏳ 待進行", total - completed)
        
        st.divider()
        
        # 圖表
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📅 每月視訊趨勢")
            
            monthly_stats = {}
            for s in video_schedules:
                month = s.get("scheduled_date", "")[:7]
                if month:
                    monthly_stats[month] = monthly_stats.get(month, 0) + 1
            
            if monthly_stats:
                import plotly.express as px
                df = pd.DataFrame([
                    {"月份": k, "視訊數": v}
                    for k, v in sorted(monthly_stats.items())
                ])
                fig = px.bar(df, x="月份", y="視訊數")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("##### 📊 視訊結果分布")
            
            result_stats = {"順利完成": 0, "未接聽": 0, "技術問題": 0, "取消/改期": 0, "其他": 0}
            for s in video_schedules:
                result = s.get("result", "")
                if "順利" in result:
                    result_stats["順利完成"] += 1
                elif "未接聽" in result:
                    result_stats["未接聽"] += 1
                elif "技術" in result:
                    result_stats["技術問題"] += 1
                elif "取消" in result or "改期" in result:
                    result_stats["取消/改期"] += 1
                elif result:
                    result_stats["其他"] += 1
            
            if any(result_stats.values()):
                import plotly.express as px
                fig = px.pie(
                    values=[v for v in result_stats.values() if v > 0],
                    names=[k for k, v in result_stats.items() if v > 0],
                    hole=0.4
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"載入統計失敗: {e}")


# ============================================
# 輔助函數
# ============================================

def generate_room_id(patient_id, date):
    """產生視訊房間 ID"""
    random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    return f"{patient_id}-{date.strftime('%m%d')}-{random_suffix}"
