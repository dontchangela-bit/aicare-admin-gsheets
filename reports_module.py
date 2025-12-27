"""
AI-CARE Lung - 報表統計模組
===========================

根據 MDASI-LC (MD Anderson Symptom Inventory - Lung Cancer) 
及國際肺癌術後追蹤研究的最佳實務設計

包含以下報表類型：
1. 總覽儀表板 (Overview Dashboard)
2. 症狀趨勢分析 (Symptom Trajectory)
3. 警示統計 (Alert Analytics)
4. 回報依從性 (Adherence Rate)
5. 症狀熱力圖 (Symptom Heatmap)
6. 病人分群分析 (Cohort Analysis)
7. 個管師工作量 (Workload Analytics)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json

def render_advanced_reports(get_all_patients, get_all_reports, get_interventions, get_education_pushes):
    """進階報表統計頁面"""
    
    st.title("📈 報表統計")
    
    # 載入資料
    try:
        patients = get_all_patients()
        reports = get_all_reports()
        interventions = get_interventions()
        
        if not patients:
            st.warning("尚無病人資料")
            return
            
    except Exception as e:
        st.error(f"載入資料失敗: {e}")
        return
    
    # 報表選單
    report_type = st.selectbox(
        "選擇報表類型",
        [
            "📊 總覽儀表板",
            "📈 症狀趨勢分析", 
            "🔔 警示統計分析",
            "✅ 回報依從性分析",
            "🌡️ 症狀熱力圖",
            "👥 病人分群分析",
            "👩‍⚕️ 個管師工作量",
            "📥 資料匯出"
        ]
    )
    
    st.divider()
    
    if report_type == "📊 總覽儀表板":
        render_overview_dashboard(patients, reports, interventions)
    elif report_type == "📈 症狀趨勢分析":
        render_symptom_trajectory(patients, reports)
    elif report_type == "🔔 警示統計分析":
        render_alert_analytics(reports)
    elif report_type == "✅ 回報依從性分析":
        render_adherence_analysis(patients, reports)
    elif report_type == "🌡️ 症狀熱力圖":
        render_symptom_heatmap(patients, reports)
    elif report_type == "👥 病人分群分析":
        render_cohort_analysis(patients, reports)
    elif report_type == "👩‍⚕️ 個管師工作量":
        render_workload_analytics(reports, interventions)
    elif report_type == "📥 資料匯出":
        render_data_export(patients, reports, interventions)


def render_overview_dashboard(patients, reports, interventions):
    """總覽儀表板"""
    st.subheader("📊 總覽儀表板")
    
    # === KPI 指標卡片 ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "👥 總收案數",
            len(patients),
            delta=f"+{len([p for p in patients if p.get('post_op_day', 0) <= 7])} 本週新增"
        )
    
    with col2:
        today = datetime.now().strftime("%Y-%m-%d")
        today_reports = len([r for r in reports if r.get("date") == today])
        st.metric("📋 今日回報", today_reports)
    
    with col3:
        pending_alerts = len([r for r in reports if r.get("alert_level") in ["red", "yellow"] and r.get("alert_handled") != "Y"])
        st.metric("⚠️ 待處理警示", pending_alerts)
    
    with col4:
        if reports:
            total_days = sum([p.get("post_op_day", 0) for p in patients])
            adherence = len(reports) / max(total_days, 1) * 100
            st.metric("✅ 整體依從率", f"{min(adherence, 100):.1f}%")
        else:
            st.metric("✅ 整體依從率", "N/A")
    
    st.divider()
    
    # === 病人狀態分布 ===
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📍 病人狀態分布")
        status_counts = {}
        for p in patients:
            status = p.get("status", "unknown")
            status_labels = {
                "hospitalized": "🏥 住院中",
                "normal": "📍 追蹤中",
                "active": "📍 追蹤中",
                "pending_setup": "⏳ 待設定",
                "discharged": "✅ 已出院",
                "completed": "🎉 完成追蹤"
            }
            label = status_labels.get(status, status)
            status_counts[label] = status_counts.get(label, 0) + 1
        
        if status_counts:
            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("##### 📅 術後天數分布")
        post_op_groups = {
            "D+0~7 住院": 0,
            "D+8~30 急性期": 0,
            "D+31~90 恢復期": 0,
            "D+91~180 穩定期": 0,
            "D+181+ 長期追蹤": 0
        }
        for p in patients:
            days = p.get("post_op_day", 0)
            if days <= 7:
                post_op_groups["D+0~7 住院"] += 1
            elif days <= 30:
                post_op_groups["D+8~30 急性期"] += 1
            elif days <= 90:
                post_op_groups["D+31~90 恢復期"] += 1
            elif days <= 180:
                post_op_groups["D+91~180 穩定期"] += 1
            else:
                post_op_groups["D+181+ 長期追蹤"] += 1
        
        fig = px.bar(
            x=list(post_op_groups.keys()),
            y=list(post_op_groups.values()),
            color=list(post_op_groups.values()),
            color_continuous_scale="Blues"
        )
        fig.update_layout(
            height=300, 
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=False,
            xaxis_title="",
            yaxis_title="人數"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # === 最近 7 天回報趨勢 ===
    st.markdown("##### 📈 最近 7 天回報趨勢")
    
    # 準備每日資料
    daily_data = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
        day_reports = [r for r in reports if r.get("date") == date]
        daily_data.append({
            "日期": date,
            "回報數": len(day_reports),
            "紅色警示": len([r for r in day_reports if r.get("alert_level") == "red"]),
            "黃色警示": len([r for r in day_reports if r.get("alert_level") == "yellow"]),
            "正常": len([r for r in day_reports if r.get("alert_level") == "green"])
        })
    
    df_daily = pd.DataFrame(daily_data)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_daily["日期"], y=df_daily["回報數"], name="總回報", line=dict(width=3)))
    fig.add_trace(go.Bar(x=df_daily["日期"], y=df_daily["紅色警示"], name="🔴 紅色", marker_color="red", opacity=0.7))
    fig.add_trace(go.Bar(x=df_daily["日期"], y=df_daily["黃色警示"], name="🟡 黃色", marker_color="orange", opacity=0.7))
    fig.update_layout(height=300, barmode="stack", margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)


def render_symptom_trajectory(patients, reports):
    """症狀趨勢分析 - 參考 MDASI-LC 研究的呈現方式"""
    st.subheader("📈 症狀趨勢分析")
    
    st.info("""
    **說明**: 此分析參考 MD Anderson Symptom Inventory (MDASI-LC) 的研究方法，
    追蹤病人術後症狀隨時間的變化趨勢。
    """)
    
    # 選擇分析維度
    analysis_type = st.radio(
        "分析維度",
        ["依術後天數（所有病人平均）", "依手術類型比較", "個別病人追蹤"],
        horizontal=True
    )
    
    if analysis_type == "依術後天數（所有病人平均）":
        # 計算每個術後天數的平均症狀分數
        st.markdown("##### 術後症狀恢復曲線")
        
        # 按術後週數分組
        week_data = {}
        for r in reports:
            # 找到對應的病人
            patient = next((p for p in patients if p.get("patient_id") == r.get("patient_id")), None)
            if patient:
                report_date = r.get("date", "")
                surgery_date = patient.get("surgery_date", "")
                if report_date and surgery_date:
                    try:
                        rd = datetime.strptime(report_date, "%Y-%m-%d")
                        sd = datetime.strptime(surgery_date, "%Y-%m-%d")
                        post_op_day = (rd - sd).days
                        week = post_op_day // 7  # 術後第幾週
                        
                        if 0 <= week <= 26:  # 只看前 6 個月
                            if week not in week_data:
                                week_data[week] = []
                            week_data[week].append(r.get("overall_score", 0))
                    except:
                        pass
        
        if week_data:
            # 計算每週平均
            trajectory_data = []
            for week in sorted(week_data.keys()):
                scores = week_data[week]
                trajectory_data.append({
                    "術後週數": f"W{week}",
                    "週數": week,
                    "平均評分": sum(scores) / len(scores),
                    "樣本數": len(scores),
                    "最高分": max(scores),
                    "最低分": min(scores)
                })
            
            df = pd.DataFrame(trajectory_data)
            
            # 繪製趨勢圖（含信賴區間）
            fig = go.Figure()
            
            # 範圍區域
            fig.add_trace(go.Scatter(
                x=df["週數"].tolist() + df["週數"].tolist()[::-1],
                y=df["最高分"].tolist() + df["最低分"].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(68, 68, 68, 0.1)',
                line=dict(color='rgba(255,255,255,0)'),
                name='範圍'
            ))
            
            # 平均線
            fig.add_trace(go.Scatter(
                x=df["週數"],
                y=df["平均評分"],
                mode='lines+markers',
                name='平均評分',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            # 警示閾值線
            fig.add_hline(y=7, line_dash="dash", line_color="red", annotation_text="紅色警示閾值")
            fig.add_hline(y=4, line_dash="dash", line_color="orange", annotation_text="黃色警示閾值")
            
            fig.update_layout(
                title="術後症狀評分變化趨勢",
                xaxis_title="術後週數",
                yaxis_title="症狀評分 (0-10)",
                yaxis=dict(range=[0, 10]),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 顯示數據表
            with st.expander("查看詳細數據"):
                st.dataframe(df[["術後週數", "平均評分", "樣本數", "最低分", "最高分"]])
        else:
            st.info("尚無足夠資料進行分析")
    
    elif analysis_type == "依手術類型比較":
        st.markdown("##### 不同手術類型的症狀恢復比較")
        
        # 按手術類型分組
        surgery_types = list(set([p.get("surgery_type", "未知") for p in patients]))
        
        fig = go.Figure()
        
        for surgery_type in surgery_types:
            if not surgery_type or surgery_type == "待設定":
                continue
                
            type_patients = [p for p in patients if p.get("surgery_type") == surgery_type]
            type_patient_ids = [p.get("patient_id") for p in type_patients]
            type_reports = [r for r in reports if r.get("patient_id") in type_patient_ids]
            
            # 按週分組計算平均
            week_scores = {}
            for r in type_reports:
                patient = next((p for p in type_patients if p.get("patient_id") == r.get("patient_id")), None)
                if patient:
                    try:
                        rd = datetime.strptime(r.get("date", ""), "%Y-%m-%d")
                        sd = datetime.strptime(patient.get("surgery_date", ""), "%Y-%m-%d")
                        week = (rd - sd).days // 7
                        if 0 <= week <= 12:
                            if week not in week_scores:
                                week_scores[week] = []
                            week_scores[week].append(r.get("overall_score", 0))
                    except:
                        pass
            
            if week_scores:
                weeks = sorted(week_scores.keys())
                avg_scores = [sum(week_scores[w]) / len(week_scores[w]) for w in weeks]
                
                fig.add_trace(go.Scatter(
                    x=weeks,
                    y=avg_scores,
                    mode='lines+markers',
                    name=surgery_type
                ))
        
        fig.update_layout(
            title="不同手術類型症狀恢復曲線比較",
            xaxis_title="術後週數",
            yaxis_title="平均症狀評分",
            yaxis=dict(range=[0, 10]),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:  # 個別病人追蹤
        st.markdown("##### 個別病人症狀追蹤")
        
        patient_options = {f"{p.get('name', '未知')} ({p.get('patient_id', '')})": p.get('patient_id') for p in patients}
        selected_label = st.selectbox("選擇病人", list(patient_options.keys()))
        
        if selected_label:
            patient_id = patient_options[selected_label]
            patient_reports = sorted(
                [r for r in reports if r.get("patient_id") == patient_id],
                key=lambda x: x.get("date", "")
            )
            
            if patient_reports:
                dates = [r.get("date", "") for r in patient_reports]
                scores = [r.get("overall_score", 0) for r in patient_reports]
                
                fig = go.Figure()
                
                # 症狀評分線
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=scores,
                    mode='lines+markers',
                    name='整體評分',
                    line=dict(width=2),
                    marker=dict(size=8)
                ))
                
                # 警示閾值
                fig.add_hline(y=7, line_dash="dash", line_color="red")
                fig.add_hline(y=4, line_dash="dash", line_color="orange")
                
                fig.update_layout(
                    title=f"{selected_label} 的症狀追蹤",
                    xaxis_title="日期",
                    yaxis_title="症狀評分",
                    yaxis=dict(range=[0, 10]),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("此病人尚無回報紀錄")


def render_alert_analytics(reports):
    """警示統計分析"""
    st.subheader("🔔 警示統計分析")
    
    if not reports:
        st.info("尚無回報資料")
        return
    
    # 警示分布
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 警示等級分布")
        alert_counts = {
            "🔴 紅色警示": len([r for r in reports if r.get("alert_level") == "red"]),
            "🟡 黃色警示": len([r for r in reports if r.get("alert_level") == "yellow"]),
            "✅ 正常": len([r for r in reports if r.get("alert_level") == "green"])
        }
        
        fig = px.pie(
            values=list(alert_counts.values()),
            names=list(alert_counts.keys()),
            color_discrete_sequence=["#ff4444", "#ffaa00", "#44aa44"]
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("##### 警示處理率")
        red_alerts = [r for r in reports if r.get("alert_level") == "red"]
        yellow_alerts = [r for r in reports if r.get("alert_level") == "yellow"]
        
        red_handled = len([r for r in red_alerts if r.get("alert_handled") == "Y"])
        yellow_handled = len([r for r in yellow_alerts if r.get("alert_handled") == "Y"])
        
        handling_data = pd.DataFrame({
            "類型": ["🔴 紅色", "🟡 黃色"],
            "已處理": [red_handled, yellow_handled],
            "未處理": [len(red_alerts) - red_handled, len(yellow_alerts) - yellow_handled]
        })
        
        fig = px.bar(
            handling_data,
            x="類型",
            y=["已處理", "未處理"],
            barmode="stack",
            color_discrete_sequence=["#44aa44", "#cccccc"]
        )
        fig.update_layout(height=300, yaxis_title="數量")
        st.plotly_chart(fig, use_container_width=True)
    
    # 警示趨勢
    st.markdown("##### 每週警示趨勢")
    
    # 按週分組
    week_alerts = {}
    for r in reports:
        try:
            date = datetime.strptime(r.get("date", ""), "%Y-%m-%d")
            week_start = (date - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
            
            if week_start not in week_alerts:
                week_alerts[week_start] = {"red": 0, "yellow": 0, "green": 0}
            
            level = r.get("alert_level", "green")
            week_alerts[week_start][level] += 1
        except:
            pass
    
    if week_alerts:
        weeks = sorted(week_alerts.keys())[-12:]  # 最近 12 週
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=weeks, y=[week_alerts[w]["red"] for w in weeks], name="紅色", marker_color="red"))
        fig.add_trace(go.Bar(x=weeks, y=[week_alerts[w]["yellow"] for w in weeks], name="黃色", marker_color="orange"))
        fig.add_trace(go.Bar(x=weeks, y=[week_alerts[w]["green"] for w in weeks], name="正常", marker_color="green"))
        
        fig.update_layout(barmode="stack", height=350, xaxis_title="週", yaxis_title="回報數")
        st.plotly_chart(fig, use_container_width=True)


def render_adherence_analysis(patients, reports):
    """回報依從性分析"""
    st.subheader("✅ 回報依從性分析")
    
    st.info("""
    **依從率計算方式**: 實際回報天數 ÷ 應回報天數 × 100%
    
    根據研究，ePRO 系統的目標依從率為 **75%** 以上。
    """)
    
    # 計算每位病人的依從率
    adherence_data = []
    for p in patients:
        patient_id = p.get("patient_id")
        post_op_days = p.get("post_op_day", 0)
        
        if post_op_days <= 0:
            continue
        
        patient_reports = [r for r in reports if r.get("patient_id") == patient_id]
        unique_days = len(set([r.get("date") for r in patient_reports]))
        
        adherence = (unique_days / post_op_days * 100) if post_op_days > 0 else 0
        
        adherence_data.append({
            "病人": p.get("name", ""),
            "patient_id": patient_id,
            "術後天數": post_op_days,
            "回報天數": unique_days,
            "依從率": min(adherence, 100)
        })
    
    if adherence_data:
        df = pd.DataFrame(adherence_data)
        
        # 整體依從率
        col1, col2, col3 = st.columns(3)
        
        avg_adherence = df["依從率"].mean()
        with col1:
            st.metric("📊 平均依從率", f"{avg_adherence:.1f}%")
        with col2:
            high_adherence = len(df[df["依從率"] >= 75])
            st.metric("✅ 達標人數 (≥75%)", f"{high_adherence}/{len(df)}")
        with col3:
            low_adherence = len(df[df["依從率"] < 50])
            st.metric("⚠️ 低依從 (<50%)", low_adherence)
        
        st.divider()
        
        # 依從率分布
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 依從率分布")
            fig = px.histogram(
                df, 
                x="依從率", 
                nbins=10,
                color_discrete_sequence=["#1f77b4"]
            )
            fig.add_vline(x=75, line_dash="dash", line_color="green", annotation_text="目標 75%")
            fig.update_layout(height=300, xaxis_title="依從率 (%)", yaxis_title="人數")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("##### 依從率 vs 術後天數")
            fig = px.scatter(
                df,
                x="術後天數",
                y="依從率",
                hover_data=["病人"],
                color="依從率",
                color_continuous_scale="RdYlGn"
            )
            fig.add_hline(y=75, line_dash="dash", line_color="green")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # 低依從率病人列表
        st.markdown("##### ⚠️ 需關注的病人（依從率 < 75%）")
        low_adherence_df = df[df["依從率"] < 75].sort_values("依從率")
        if len(low_adherence_df) > 0:
            st.dataframe(
                low_adherence_df[["病人", "術後天數", "回報天數", "依從率"]].head(10),
                hide_index=True
            )
        else:
            st.success("所有病人依從率都達標！")


def render_symptom_heatmap(patients, reports):
    """症狀熱力圖"""
    st.subheader("🌡️ 症狀熱力圖")
    
    st.info("""
    **熱力圖說明**: 顏色越深代表症狀越嚴重。
    可用於快速識別哪些症狀在哪個時期最嚴重。
    """)
    
    # 解析症狀資料
    symptom_names = {
        "dyspnea": "呼吸困難",
        "pain": "疼痛",
        "cough": "咳嗽",
        "fatigue": "疲勞",
        "sleep": "睡眠",
        "appetite": "食慾",
        "mood": "情緒"
    }
    
    # 按週計算每個症狀的平均分數
    week_symptoms = {}
    
    for r in reports:
        try:
            date = datetime.strptime(r.get("date", ""), "%Y-%m-%d")
            # 找到對應病人計算術後週數
            patient = next((p for p in patients if p.get("patient_id") == r.get("patient_id")), None)
            if patient and patient.get("surgery_date"):
                sd = datetime.strptime(patient.get("surgery_date"), "%Y-%m-%d")
                week = (date - sd).days // 7
                
                if 0 <= week <= 12:
                    if week not in week_symptoms:
                        week_symptoms[week] = {s: [] for s in symptom_names.keys()}
                    
                    symptoms_str = r.get("symptoms", "{}")
                    symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
                    
                    for key in symptom_names.keys():
                        if key in symptoms:
                            week_symptoms[week][key].append(symptoms[key])
        except:
            pass
    
    if week_symptoms:
        # 建立熱力圖資料
        heatmap_data = []
        weeks = sorted(week_symptoms.keys())
        
        for symptom_key, symptom_name in symptom_names.items():
            row = []
            for week in weeks:
                scores = week_symptoms[week].get(symptom_key, [])
                avg = sum(scores) / len(scores) if scores else 0
                row.append(avg)
            heatmap_data.append(row)
        
        # 繪製熱力圖
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=[f"W{w}" for w in weeks],
            y=list(symptom_names.values()),
            colorscale="RdYlGn_r",  # 紅色=高分=嚴重
            zmin=0,
            zmax=10
        ))
        
        fig.update_layout(
            title="各症狀隨術後週數的變化熱力圖",
            xaxis_title="術後週數",
            yaxis_title="症狀",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption("💡 顏色說明：綠色=症狀輕微，黃色=中度，紅色=嚴重")
    else:
        st.info("尚無足夠的症狀資料進行分析")


def render_cohort_analysis(patients, reports):
    """病人分群分析"""
    st.subheader("👥 病人分群分析")
    
    # 分群維度選擇
    grouping = st.selectbox(
        "選擇分群維度",
        ["依手術類型", "依年齡層", "依性別", "依術後階段"]
    )
    
    if grouping == "依手術類型":
        group_field = "surgery_type"
        groups = list(set([p.get(group_field, "未知") for p in patients if p.get(group_field)]))
    elif grouping == "依年齡層":
        # 分成年齡組
        groups = ["<50歲", "50-59歲", "60-69歲", "70+歲"]
    elif grouping == "依性別":
        groups = ["男", "女"]
    else:
        groups = ["住院期 (D+0~7)", "急性期 (D+8~30)", "恢復期 (D+31~90)", "穩定期 (D+91+)"]
    
    # 計算各組統計
    group_stats = []
    
    for group in groups:
        if grouping == "依手術類型":
            group_patients = [p for p in patients if p.get("surgery_type") == group]
        elif grouping == "依年齡層":
            if group == "<50歲":
                group_patients = [p for p in patients if p.get("age", 0) < 50]
            elif group == "50-59歲":
                group_patients = [p for p in patients if 50 <= p.get("age", 0) < 60]
            elif group == "60-69歲":
                group_patients = [p for p in patients if 60 <= p.get("age", 0) < 70]
            else:
                group_patients = [p for p in patients if p.get("age", 0) >= 70]
        elif grouping == "依性別":
            group_patients = [p for p in patients if p.get("gender") == group]
        else:
            if "住院期" in group:
                group_patients = [p for p in patients if p.get("post_op_day", 0) <= 7]
            elif "急性期" in group:
                group_patients = [p for p in patients if 8 <= p.get("post_op_day", 0) <= 30]
            elif "恢復期" in group:
                group_patients = [p for p in patients if 31 <= p.get("post_op_day", 0) <= 90]
            else:
                group_patients = [p for p in patients if p.get("post_op_day", 0) > 90]
        
        patient_ids = [p.get("patient_id") for p in group_patients]
        group_reports = [r for r in reports if r.get("patient_id") in patient_ids]
        
        avg_score = sum([r.get("overall_score", 0) for r in group_reports]) / len(group_reports) if group_reports else 0
        red_rate = len([r for r in group_reports if r.get("alert_level") == "red"]) / len(group_reports) * 100 if group_reports else 0
        
        group_stats.append({
            "分組": group,
            "人數": len(group_patients),
            "回報數": len(group_reports),
            "平均評分": round(avg_score, 2),
            "紅色警示率": round(red_rate, 1)
        })
    
    df_stats = pd.DataFrame(group_stats)
    
    # 顯示統計表
    st.dataframe(df_stats, hide_index=True, use_container_width=True)
    
    # 視覺化比較
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(df_stats, x="分組", y="人數", title="各組人數", color="人數", color_continuous_scale="Blues")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(df_stats, x="分組", y="平均評分", title="各組平均症狀評分", color="平均評分", color_continuous_scale="RdYlGn_r")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)


def render_workload_analytics(reports, interventions):
    """個管師工作量分析"""
    st.subheader("👩‍⚕️ 個管師工作量")
    
    # 處理量統計
    handler_stats = {}
    
    for r in reports:
        handler = r.get("handled_by", "")
        if handler and r.get("alert_handled") == "Y":
            if handler not in handler_stats:
                handler_stats[handler] = {"處理警示": 0, "介入紀錄": 0}
            handler_stats[handler]["處理警示"] += 1
    
    for inv in interventions:
        handler = inv.get("created_by", "")
        if handler:
            if handler not in handler_stats:
                handler_stats[handler] = {"處理警示": 0, "介入紀錄": 0}
            handler_stats[handler]["介入紀錄"] += 1
    
    if handler_stats:
        df_workload = pd.DataFrame([
            {"個管師": k, **v, "總工作量": v["處理警示"] + v["介入紀錄"]}
            for k, v in handler_stats.items()
        ]).sort_values("總工作量", ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 個管師工作量分布")
            fig = px.bar(
                df_workload,
                x="個管師",
                y=["處理警示", "介入紀錄"],
                barmode="stack",
                title=""
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("##### 工作量統計")
            st.dataframe(df_workload, hide_index=True)
    else:
        st.info("尚無工作量資料")


def render_data_export(patients, reports, interventions):
    """資料匯出"""
    st.subheader("📥 資料匯出")
    
    st.markdown("選擇要匯出的資料：")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 匯出病人資料", use_container_width=True):
            df = pd.DataFrame(patients)
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ 下載 patients.csv",
                csv,
                "patients.csv",
                "text/csv"
            )
    
    with col2:
        if st.button("📥 匯出回報資料", use_container_width=True):
            df = pd.DataFrame(reports)
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ 下載 reports.csv",
                csv,
                "reports.csv",
                "text/csv"
            )
    
    with col3:
        if st.button("📥 匯出介入紀錄", use_container_width=True):
            df = pd.DataFrame(interventions)
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ 下載 interventions.csv",
                csv,
                "interventions.csv",
                "text/csv"
            )
    
    st.divider()
    
    # 自訂報表
    st.markdown("##### 📊 自訂報表產生器")
    
    date_range = st.date_input(
        "選擇日期範圍",
        value=(datetime.now() - timedelta(days=30), datetime.now()),
        max_value=datetime.now()
    )
    
    if st.button("產生期間報表", type="primary"):
        start_date = date_range[0].strftime("%Y-%m-%d")
        end_date = date_range[1].strftime("%Y-%m-%d") if len(date_range) > 1 else start_date
        
        period_reports = [r for r in reports if start_date <= r.get("date", "") <= end_date]
        
        st.markdown(f"### 📋 {start_date} ~ {end_date} 報表摘要")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("回報總數", len(period_reports))
        with col2:
            red = len([r for r in period_reports if r.get("alert_level") == "red"])
            st.metric("🔴 紅色警示", red)
        with col3:
            yellow = len([r for r in period_reports if r.get("alert_level") == "yellow"])
            st.metric("🟡 黃色警示", yellow)
        with col4:
            if period_reports:
                avg = sum([r.get("overall_score", 0) for r in period_reports]) / len(period_reports)
                st.metric("平均評分", f"{avg:.1f}")
