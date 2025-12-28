"""
AI-CARE Lung - Google Sheets 初始化/更新腳本
=============================================

功能：
1. 檢查現有工作表結構
2. 新增缺少的欄位
3. 建立缺少的工作表
4. 產生更新報告

使用方式：
1. 在 Streamlit Cloud 的 secrets 設定好 gcp_service_account 和 spreadsheet_id
2. 執行此腳本：streamlit run setup_sheets.py
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ============================================
# 完整欄位定義（與系統同步）
# ============================================

WORKSHEETS_CONFIG = {
    "Patients": [
        "patient_id", "name", "phone", "password", "birth_date", "age", "gender",
        "id_number", "emergency_contact", "emergency_phone",
        "diagnosis", "pathology", "clinical_stage", "pathological_stage", 
        "tumor_location", "tumor_size", "histology_type",
        "surgery_type", "surgery_date", "surgery_approach", "resection_extent",
        "lymph_node_dissection", "surgical_margin", "complications",
        "adjuvant_chemo", "adjuvant_radio", "target_therapy", "immunotherapy",
        "treatment_status", "treatment_notes",
        "comorbidities", "smoking_history", "risk_level",
        "ecog_ps", "kps_score",
        "status", "post_op_day", "consent_agreed", "consent_time", "registered_at",
        "notes"
    ],
    
    "Reports": [
        "report_id", "patient_id", "patient_name", "date", "timestamp",
        "overall_score", "symptoms", "messages_count",
        "conversation", "ai_summary",
        "alert_level", "alert_handled", "handled_by", "handled_time",
        "handling_action", "handling_notes"
    ],
    
    "Education": [
        "push_id", "patient_id", "patient_name", "material_id", "material_title",
        "category", "push_type", "pushed_by", "pushed_at",
        "read_at", "status"
    ],
    
    "Interventions": [
        "intervention_id", "patient_id", "patient_name", "date", "timestamp",
        "intervention_type", "intervention_category", "method", "duration", 
        "problem_addressed", "content", "pre_symptom_score", "post_symptom_score",
        "outcome", "satisfaction", "referral", "referral_status", "follow_up_date",
        "created_by", "notes"
    ],
    
    "Schedules": [
        "schedule_id", "patient_id", "patient_name", "schedule_type",
        "scheduled_date", "scheduled_time", "location", "provider",
        "reminder_sent", "status", "result", "notes", "created_by", "created_at"
    ],
    
    "Labs": [
        "lab_id", "patient_id", "patient_name", "test_date", "test_type",
        "cea", "cyfra211", "scc", "nse", "other_markers",
        "wbc", "hgb", "plt", "creatinine", "ast", "alt",
        "imaging_type", "imaging_result", "imaging_comparison",
        "notes", "created_by"
    ],
    
    "Functional": [
        "assessment_id", "patient_id", "patient_name", "assessment_date",
        "ecog_ps", "kps_score",
        "fev1_pre", "fev1_post", "fvc_pre", "fvc_post", "dlco",
        "six_min_walk", "spo2_rest", "spo2_exercise",
        "pain_score", "dyspnea_score", "fatigue_score",
        "qol_physical", "qol_emotional", "qol_social", "qol_overall",
        "notes", "assessed_by"
    ],
    
    "Problems": [
        "problem_id", "patient_id", "patient_name", "identified_date",
        "problem_type", "problem_category", "description", "severity",
        "status", "target_date", "resolution_date", "resolution_notes",
        "created_by", "updated_at"
    ]
}


def get_connection():
    """取得 Google Sheets 連線"""
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        spreadsheet_id = st.secrets.get("spreadsheet_id", "")
        return client.open_by_key(spreadsheet_id)
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None


def check_and_update_worksheet(spreadsheet, sheet_name, required_columns):
    """檢查並更新工作表"""
    results = {
        "status": "unknown",
        "existing_columns": [],
        "added_columns": [],
        "message": ""
    }
    
    try:
        # 嘗試取得工作表
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            results["status"] = "exists"
            
            # 取得現有欄位
            existing_headers = worksheet.row_values(1)
            results["existing_columns"] = existing_headers
            
            # 找出缺少的欄位
            missing_columns = [col for col in required_columns if col not in existing_headers]
            
            if missing_columns:
                # 新增缺少的欄位
                start_col = len(existing_headers) + 1
                for i, col in enumerate(missing_columns):
                    worksheet.update_cell(1, start_col + i, col)
                results["added_columns"] = missing_columns
                results["message"] = f"新增 {len(missing_columns)} 個欄位"
            else:
                results["message"] = "欄位完整，無需更新"
                
        except gspread.WorksheetNotFound:
            # 建立新工作表
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(required_columns))
            worksheet.append_row(required_columns)
            results["status"] = "created"
            results["added_columns"] = required_columns
            results["message"] = f"新建工作表，包含 {len(required_columns)} 個欄位"
            
    except Exception as e:
        results["status"] = "error"
        results["message"] = str(e)
    
    return results


def main():
    st.set_page_config(page_title="AI-CARE Lung - Sheets 設定", page_icon="⚙️")
    
    st.title("⚙️ Google Sheets 初始化/更新工具")
    
    st.markdown("""
    此工具會檢查您的 Google Sheets 並：
    - ✅ 新增缺少的工作表
    - ✅ 新增缺少的欄位
    - ✅ 保留現有資料
    """)
    
    # 連線測試
    st.markdown("### 1️⃣ 連線測試")
    
    spreadsheet = get_connection()
    
    if spreadsheet:
        st.success(f"✅ 成功連線到: {spreadsheet.title}")
        st.info(f"📋 Spreadsheet ID: {spreadsheet.id}")
    else:
        st.error("❌ 無法連線，請檢查 secrets 設定")
        st.stop()
    
    # 顯示目前狀態
    st.markdown("### 2️⃣ 目前工作表狀態")
    
    existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**現有工作表：**")
        for sheet in existing_sheets:
            st.write(f"• {sheet}")
    
    with col2:
        st.markdown("**需要的工作表：**")
        for sheet in WORKSHEETS_CONFIG.keys():
            if sheet in existing_sheets:
                st.write(f"✅ {sheet}")
            else:
                st.write(f"❌ {sheet} (缺少)")
    
    # 執行更新
    st.markdown("### 3️⃣ 執行更新")
    
    if st.button("🚀 開始檢查並更新", type="primary", use_container_width=True):
        
        st.markdown("---")
        
        progress = st.progress(0)
        status_container = st.empty()
        
        results_summary = []
        
        for i, (sheet_name, columns) in enumerate(WORKSHEETS_CONFIG.items()):
            progress.progress((i + 1) / len(WORKSHEETS_CONFIG))
            status_container.info(f"正在處理: {sheet_name}...")
            
            result = check_and_update_worksheet(spreadsheet, sheet_name, columns)
            result["sheet_name"] = sheet_name
            results_summary.append(result)
        
        status_container.success("✅ 處理完成！")
        
        # 顯示結果
        st.markdown("### 📋 更新報告")
        
        for result in results_summary:
            sheet_name = result["sheet_name"]
            
            if result["status"] == "created":
                st.success(f"🆕 **{sheet_name}**: {result['message']}")
            elif result["status"] == "exists" and result["added_columns"]:
                st.warning(f"➕ **{sheet_name}**: {result['message']}")
                with st.expander(f"查看新增的欄位"):
                    st.write(result["added_columns"])
            elif result["status"] == "exists":
                st.info(f"✅ **{sheet_name}**: {result['message']}")
            else:
                st.error(f"❌ **{sheet_name}**: {result['message']}")
        
        # 統計
        st.markdown("---")
        created = len([r for r in results_summary if r["status"] == "created"])
        updated = len([r for r in results_summary if r["status"] == "exists" and r["added_columns"]])
        unchanged = len([r for r in results_summary if r["status"] == "exists" and not r["added_columns"]])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🆕 新建工作表", created)
        col2.metric("➕ 更新工作表", updated)
        col3.metric("✅ 無需更新", unchanged)
        
        st.balloons()
    
    # 欄位參考
    st.markdown("### 4️⃣ 欄位參考")
    
    with st.expander("查看所有工作表欄位定義"):
        for sheet_name, columns in WORKSHEETS_CONFIG.items():
            st.markdown(f"**{sheet_name}** ({len(columns)} 欄位)")
            st.code(", ".join(columns))
            st.markdown("---")


if __name__ == "__main__":
    main()
