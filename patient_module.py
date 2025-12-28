"""
AI-CARE Lung - 病人管理模組（完整版）
=====================================

功能：
1. 病人資料管理（強化版）
2. 追蹤排程管理
3. 檢查結果追蹤
4. 功能狀態評估
5. 治療摘要
6. 風險分層
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# ============================================
# 常數定義
# ============================================

# TNM 分期選項
CLINICAL_STAGES = ["I", "IA1", "IA2", "IA3", "IB", "II", "IIA", "IIB", "III", "IIIA", "IIIB", "IIIC", "IV", "IVA", "IVB"]

# 手術類型
SURGERY_TYPES = {
    "lobectomy": "肺葉切除 (Lobectomy)",
    "wedge": "楔狀切除 (Wedge resection)",
    "segmentectomy": "肺節切除 (Segmentectomy)",
    "pneumonectomy": "全肺切除 (Pneumonectomy)",
    "sleeve": "袖狀切除 (Sleeve resection)",
    "bilobectomy": "雙肺葉切除 (Bilobectomy)"
}

# 手術方式
SURGERY_APPROACHES = {
    "vats": "胸腔鏡手術 (VATS)",
    "rats": "機器人手術 (RATS)",
    "open": "傳統開胸手術",
    "converted": "中轉開胸"
}

# 組織學類型
HISTOLOGY_TYPES = {
    "adenocarcinoma": "腺癌 (Adenocarcinoma)",
    "squamous": "鱗狀細胞癌 (Squamous cell carcinoma)",
    "large_cell": "大細胞癌 (Large cell carcinoma)",
    "small_cell": "小細胞癌 (Small cell carcinoma)",
    "carcinoid": "類癌 (Carcinoid)",
    "other": "其他"
}

# 腫瘤位置
TUMOR_LOCATIONS = {
    "rul": "右上葉 (RUL)",
    "rml": "右中葉 (RML)",
    "rll": "右下葉 (RLL)",
    "lul": "左上葉 (LUL)",
    "lll": "左下葉 (LLL)",
    "multiple": "多處"
}

# 共病症
COMORBIDITIES = [
    "高血壓", "糖尿病", "冠心病", "心律不整", "心衰竭",
    "COPD", "氣喘", "肺纖維化", "肺結核病史",
    "腎功能不全", "肝功能異常", "腦中風病史",
    "其他惡性腫瘤病史", "免疫疾病"
]

# ECOG Performance Status
ECOG_PS = {
    0: "完全正常活動，無任何限制",
    1: "輕度受限，可自由走動及從事輕度體力活動",
    2: "可自由走動及自我照顧，但無法從事任何工作活動",
    3: "僅能有限度自我照顧，臥床或坐輪椅超過50%清醒時間",
    4: "完全無法自我照顧，完全臥床"
}

# 追蹤排程類型
SCHEDULE_TYPES = {
    "opd": "門診回診",
    "ct": "胸部 CT",
    "xray": "胸部 X 光",
    "pet": "PET-CT",
    "blood": "抽血檢查",
    "pulmonary": "肺功能檢查",
    "video_call": "📹 視訊諮詢",
    "phone_call": "📞 電話追蹤",
    "other": "其他"
}

# 視訊平台設定
VIDEO_PLATFORMS = {
    "google_meet": {
        "name": "Google Meet",
        "icon": "🟢",
        "url_pattern": "https://meet.google.com/",
        "instructions": "點擊連結直接加入視訊會議"
    },
    "zoom": {
        "name": "Zoom",
        "icon": "🔵",
        "url_pattern": "https://zoom.us/j/",
        "instructions": "點擊連結或輸入會議 ID 加入"
    },
    "line": {
        "name": "LINE 視訊",
        "icon": "🟢",
        "url_pattern": "",
        "instructions": "個管師將透過 LINE 發起視訊通話"
    },
    "teams": {
        "name": "Microsoft Teams",
        "icon": "🟣",
        "url_pattern": "https://teams.microsoft.com/",
        "instructions": "點擊連結加入 Teams 會議"
    }
}

# 風險等級定義
RISK_LEVELS = {
    "high": {
        "name": "高風險",
        "color": "🔴",
        "criteria": "Stage IIIA 以上、淋巴結轉移、切緣陽性",
        "follow_up": "每 3 個月追蹤"
    },
    "medium": {
        "name": "中風險",
        "color": "🟡",
        "criteria": "Stage IB-II、腫瘤 > 4cm",
        "follow_up": "每 4-6 個月追蹤"
    },
    "low": {
        "name": "低風險",
        "color": "🟢",
        "criteria": "Stage IA、腫瘤 ≤ 2cm、無淋巴結轉移",
        "follow_up": "每 6-12 個月追蹤"
    }
}


# ============================================
# 主要渲染函數
# ============================================

def render_patient_management(get_all_patients, get_patient_by_id, update_patient,
                               get_patient_reports, get_interventions,
                               get_schedules, save_schedule, update_schedule,
                               get_lab_results, save_lab_result,
                               get_functional_assessments, save_functional_assessment,
                               username):
    """病人管理主頁面"""
    
    st.title("👥 病人管理")
    
    # 7 個標籤頁
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📋 病人總覽", 
        "👤 詳細資料",
        "📅 追蹤排程",
        "🔬 檢查結果",
        "📊 功能評估",
        "📄 治療摘要",
        "📈 追蹤歷程"
    ])
    
    # === 病人總覽 ===
    with tab1:
        render_patient_overview(get_all_patients)
    
    # === 詳細資料 ===
    with tab2:
        render_patient_detail(get_all_patients, update_patient, username)
    
    # === 追蹤排程 ===
    with tab3:
        render_schedule_management(get_all_patients, get_schedules, save_schedule, update_schedule, username)
    
    # === 檢查結果 ===
    with tab4:
        render_lab_management(get_all_patients, get_lab_results, save_lab_result, username)
    
    # === 功能評估 ===
    with tab5:
        render_functional_assessment(get_all_patients, get_functional_assessments, save_functional_assessment, username)
    
    # === 治療摘要 ===
    with tab6:
        render_treatment_summary(get_all_patients, get_patient_reports, get_interventions)
    
    # === 追蹤歷程 ===
    with tab7:
        render_patient_history(get_all_patients, get_patient_reports, get_interventions)


# ============================================
# 病人總覽
# ============================================

def render_patient_overview(get_all_patients):
    """病人總覽"""
    st.subheader("📋 病人總覽")
    
    try:
        patients = get_all_patients()
        
        if not patients:
            st.info("尚無病人資料")
            return
        
        # === KPI 指標 ===
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total = len(patients)
        hospitalized = len([p for p in patients if p.get("status") == "hospitalized"])
        active = len([p for p in patients if p.get("status") in ["normal", "active"]])
        pending = len([p for p in patients if p.get("status") == "pending_setup"])
        high_risk = len([p for p in patients if p.get("risk_level") == "high"])
        
        col1.metric("📊 總收案數", total)
        col2.metric("🏥 住院中", hospitalized)
        col3.metric("🟢 追蹤中", active)
        col4.metric("⏳ 待設定", pending)
        col5.metric("🔴 高風險", high_risk)
        
        st.divider()
        
        # === 篩選 ===
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            search = st.text_input("🔍 搜尋", placeholder="姓名/病歷號/ID")
        with col2:
            status_filter = st.selectbox("狀態", ["全部", "住院中", "追蹤中", "待設定", "已結案"])
        with col3:
            risk_filter = st.selectbox("風險等級", ["全部", "高風險", "中風險", "低風險"])
        with col4:
            stage_filter = st.selectbox("術後階段", ["全部", "急性期(D0-7)", "恢復期(D8-30)", "穩定期(D31-90)", "長期追蹤(D90+)"])
        
        # 篩選資料
        filtered = patients
        
        if search:
            filtered = [p for p in filtered if 
                       search.lower() in str(p.get("name", "")).lower() or
                       search in str(p.get("patient_id", "")) or
                       search in str(p.get("medical_record", ""))]
        
        if status_filter != "全部":
            status_map = {"住院中": "hospitalized", "追蹤中": ["normal", "active"], "待設定": "pending_setup", "已結案": "completed"}
            target = status_map.get(status_filter)
            if isinstance(target, list):
                filtered = [p for p in filtered if p.get("status") in target]
            else:
                filtered = [p for p in filtered if p.get("status") == target]
        
        if risk_filter != "全部":
            risk_map = {"高風險": "high", "中風險": "medium", "低風險": "low"}
            filtered = [p for p in filtered if p.get("risk_level") == risk_map.get(risk_filter)]
        
        if stage_filter != "全部":
            def get_stage(post_op_day):
                if post_op_day <= 7: return "急性期(D0-7)"
                elif post_op_day <= 30: return "恢復期(D8-30)"
                elif post_op_day <= 90: return "穩定期(D31-90)"
                else: return "長期追蹤(D90+)"
            filtered = [p for p in filtered if get_stage(p.get("post_op_day", 0)) == stage_filter]
        
        st.info(f"顯示 {len(filtered)} / {total} 位病人")
        
        # === 病人卡片 ===
        for patient in filtered:
            render_patient_card(patient)
            
    except Exception as e:
        st.error(f"載入失敗: {e}")


def render_patient_card(patient):
    """病人卡片"""
    status = patient.get("status", "")
    status_icons = {
        "hospitalized": "🏥",
        "normal": "🟢",
        "active": "🟢",
        "pending_setup": "⏳",
        "completed": "✅"
    }
    status_icon = status_icons.get(status, "⚪")
    
    risk = patient.get("risk_level", "")
    risk_icon = RISK_LEVELS.get(risk, {}).get("color", "")
    
    post_op = patient.get("post_op_day", 0)
    
    with st.expander(f"{status_icon} {patient.get('name', '未知')} ({patient.get('patient_id', '')}) - D+{post_op} {risk_icon}"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**基本資料**")
            st.write(f"姓名: {patient.get('name', '')}")
            st.write(f"年齡: {patient.get('age', '')} 歲")
            st.write(f"電話: {patient.get('phone', '')}")
        
        with col2:
            st.write("**疾病資訊**")
            st.write(f"診斷: {patient.get('diagnosis', '')}")
            st.write(f"分期: {patient.get('pathological_stage', patient.get('clinical_stage', ''))}")
            st.write(f"組織: {patient.get('histology_type', '')}")
        
        with col3:
            st.write("**手術資訊**")
            st.write(f"日期: {patient.get('surgery_date', '')}")
            st.write(f"方式: {patient.get('surgery_type', '')}")
            st.write(f"術後: D+{post_op}")


# ============================================
# 病人詳細資料
# ============================================

def render_patient_detail(get_all_patients, update_patient, username):
    """病人詳細資料編輯"""
    st.subheader("👤 病人詳細資料")
    
    try:
        patients = get_all_patients()
        
        if not patients:
            st.info("尚無病人資料")
            return
        
        # 選擇病人
        patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p for p in patients}
        selected_label = st.selectbox("選擇病人", list(patient_options.keys()), key="detail_patient")
        
        if not selected_label:
            return
        
        patient = patient_options[selected_label]
        patient_id = patient.get("patient_id")
        
        with st.form("patient_detail_form"):
            # === 基本資料 ===
            st.markdown("##### 📋 基本資料")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name = st.text_input("姓名", value=patient.get("name", ""), disabled=True)
                phone = st.text_input("電話", value=str(patient.get("phone", "")), disabled=True)
                id_number = st.text_input("身分證字號", value=patient.get("id_number", ""))
            
            with col2:
                age = st.number_input("年齡", value=int(patient.get("age", 0)) if patient.get("age") else 0)
                gender = st.selectbox("性別", ["男", "女"], index=0 if patient.get("gender") == "男" else 1)
                birth_date = st.text_input("生日", value=patient.get("birth_date", ""))
            
            with col3:
                emergency_contact = st.text_input("緊急聯絡人", value=patient.get("emergency_contact", ""))
                emergency_phone = st.text_input("緊急聯絡電話", value=patient.get("emergency_phone", ""))
                medical_record = st.text_input("病歷號", value=patient.get("medical_record", ""))
            
            st.divider()
            
            # === 診斷資訊 ===
            st.markdown("##### 🔬 診斷資訊")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                diagnosis = st.text_input("診斷", value=patient.get("diagnosis", ""), placeholder="如: Lung adenocarcinoma")
                
                histology_options = list(HISTOLOGY_TYPES.values())
                current_histology = patient.get("histology_type", "")
                histology_index = histology_options.index(current_histology) if current_histology in histology_options else 0
                histology_type = st.selectbox("組織學類型", histology_options, index=histology_index)
            
            with col2:
                clinical_stage = st.selectbox("臨床分期 (cTNM)", CLINICAL_STAGES, 
                    index=CLINICAL_STAGES.index(patient.get("clinical_stage")) if patient.get("clinical_stage") in CLINICAL_STAGES else 0)
                pathological_stage = st.selectbox("病理分期 (pTNM)", CLINICAL_STAGES,
                    index=CLINICAL_STAGES.index(patient.get("pathological_stage")) if patient.get("pathological_stage") in CLINICAL_STAGES else 0)
            
            with col3:
                location_options = list(TUMOR_LOCATIONS.values())
                current_location = patient.get("tumor_location", "")
                location_index = location_options.index(current_location) if current_location in location_options else 0
                tumor_location = st.selectbox("腫瘤位置", location_options, index=location_index)
                
                tumor_size = st.text_input("腫瘤大小", value=patient.get("tumor_size", ""), placeholder="如: 2.5 cm")
            
            st.divider()
            
            # === 手術資訊 ===
            st.markdown("##### 🏥 手術資訊")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # 手術日期
                current_date = patient.get("surgery_date", "")
                if current_date:
                    try:
                        default_date = datetime.strptime(str(current_date), "%Y-%m-%d").date()
                    except:
                        default_date = datetime.now().date()
                else:
                    default_date = datetime.now().date()
                surgery_date = st.date_input("手術日期", value=default_date)
                
                surgery_options = list(SURGERY_TYPES.values())
                current_surgery = patient.get("surgery_type", "")
                surgery_index = surgery_options.index(current_surgery) if current_surgery in surgery_options else 0
                surgery_type = st.selectbox("手術類型", surgery_options, index=surgery_index)
            
            with col2:
                approach_options = list(SURGERY_APPROACHES.values())
                current_approach = patient.get("surgery_approach", "")
                approach_index = approach_options.index(current_approach) if current_approach in approach_options else 0
                surgery_approach = st.selectbox("手術方式", approach_options, index=approach_index)
                
                resection_extent = st.text_input("切除範圍", value=patient.get("resection_extent", ""))
            
            with col3:
                lymph_node = st.text_input("淋巴結清除", value=patient.get("lymph_node_dissection", ""), placeholder="如: 2L, 4L, 7")
                surgical_margin = st.selectbox("切緣狀態", ["R0 (陰性)", "R1 (鏡下陽性)", "R2 (肉眼陽性)"],
                    index=["R0 (陰性)", "R1 (鏡下陽性)", "R2 (肉眼陽性)"].index(patient.get("surgical_margin", "R0 (陰性)")) if patient.get("surgical_margin") in ["R0 (陰性)", "R1 (鏡下陽性)", "R2 (肉眼陽性)"] else 0)
            
            complications = st.text_area("手術併發症", value=patient.get("complications", ""), placeholder="如有併發症請填寫")
            
            st.divider()
            
            # === 輔助治療 ===
            st.markdown("##### 💊 輔助治療")
            col1, col2 = st.columns(2)
            
            with col1:
                adjuvant_chemo = st.text_input("輔助化療", value=patient.get("adjuvant_chemo", ""), placeholder="如: Cisplatin + Vinorelbine x 4 cycles")
                adjuvant_radio = st.text_input("輔助放療", value=patient.get("adjuvant_radio", ""), placeholder="如: 60Gy/30fx")
            
            with col2:
                target_therapy = st.text_input("標靶治療", value=patient.get("target_therapy", ""), placeholder="如: Osimertinib (EGFR L858R)")
                immunotherapy = st.text_input("免疫治療", value=patient.get("immunotherapy", ""), placeholder="如: Pembrolizumab")
            
            st.divider()
            
            # === 共病症與風險 ===
            st.markdown("##### ⚠️ 共病症與風險評估")
            col1, col2 = st.columns(2)
            
            with col1:
                current_comorbidities = patient.get("comorbidities", "").split(",") if patient.get("comorbidities") else []
                comorbidities = st.multiselect("共病症", COMORBIDITIES, default=[c.strip() for c in current_comorbidities if c.strip() in COMORBIDITIES])
                
                smoking_options = ["從未吸菸", "已戒菸", "目前吸菸"]
                smoking_index = smoking_options.index(patient.get("smoking_history", "從未吸菸")) if patient.get("smoking_history") in smoking_options else 0
                smoking_history = st.selectbox("吸菸史", smoking_options, index=smoking_index)
            
            with col2:
                risk_options = ["low", "medium", "high"]
                risk_labels = ["🟢 低風險", "🟡 中風險", "🔴 高風險"]
                current_risk = patient.get("risk_level", "low")
                risk_index = risk_options.index(current_risk) if current_risk in risk_options else 0
                risk_level = st.selectbox("風險等級", risk_labels, index=risk_index)
                risk_level_value = risk_options[risk_labels.index(risk_level)]
                
                # 顯示風險說明
                st.caption(f"追蹤頻率: {RISK_LEVELS[risk_level_value]['follow_up']}")
            
            st.divider()
            
            # === 功能狀態 ===
            st.markdown("##### 📊 目前功能狀態")
            col1, col2 = st.columns(2)
            
            with col1:
                ecog_options = [f"{k}: {v}" for k, v in ECOG_PS.items()]
                current_ecog = patient.get("ecog_ps", "0")
                ecog_index = int(current_ecog) if str(current_ecog).isdigit() and int(current_ecog) < 5 else 0
                ecog_ps = st.selectbox("ECOG PS", ecog_options, index=ecog_index)
                ecog_value = ecog_ps.split(":")[0]
            
            with col2:
                kps_score = st.slider("KPS 分數", 0, 100, int(patient.get("kps_score", 100)) if patient.get("kps_score") else 100, step=10)
            
            st.divider()
            
            # === 狀態 ===
            st.markdown("##### 📝 系統狀態")
            col1, col2 = st.columns(2)
            
            with col1:
                status_options = ["pending_setup", "hospitalized", "normal", "active", "completed"]
                status_labels = ["待設定", "住院中", "正常追蹤", "需關注", "已結案"]
                current_status = patient.get("status", "pending_setup")
                status_index = status_options.index(current_status) if current_status in status_options else 0
                status = st.selectbox("追蹤狀態", status_labels, index=status_index)
                status_value = status_options[status_labels.index(status)]
            
            with col2:
                notes = st.text_area("備註", value=patient.get("notes", ""))
            
            # === 儲存 ===
            submitted = st.form_submit_button("💾 儲存病人資料", type="primary", use_container_width=True)
            
            if submitted:
                updates = {
                    "id_number": id_number,
                    "age": age,
                    "gender": gender,
                    "birth_date": birth_date,
                    "emergency_contact": emergency_contact,
                    "emergency_phone": emergency_phone,
                    "medical_record": medical_record,
                    "diagnosis": diagnosis,
                    "histology_type": histology_type,
                    "clinical_stage": clinical_stage,
                    "pathological_stage": pathological_stage,
                    "tumor_location": tumor_location,
                    "tumor_size": tumor_size,
                    "surgery_date": surgery_date.strftime("%Y-%m-%d"),
                    "surgery_type": surgery_type,
                    "surgery_approach": surgery_approach,
                    "resection_extent": resection_extent,
                    "lymph_node_dissection": lymph_node,
                    "surgical_margin": surgical_margin,
                    "complications": complications,
                    "adjuvant_chemo": adjuvant_chemo,
                    "adjuvant_radio": adjuvant_radio,
                    "target_therapy": target_therapy,
                    "immunotherapy": immunotherapy,
                    "comorbidities": ",".join(comorbidities),
                    "smoking_history": smoking_history,
                    "risk_level": risk_level_value,
                    "ecog_ps": ecog_value,
                    "kps_score": kps_score,
                    "status": status_value,
                    "notes": notes
                }
                
                if update_patient(patient_id, updates):
                    st.success("✅ 病人資料已更新！")
                    st.cache_data.clear()
                else:
                    st.error("更新失敗")
                    
    except Exception as e:
        st.error(f"載入失敗: {e}")


# ============================================
# 追蹤排程管理
# ============================================

def render_schedule_management(get_all_patients, get_schedules, save_schedule, update_schedule, username):
    """追蹤排程管理"""
    st.subheader("📅 追蹤排程管理")
    
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📋 排程總覽", "➕ 新增排程", "⏰ 逾期提醒"])
    
    # === 排程總覽 ===
    with sub_tab1:
        try:
            schedules = get_schedules()
            patients = get_all_patients()
            
            if not schedules:
                st.info("尚無排程資料")
            else:
                # 篩選
                col1, col2, col3 = st.columns(3)
                with col1:
                    status_filter = st.selectbox("狀態", ["全部", "scheduled", "completed", "cancelled"], key="sch_status")
                with col2:
                    type_filter = st.selectbox("類型", ["全部"] + list(SCHEDULE_TYPES.values()), key="sch_type")
                with col3:
                    date_range = st.selectbox("時間", ["全部", "今天", "本週", "本月"], key="sch_date")
                
                filtered = schedules
                
                if status_filter != "全部":
                    filtered = [s for s in filtered if s.get("status") == status_filter]
                
                if type_filter != "全部":
                    filtered = [s for s in filtered if s.get("schedule_type") == type_filter]
                
                today = datetime.now().date()
                if date_range == "今天":
                    filtered = [s for s in filtered if s.get("scheduled_date") == today.strftime("%Y-%m-%d")]
                elif date_range == "本週":
                    week_start = today - timedelta(days=today.weekday())
                    week_end = week_start + timedelta(days=6)
                    filtered = [s for s in filtered if week_start.strftime("%Y-%m-%d") <= s.get("scheduled_date", "") <= week_end.strftime("%Y-%m-%d")]
                elif date_range == "本月":
                    month_start = today.replace(day=1)
                    filtered = [s for s in filtered if s.get("scheduled_date", "").startswith(month_start.strftime("%Y-%m"))]
                
                st.info(f"共 {len(filtered)} 筆排程")
                
                for sch in sorted(filtered, key=lambda x: x.get("scheduled_date", ""), reverse=False):
                    status = sch.get("status", "scheduled")
                    status_icon = {"scheduled": "📅", "completed": "✅", "cancelled": "❌"}.get(status, "")
                    
                    with st.expander(f"{status_icon} {sch.get('scheduled_date', '')} | {sch.get('patient_name', '')} | {sch.get('schedule_type', '')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**病人**: {sch.get('patient_name', '')}")
                            st.write(f"**類型**: {sch.get('schedule_type', '')}")
                            st.write(f"**日期**: {sch.get('scheduled_date', '')}")
                            st.write(f"**地點**: {sch.get('location', '')}")
                        with col2:
                            st.write(f"**狀態**: {status}")
                            st.write(f"**建立者**: {sch.get('created_by', '')}")
                            if sch.get("result"):
                                st.write(f"**結果**: {sch.get('result', '')}")
                        
                        if status == "scheduled":
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("✅ 完成", key=f"complete_{sch.get('schedule_id')}"):
                                    update_schedule(sch.get("schedule_id"), {"status": "completed"})
                                    st.success("已更新")
                                    st.rerun()
                            with col_b:
                                if st.button("❌ 取消", key=f"cancel_{sch.get('schedule_id')}"):
                                    update_schedule(sch.get("schedule_id"), {"status": "cancelled"})
                                    st.success("已更新")
                                    st.rerun()
                                    
        except Exception as e:
            st.error(f"載入失敗: {e}")
    
    # === 新增排程 ===
    with sub_tab2:
        try:
            patients = get_all_patients()
            
            with st.form("schedule_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p for p in patients}
                    selected = st.selectbox("選擇病人 *", list(patient_options.keys()))
                    patient = patient_options.get(selected, {})
                    
                    schedule_type = st.selectbox("排程類型 *", list(SCHEDULE_TYPES.values()))
                
                with col2:
                    scheduled_date = st.date_input("排程日期 *", value=datetime.now().date() + timedelta(days=7))
                    scheduled_time = st.time_input("排程時間")
                
                col1, col2 = st.columns(2)
                with col1:
                    location = st.text_input("地點", placeholder="如: 胸腔外科門診 5 診")
                with col2:
                    provider = st.text_input("負責醫師/護理師", value=username)
                
                notes = st.text_area("備註")
                
                submitted = st.form_submit_button("💾 新增排程", type="primary", use_container_width=True)
                
                if submitted:
                    schedule_data = {
                        "patient_id": patient.get("patient_id"),
                        "patient_name": patient.get("name"),
                        "schedule_type": schedule_type,
                        "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
                        "scheduled_time": scheduled_time.strftime("%H:%M"),
                        "location": location,
                        "provider": provider,
                        "notes": notes,
                        "created_by": username
                    }
                    
                    result = save_schedule(schedule_data)
                    if result:
                        st.success("✅ 排程已新增！")
                    else:
                        st.error("新增失敗")
                        
        except Exception as e:
            st.error(f"載入失敗: {e}")
    
    # === 逾期提醒 ===
    with sub_tab3:
        try:
            schedules = get_schedules()
            today = datetime.now().date()
            
            overdue = [s for s in schedules if 
                      s.get("status") == "scheduled" and 
                      s.get("scheduled_date", "") < today.strftime("%Y-%m-%d")]
            
            if overdue:
                st.warning(f"⚠️ 有 {len(overdue)} 筆逾期排程！")
                
                for sch in overdue:
                    scheduled_date = sch.get("scheduled_date", "")
                    days_overdue = (today - datetime.strptime(scheduled_date, "%Y-%m-%d").date()).days if scheduled_date else 0
                    
                    st.error(f"🔴 {sch.get('patient_name', '')} - {sch.get('schedule_type', '')} - 已逾期 {days_overdue} 天")
            else:
                st.success("✅ 沒有逾期排程")
                
        except Exception as e:
            st.error(f"載入失敗: {e}")


# ============================================
# 檢查結果追蹤
# ============================================

def render_lab_management(get_all_patients, get_lab_results, save_lab_result, username):
    """檢查結果追蹤"""
    st.subheader("🔬 檢查結果追蹤")
    
    sub_tab1, sub_tab2 = st.tabs(["📊 檢查紀錄", "➕ 新增結果"])
    
    # === 檢查紀錄 ===
    with sub_tab1:
        try:
            patients = get_all_patients()
            
            # 選擇病人
            patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p for p in patients}
            selected = st.selectbox("選擇病人查看", list(patient_options.keys()), key="lab_patient")
            patient = patient_options.get(selected, {})
            
            if patient:
                labs = get_lab_results(patient.get("patient_id"))
                
                if labs:
                    # 腫瘤標記趨勢
                    st.markdown("##### 📈 腫瘤標記趨勢")
                    
                    cea_data = []
                    for lab in sorted(labs, key=lambda x: x.get("test_date", "")):
                        if lab.get("cea"):
                            cea_data.append({
                                "日期": lab.get("test_date"),
                                "CEA": float(lab.get("cea")) if lab.get("cea") else None
                            })
                    
                    if cea_data:
                        df = pd.DataFrame(cea_data)
                        st.line_chart(df.set_index("日期"))
                    
                    # 檢查紀錄列表
                    st.markdown("##### 📋 檢查紀錄")
                    for lab in sorted(labs, key=lambda x: x.get("test_date", ""), reverse=True):
                        with st.expander(f"📅 {lab.get('test_date', '')} - {lab.get('test_type', '')}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**腫瘤標記:**")
                                if lab.get("cea"): st.write(f"- CEA: {lab.get('cea')}")
                                if lab.get("cyfra211"): st.write(f"- CYFRA21-1: {lab.get('cyfra211')}")
                                if lab.get("nse"): st.write(f"- NSE: {lab.get('nse')}")
                            with col2:
                                if lab.get("imaging_type"):
                                    st.write("**影像檢查:**")
                                    st.write(f"- 類型: {lab.get('imaging_type')}")
                                    st.write(f"- 結果: {lab.get('imaging_result')}")
                else:
                    st.info("此病人尚無檢查紀錄")
                    
        except Exception as e:
            st.error(f"載入失敗: {e}")
    
    # === 新增結果 ===
    with sub_tab2:
        try:
            patients = get_all_patients()
            
            with st.form("lab_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p for p in patients}
                    selected = st.selectbox("選擇病人 *", list(patient_options.keys()), key="lab_new")
                    patient = patient_options.get(selected, {})
                    
                    test_date = st.date_input("檢查日期 *")
                    test_type = st.selectbox("檢查類型", ["抽血", "影像", "抽血+影像"])
                
                with col2:
                    st.write("")  # 佔位
                
                # 腫瘤標記
                st.markdown("**腫瘤標記**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    cea = st.text_input("CEA", placeholder="ng/mL")
                with col2:
                    cyfra211 = st.text_input("CYFRA21-1", placeholder="ng/mL")
                with col3:
                    scc = st.text_input("SCC", placeholder="ng/mL")
                with col4:
                    nse = st.text_input("NSE", placeholder="ng/mL")
                
                # 影像
                st.markdown("**影像檢查**")
                col1, col2 = st.columns(2)
                with col1:
                    imaging_type = st.selectbox("影像類型", ["", "胸部 CT", "PET-CT", "胸部 X 光", "腦部 MRI", "骨掃描"])
                with col2:
                    imaging_result = st.selectbox("影像結果", ["", "穩定", "部分反應", "進展", "新病灶"])
                
                imaging_comparison = st.text_area("影像比較說明", placeholder="與前次比較...")
                notes = st.text_area("備註")
                
                submitted = st.form_submit_button("💾 儲存檢查結果", type="primary", use_container_width=True)
                
                if submitted:
                    lab_data = {
                        "patient_id": patient.get("patient_id"),
                        "patient_name": patient.get("name"),
                        "test_date": test_date.strftime("%Y-%m-%d"),
                        "test_type": test_type,
                        "cea": cea,
                        "cyfra211": cyfra211,
                        "scc": scc,
                        "nse": nse,
                        "imaging_type": imaging_type,
                        "imaging_result": imaging_result,
                        "imaging_comparison": imaging_comparison,
                        "notes": notes,
                        "created_by": username
                    }
                    
                    result = save_lab_result(lab_data)
                    if result:
                        st.success("✅ 檢查結果已儲存！")
                    else:
                        st.error("儲存失敗")
                        
        except Exception as e:
            st.error(f"載入失敗: {e}")


# ============================================
# 功能狀態評估
# ============================================

def render_functional_assessment(get_all_patients, get_functional_assessments, save_functional_assessment, username):
    """功能狀態評估"""
    st.subheader("📊 功能狀態評估")
    
    sub_tab1, sub_tab2 = st.tabs(["📈 評估紀錄", "➕ 新增評估"])
    
    # === 評估紀錄 ===
    with sub_tab1:
        try:
            patients = get_all_patients()
            
            patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p for p in patients}
            selected = st.selectbox("選擇病人查看", list(patient_options.keys()), key="func_patient")
            patient = patient_options.get(selected, {})
            
            if patient:
                assessments = get_functional_assessments(patient.get("patient_id"))
                
                if assessments:
                    # ECOG/KPS 趨勢
                    st.markdown("##### 📈 功能狀態趨勢")
                    
                    trend_data = []
                    for a in sorted(assessments, key=lambda x: x.get("assessment_date", "")):
                        trend_data.append({
                            "日期": a.get("assessment_date"),
                            "ECOG": int(a.get("ecog_ps", 0)) if a.get("ecog_ps") else 0,
                            "KPS": int(a.get("kps_score", 100)) if a.get("kps_score") else 100
                        })
                    
                    if trend_data:
                        df = pd.DataFrame(trend_data)
                        st.line_chart(df.set_index("日期"))
                    
                    # 評估紀錄
                    for a in sorted(assessments, key=lambda x: x.get("assessment_date", ""), reverse=True):
                        with st.expander(f"📅 {a.get('assessment_date', '')} - ECOG {a.get('ecog_ps', '')} / KPS {a.get('kps_score', '')}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**ECOG PS**: {a.get('ecog_ps', '')}")
                                st.write(f"**KPS**: {a.get('kps_score', '')}")
                            with col2:
                                st.write(f"**整體生活品質**: {a.get('global_qol', '')}")
                                st.write(f"**評估者**: {a.get('created_by', '')}")
                else:
                    st.info("此病人尚無功能評估紀錄")
                    
        except Exception as e:
            st.error(f"載入失敗: {e}")
    
    # === 新增評估 ===
    with sub_tab2:
        try:
            patients = get_all_patients()
            
            with st.form("func_form"):
                patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p for p in patients}
                selected = st.selectbox("選擇病人 *", list(patient_options.keys()), key="func_new")
                patient = patient_options.get(selected, {})
                
                assessment_date = st.date_input("評估日期 *")
                
                st.markdown("**功能狀態**")
                col1, col2 = st.columns(2)
                with col1:
                    ecog_options = [f"{k}: {v}" for k, v in ECOG_PS.items()]
                    ecog_ps = st.selectbox("ECOG PS *", ecog_options)
                with col2:
                    kps_score = st.slider("KPS 分數 *", 0, 100, 100, step=10)
                
                st.markdown("**生活品質量表 (0-100)**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    physical = st.slider("身體功能", 0, 100, 80)
                    role = st.slider("角色功能", 0, 100, 80)
                with col2:
                    emotional = st.slider("情緒功能", 0, 100, 80)
                    cognitive = st.slider("認知功能", 0, 100, 80)
                with col3:
                    social = st.slider("社會功能", 0, 100, 80)
                    global_qol = st.slider("整體生活品質", 0, 100, 80)
                
                notes = st.text_area("評估備註")
                
                submitted = st.form_submit_button("💾 儲存評估", type="primary", use_container_width=True)
                
                if submitted:
                    assessment_data = {
                        "patient_id": patient.get("patient_id"),
                        "patient_name": patient.get("name"),
                        "assessment_date": assessment_date.strftime("%Y-%m-%d"),
                        "ecog_ps": ecog_ps.split(":")[0],
                        "kps_score": kps_score,
                        "physical_function": physical,
                        "role_function": role,
                        "emotional_function": emotional,
                        "cognitive_function": cognitive,
                        "social_function": social,
                        "global_qol": global_qol,
                        "notes": notes,
                        "created_by": username
                    }
                    
                    result = save_functional_assessment(assessment_data)
                    if result:
                        st.success("✅ 功能評估已儲存！")
                    else:
                        st.error("儲存失敗")
                        
        except Exception as e:
            st.error(f"載入失敗: {e}")


# ============================================
# 治療摘要
# ============================================

def render_treatment_summary(get_all_patients, get_patient_reports, get_interventions):
    """治療摘要"""
    st.subheader("📄 治療摘要")
    
    try:
        patients = get_all_patients()
        
        patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p for p in patients}
        selected = st.selectbox("選擇病人", list(patient_options.keys()), key="summary_patient")
        patient = patient_options.get(selected, {})
        
        if patient:
            st.markdown("---")
            
            # === 治療摘要 ===
            st.markdown("### 📋 治療摘要")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**病人資訊**")
                st.write(f"- 姓名: {patient.get('name', '')}")
                st.write(f"- 年齡: {patient.get('age', '')} 歲")
                st.write(f"- 診斷: {patient.get('diagnosis', '')}")
                st.write(f"- 病理: {patient.get('histology_type', '')}")
                st.write(f"- 分期: {patient.get('pathological_stage', patient.get('clinical_stage', ''))}")
            
            with col2:
                st.markdown("**手術資訊**")
                st.write(f"- 手術日期: {patient.get('surgery_date', '')}")
                st.write(f"- 手術方式: {patient.get('surgery_type', '')}")
                st.write(f"- 切除範圍: {patient.get('resection_extent', '')}")
                st.write(f"- 切緣: {patient.get('surgical_margin', '')}")
                st.write(f"- 併發症: {patient.get('complications', '無')}")
            
            # 輔助治療
            if any([patient.get('adjuvant_chemo'), patient.get('adjuvant_radio'), 
                   patient.get('target_therapy'), patient.get('immunotherapy')]):
                st.markdown("**輔助治療**")
                if patient.get('adjuvant_chemo'):
                    st.write(f"- 化療: {patient.get('adjuvant_chemo')}")
                if patient.get('adjuvant_radio'):
                    st.write(f"- 放療: {patient.get('adjuvant_radio')}")
                if patient.get('target_therapy'):
                    st.write(f"- 標靶: {patient.get('target_therapy')}")
                if patient.get('immunotherapy'):
                    st.write(f"- 免疫: {patient.get('immunotherapy')}")
            
            st.markdown("---")
            
            # === 追蹤計畫 ===
            st.markdown("### 📅 追蹤計畫")
            
            risk = patient.get("risk_level", "low")
            risk_info = RISK_LEVELS.get(risk, RISK_LEVELS["low"])
            
            st.info(f"**風險等級**: {risk_info['color']} {risk_info['name']} - {risk_info['follow_up']}")
            
            st.markdown("""
            **標準追蹤時程（依 ASCO 指引）**:
            - 術後 1-2 年: 每 6 個月胸部 CT
            - 術後 3-5 年: 每年胸部 CT
            - 術後 5 年以上: 每年低劑量 CT
            
            **注意事項**:
            - 定期監測腫瘤標記 (CEA)
            - 注意復發警示症狀
            - 持續戒菸/避免二手菸
            """)
            
            # === 匯出按鈕 ===
            st.markdown("---")
            
            if st.button("📥 匯出治療摘要 (PDF)", type="primary"):
                st.info("PDF 匯出功能開發中...")
                
    except Exception as e:
        st.error(f"載入失敗: {e}")


# ============================================
# 追蹤歷程
# ============================================

def render_patient_history(get_all_patients, get_patient_reports, get_interventions):
    """追蹤歷程"""
    st.subheader("📈 追蹤歷程")
    
    try:
        patients = get_all_patients()
        
        patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')}) - D+{p.get('post_op_day', 0)}": p for p in patients}
        selected = st.selectbox("選擇病人", list(patient_options.keys()), key="history_patient")
        patient = patient_options.get(selected, {})
        
        if patient:
            patient_id = patient.get("patient_id")
            
            # 基本資訊
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("姓名", patient.get("name", ""))
            col2.metric("術後天數", f"D+{patient.get('post_op_day', 0)}")
            col3.metric("手術類型", patient.get("surgery_type", ""))
            col4.metric("風險等級", RISK_LEVELS.get(patient.get("risk_level", "low"), {}).get("name", ""))
            
            st.divider()
            
            # 回報紀錄
            reports = get_patient_reports(patient_id)
            
            if reports:
                reports_sorted = sorted(reports, key=lambda x: x.get("date", ""))
                
                # 趨勢圖
                st.markdown("##### 📊 症狀趨勢圖")
                
                chart_data = []
                for r in reports_sorted:
                    chart_data.append({
                        "日期": r.get("date", ""),
                        "評分": r.get("overall_score", 0)
                    })
                
                df = pd.DataFrame(chart_data)
                if not df.empty:
                    st.line_chart(df.set_index("日期"))
                
                # 統計
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("總回報數", len(reports))
                col2.metric("🔴 紅色警示", len([r for r in reports if r.get("alert_level") == "red"]))
                col3.metric("🟡 黃色警示", len([r for r in reports if r.get("alert_level") == "yellow"]))
                col4.metric("平均評分", f"{sum([r.get('overall_score', 0) for r in reports]) / len(reports):.1f}")
                
                # 詳細紀錄
                st.markdown("##### 📋 詳細回報紀錄")
                
                for r in sorted(reports, key=lambda x: x.get("date", ""), reverse=True)[:20]:
                    alert = r.get("alert_level", "green")
                    icon = {"red": "🔴", "yellow": "🟡", "green": "✅"}.get(alert, "")
                    
                    with st.expander(f"{icon} {r.get('date', '')} - 評分 {r.get('overall_score', 0)}/10"):
                        st.write(f"**警示等級**: {alert}")
                        st.write(f"**處理狀態**: {'已處理' if r.get('alert_handled') == 'Y' else '未處理'}")
            else:
                st.info("此病人尚無回報紀錄")
            
            # 介入紀錄
            st.divider()
            st.markdown("##### 📝 介入紀錄")
            
            interventions = get_interventions(patient_id)
            
            if interventions:
                for inv in sorted(interventions, key=lambda x: x.get("date", ""), reverse=True)[:10]:
                    with st.expander(f"📝 {inv.get('date', '')} - {inv.get('intervention_category', '')}"):
                        st.write(f"**類型**: {inv.get('intervention_type', '')}")
                        st.write(f"**方式**: {inv.get('method', '')}")
                        st.write(f"**內容**: {inv.get('content', '')}")
            else:
                st.info("此病人尚無介入紀錄")
                
    except Exception as e:
        st.error(f"載入失敗: {e}")
