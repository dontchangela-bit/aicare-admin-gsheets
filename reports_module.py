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
6. AI vs 問卷對照分析 (AI vs Questionnaire)
7. 病人分群分析 (Cohort Analysis)
8. 個管師工作量 (Workload Analytics)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json

# 嘗試載入 scipy（統計分析用）
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except:
    SCIPY_AVAILABLE = False

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
            "📚 衛教統計分析",
            "📝 介入成效分析",
            "🤖 AI vs 問卷對照分析",
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
    elif report_type == "📚 衛教統計分析":
        render_education_analytics(patients, get_education_pushes)
    elif report_type == "📝 介入成效分析":
        render_intervention_analytics(interventions)
    elif report_type == "🤖 AI vs 問卷對照分析":
        render_ai_vs_questionnaire_analysis(patients, reports)
    elif report_type == "👥 病人分群分析":
        render_cohort_analysis(patients, reports)
    elif report_type == "👩‍⚕️ 個管師工作量":
        render_workload_analytics(reports, interventions)
    elif report_type == "📥 資料匯出":
        render_data_export(patients, reports, interventions)


def render_overview_dashboard(patients, reports, interventions):
    """總覽儀表板（研究級）"""
    st.subheader("📊 總覽儀表板")
    
    st.markdown("""
    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
    <b>📊 AI-CARE Lung Trial 統計總覽</b><br>
    本儀表板提供試驗執行狀態的即時監控，符合 GCP 與 IRB 報告要求。
    </div>
    """, unsafe_allow_html=True)
    
    # === 核心 KPI（第一行）===
    st.markdown("##### 🎯 核心指標")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    with col1:
        active = len([p for p in patients if p.get("status") not in ["discharged", "withdrawn", "completed"]])
        st.metric(
            "👥 收案中",
            active,
            delta=f"/ {len(patients)} 總數"
        )
    
    with col2:
        today_reports = len([r for r in reports if r.get("date") == today])
        st.metric("📋 今日回報", today_reports)
    
    with col3:
        pending_alerts = len([r for r in reports if r.get("alert_level") in ["red", "yellow"] and r.get("alert_handled") != "Y"])
        st.metric("⚠️ 待處理警示", pending_alerts,
                 delta="需處理" if pending_alerts > 0 else "✅",
                 delta_color="inverse" if pending_alerts > 0 else "off")
    
    with col4:
        # 整體依從率計算（有回報天數 / 術後總天數）
        if patients:
            total_expected = sum([max(p.get("post_op_day", 0), 1) for p in patients if p.get("status") not in ["discharged", "withdrawn"]])
            total_actual = len(reports)
            adherence = min(total_actual / max(total_expected, 1) * 100, 100)
            st.metric("✅ 整體依從率", f"{adherence:.1f}%",
                     delta="達標" if adherence >= 75 else "待加強",
                     delta_color="normal" if adherence >= 75 else "inverse")
        else:
            st.metric("✅ 整體依從率", "N/A")
    
    with col5:
        total_interventions = len(interventions)
        st.metric("📝 總介入次數", total_interventions)
    
    st.divider()
    
    # === 試驗執行狀態（第二行）===
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📍 收案狀態分布")
        status_counts = {}
        status_labels = {
            "hospitalized": "🏥 住院中",
            "normal": "📍 追蹤中",
            "active": "📍 追蹤中",
            "pending_setup": "⏳ 待設定",
            "discharged": "✅ 已出院",
            "completed": "🎉 完成追蹤",
            "withdrawn": "❌ 退出"
        }
        for p in patients:
            status = p.get("status", "unknown")
            label = status_labels.get(status, status)
            status_counts[label] = status_counts.get(label, 0) + 1
        
        if status_counts:
            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_layout(height=280, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("##### 📅 術後天數分布")
        post_op_groups = {
            "D+0~7": 0,
            "D+8~30": 0,
            "D+31~90": 0,
            "D+91~180": 0,
            "D+181+": 0
        }
        for p in patients:
            days = p.get("post_op_day", 0)
            if days <= 7:
                post_op_groups["D+0~7"] += 1
            elif days <= 30:
                post_op_groups["D+8~30"] += 1
            elif days <= 90:
                post_op_groups["D+31~90"] += 1
            elif days <= 180:
                post_op_groups["D+91~180"] += 1
            else:
                post_op_groups["D+181+"] += 1
        
        if any(post_op_groups.values()):
            fig = px.bar(
                x=list(post_op_groups.keys()),
                y=list(post_op_groups.values()),
                color=list(post_op_groups.values()),
                color_continuous_scale="Blues"
            )
            fig.update_layout(
                height=280, 
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                coloraxis_showscale=False,
                xaxis_title="術後階段",
                yaxis_title="人數"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # === 風險分層（第三行）===
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🎯 風險分層分布")
        risk_counts = {"🔴 高風險": 0, "🟡 中風險": 0, "🟢 低風險": 0, "⚪ 未分類": 0}
        for p in patients:
            risk = p.get("risk_level", "")
            if "高" in risk:
                risk_counts["🔴 高風險"] += 1
            elif "中" in risk:
                risk_counts["🟡 中風險"] += 1
            elif "低" in risk:
                risk_counts["🟢 低風險"] += 1
            else:
                risk_counts["⚪ 未分類"] += 1
        
        risk_df = pd.DataFrame([
            {"風險等級": k, "人數": v, "佔比": f"{v/len(patients)*100:.1f}%" if patients else "0%"}
            for k, v in risk_counts.items() if v > 0
        ])
        st.dataframe(risk_df, hide_index=True, use_container_width=True)
    
    with col2:
        st.markdown("##### 🏥 手術類型分布")
        surgery_counts = {}
        for p in patients:
            surgery = p.get("surgery_type", "未記錄")
            surgery_counts[surgery] = surgery_counts.get(surgery, 0) + 1
        
        if surgery_counts:
            surgery_df = pd.DataFrame([
                {"手術類型": k, "人數": v}
                for k, v in sorted(surgery_counts.items(), key=lambda x: x[1], reverse=True)
            ])
            st.dataframe(surgery_df, hide_index=True, use_container_width=True)
    
    st.divider()
    
    # === 警示與依從性趨勢（第四行）===
    st.markdown("##### 📈 趨勢分析（近 30 天）")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**警示等級趨勢**")
        
        daily_alerts = {}
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_alerts[date] = {"紅色": 0, "黃色": 0, "綠色": 0}
        
        for r in reports:
            date = r.get("date", "")
            if date in daily_alerts:
                level = r.get("alert_level", "green")
                if level == "red":
                    daily_alerts[date]["紅色"] += 1
                elif level == "yellow":
                    daily_alerts[date]["黃色"] += 1
                else:
                    daily_alerts[date]["綠色"] += 1
        
        dates = sorted(daily_alerts.keys())
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=[daily_alerts[d]["紅色"] for d in dates],
            name="🔴 紅色", line=dict(color="#dc3545"), mode="lines"
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=[daily_alerts[d]["黃色"] for d in dates],
            name="🟡 黃色", line=dict(color="#ffc107"), mode="lines"
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=[daily_alerts[d]["綠色"] for d in dates],
            name="🟢 綠色", line=dict(color="#28a745"), mode="lines"
        ))
        fig.update_layout(height=280, margin=dict(t=30, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**每週依從率趨勢**")
        
        # 計算每週依從率
        weekly_adherence = {}
        for i in range(8):  # 8 週
            week_start = datetime.now() - timedelta(weeks=i+1)
            week_end = datetime.now() - timedelta(weeks=i)
            week_label = week_start.strftime("%m/%d")
            
            week_reports = len([r for r in reports 
                               if week_start.strftime("%Y-%m-%d") <= r.get("date", "") < week_end.strftime("%Y-%m-%d")])
            week_expected = len([p for p in patients if p.get("status") not in ["discharged"]]) * 7
            
            adherence = (week_reports / max(week_expected, 1)) * 100
            weekly_adherence[week_label] = min(adherence, 100)
        
        if weekly_adherence:
            weeks = list(reversed(list(weekly_adherence.keys())))
            values = [weekly_adherence[w] for w in weeks]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=weeks, y=values,
                marker_color=["#28a745" if v >= 75 else "#ffc107" if v >= 50 else "#dc3545" for v in values]
            ))
            fig.add_hline(y=75, line_dash="dash", line_color="green", annotation_text="目標 75%")
            fig.update_layout(height=280, margin=dict(t=30, b=20, l=20, r=20), yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # === 研究摘要統計（第五行）===
    st.markdown("##### 📋 研究摘要統計")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**收案統計**")
        st.write(f"• 總收案數: {len(patients)}")
        st.write(f"• 追蹤中: {len([p for p in patients if p.get('status') in ['normal', 'active', 'hospitalized']])}")
        st.write(f"• 完成追蹤: {len([p for p in patients if p.get('status') == 'completed'])}")
        st.write(f"• 退出/失訪: {len([p for p in patients if p.get('status') in ['withdrawn', 'lost']])}")
    
    with col2:
        st.markdown("**回報統計**")
        st.write(f"• 總回報數: {len(reports)}")
        st.write(f"• 紅色警示: {len([r for r in reports if r.get('alert_level') == 'red'])}")
        st.write(f"• 黃色警示: {len([r for r in reports if r.get('alert_level') == 'yellow'])}")
        st.write(f"• AI 摘要數: {len([r for r in reports if r.get('ai_summary')])}")
    
    with col3:
        st.markdown("**介入統計**")
        st.write(f"• 總介入次數: {len(interventions)}")
        improved = len([i for i in interventions if i.get("outcome") in ["改善", "部分改善"]])
        st.write(f"• 改善率: {improved/len(interventions)*100:.1f}%" if interventions else "• 改善率: N/A")
        total_duration = sum([int(i.get("duration", 0)) for i in interventions if str(i.get("duration", "0")).isdigit()])
        st.write(f"• 總介入時數: {total_duration/60:.1f} 小時")
        
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


def render_education_analytics(patients, get_education_pushes):
    """衛教統計分析"""
    st.subheader("📚 衛教統計分析")
    
    # 取得衛教資料
    try:
        education = get_education_pushes()
    except:
        education = []
    
    if not education:
        st.info("尚無衛教推播紀錄")
        return
    
    # === KPI 指標 ===
    col1, col2, col3, col4 = st.columns(4)
    
    total_pushes = len(education)
    read_pushes = len([e for e in education if e.get("status") == "read"])
    read_rate = (read_pushes / total_pushes * 100) if total_pushes > 0 else 0
    
    with col1:
        st.metric("📤 總推播數", total_pushes)
    with col2:
        st.metric("👁️ 已讀數", read_pushes)
    with col3:
        st.metric("📊 閱讀率", f"{read_rate:.1f}%")
    with col4:
        unique_patients = len(set([e.get("patient_id") for e in education]))
        st.metric("👥 涵蓋病人數", unique_patients)
    
    st.divider()
    
    # === 各類衛教推播統計 ===
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📂 各類別推播統計")
        category_stats = {}
        for e in education:
            cat = e.get("category", "未分類")
            if cat not in category_stats:
                category_stats[cat] = {"推播": 0, "已讀": 0}
            category_stats[cat]["推播"] += 1
            if e.get("status") == "read":
                category_stats[cat]["已讀"] += 1
        
        cat_df = pd.DataFrame([
            {"類別": k, "推播數": v["推播"], "已讀數": v["已讀"], 
             "閱讀率": f"{v['已讀']/v['推播']*100:.1f}%" if v["推播"] > 0 else "0%"}
            for k, v in category_stats.items()
        ])
        
        if not cat_df.empty:
            fig = px.bar(cat_df, x="類別", y=["推播數", "已讀數"], barmode="group")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("##### 📈 推播方式分布")
        push_type_stats = {}
        for e in education:
            pt = e.get("push_type", "manual")
            push_type_labels = {
                "auto": "🤖 自動推播",
                "manual": "👤 手動推播",
                "rule": "📋 規則推播"
            }
            label = push_type_labels.get(pt, pt)
            push_type_stats[label] = push_type_stats.get(label, 0) + 1
        
        if push_type_stats:
            fig = px.pie(
                values=list(push_type_stats.values()),
                names=list(push_type_stats.keys()),
                hole=0.4
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    # === 各衛教材料統計 ===
    st.markdown("##### 📖 各衛教材料統計")
    
    material_stats = {}
    for e in education:
        title = e.get("material_title", "未知")
        if title not in material_stats:
            material_stats[title] = {"推播": 0, "已讀": 0}
        material_stats[title]["推播"] += 1
        if e.get("status") == "read":
            material_stats[title]["已讀"] += 1
    
    mat_df = pd.DataFrame([
        {"衛教材料": k, "推播數": v["推播"], "已讀數": v["已讀"],
         "閱讀率": round(v["已讀"]/v["推播"]*100, 1) if v["推播"] > 0 else 0}
        for k, v in material_stats.items()
    ]).sort_values("推播數", ascending=False)
    
    if not mat_df.empty:
        st.dataframe(mat_df, hide_index=True, use_container_width=True)
    
    # === 病人衛教涵蓋率 ===
    st.markdown("##### 👥 病人衛教涵蓋分析")
    
    patient_edu_stats = {}
    for e in education:
        pid = e.get("patient_id")
        pname = e.get("patient_name", "")
        if pid not in patient_edu_stats:
            patient_edu_stats[pid] = {"name": pname, "推播": 0, "已讀": 0}
        patient_edu_stats[pid]["推播"] += 1
        if e.get("status") == "read":
            patient_edu_stats[pid]["已讀"] += 1
    
    # 找出未收到衛教的病人
    edu_patient_ids = set(patient_edu_stats.keys())
    all_patient_ids = set([p.get("patient_id") for p in patients])
    no_edu_patients = all_patient_ids - edu_patient_ids
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ 已收到衛教", len(edu_patient_ids))
    with col2:
        st.metric("⚠️ 未收到衛教", len(no_edu_patients))
    
    if no_edu_patients:
        with st.expander(f"查看 {len(no_edu_patients)} 位未收到衛教的病人"):
            no_edu_list = [p for p in patients if p.get("patient_id") in no_edu_patients]
            for p in no_edu_list[:20]:
                st.write(f"- {p.get('name', '未知')} ({p.get('patient_id')}) - D+{p.get('post_op_day', 0)}")


def render_intervention_analytics(interventions):
    """介入成效分析"""
    st.subheader("📝 介入成效分析")
    
    if not interventions:
        st.info("尚無介入紀錄")
        return
    
    # === KPI ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 總介入次數", len(interventions))
    
    with col2:
        improved = len([i for i in interventions if i.get("outcome") in ["改善", "部分改善"]])
        improve_rate = improved / len(interventions) * 100 if interventions else 0
        st.metric("✅ 改善率", f"{improve_rate:.1f}%")
    
    with col3:
        total_duration = sum([int(i.get("duration", 0)) for i in interventions if str(i.get("duration", "0")).isdigit()])
        avg_duration = total_duration / len(interventions) if interventions else 0
        st.metric("⏱️ 平均時長", f"{avg_duration:.1f} 分鐘")
    
    with col4:
        referrals = len([i for i in interventions if i.get("referral")])
        st.metric("🔄 轉介次數", referrals)
    
    st.divider()
    
    # === 各類別介入成效 ===
    st.markdown("##### 📊 各類別介入成效")
    
    category_stats = {}
    for inv in interventions:
        cat = inv.get("intervention_category", "未分類")
        if cat not in category_stats:
            category_stats[cat] = {"總數": 0, "改善": 0, "部分改善": 0, "無變化": 0, "惡化": 0}
        category_stats[cat]["總數"] += 1
        outcome = inv.get("outcome", "")
        if outcome in category_stats[cat]:
            category_stats[cat][outcome] += 1
    
    cat_df = pd.DataFrame([
        {
            "類別": k,
            "總數": v["總數"],
            "改善": v["改善"],
            "部分改善": v["部分改善"],
            "無變化": v["無變化"],
            "惡化": v["惡化"],
            "改善率": f"{(v['改善'] + v['部分改善']) / v['總數'] * 100:.1f}%" if v["總數"] > 0 else "0%"
        }
        for k, v in category_stats.items()
    ])
    
    if not cat_df.empty:
        st.dataframe(cat_df, hide_index=True, use_container_width=True)
    
    # === 圖表 ===
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📂 介入類別分布")
        if category_stats:
            fig = px.pie(
                values=[v["總數"] for v in category_stats.values()],
                names=list(category_stats.keys()),
                hole=0.4
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("##### 📈 成效分布")
        outcome_counts = {}
        for inv in interventions:
            outcome = inv.get("outcome", "未記錄")
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        
        if outcome_counts:
            fig = px.bar(
                x=list(outcome_counts.keys()),
                y=list(outcome_counts.values()),
                color=list(outcome_counts.keys()),
                color_discrete_map={
                    "改善": "#28a745", "部分改善": "#90EE90",
                    "無變化": "#6c757d", "惡化": "#dc3545", "待評估": "#ffc107"
                }
            )
            fig.update_layout(height=300, showlegend=False, xaxis_title="", yaxis_title="次數")
            st.plotly_chart(fig, use_container_width=True)
    
    # === 症狀評分變化分析 ===
    st.markdown("##### 📉 介入前後症狀評分變化")
    
    score_data = []
    for inv in interventions:
        pre = inv.get("pre_symptom_score", "")
        post = inv.get("post_symptom_score", "")
        if str(pre).isdigit() and str(post).isdigit():
            score_data.append({
                "類別": inv.get("intervention_category", ""),
                "介入前": int(pre),
                "介入後": int(post),
                "變化": int(post) - int(pre)
            })
    
    if score_data:
        score_df = pd.DataFrame(score_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 整體平均
            avg_pre = score_df["介入前"].mean()
            avg_post = score_df["介入後"].mean()
            avg_change = score_df["變化"].mean()
            
            st.metric("整體平均介入前", f"{avg_pre:.1f}")
            st.metric("整體平均介入後", f"{avg_post:.1f}", delta=f"{avg_change:.1f}")
        
        with col2:
            # 各類別平均變化
            category_change = score_df.groupby("類別")["變化"].mean().reset_index()
            category_change.columns = ["類別", "平均變化"]
            category_change["平均變化"] = category_change["平均變化"].round(2)
            st.dataframe(category_change, hide_index=True)
        
        st.caption("💡 負值表示症狀改善（分數降低）")
    
    # === 轉介分析 ===
    st.markdown("##### 🔄 轉介統計")
    
    referral_stats = {}
    for inv in interventions:
        ref = inv.get("referral", "")
        if ref:
            referral_stats[ref] = referral_stats.get(ref, 0) + 1
    
    if referral_stats:
        ref_df = pd.DataFrame([
            {"轉介單位": k, "次數": v}
            for k, v in sorted(referral_stats.items(), key=lambda x: x[1], reverse=True)
        ])
        st.dataframe(ref_df, hide_index=True)
    else:
        st.info("尚無轉介紀錄")
    
    # === 滿意度分析 ===
    st.markdown("##### 😊 病人滿意度分析")
    
    satisfaction_stats = {}
    for inv in interventions:
        sat = inv.get("satisfaction", "")
        if sat:
            satisfaction_stats[sat] = satisfaction_stats.get(sat, 0) + 1
    
    if satisfaction_stats:
        sat_order = ["非常不滿意", "不滿意", "普通", "滿意", "非常滿意"]
        sat_df = pd.DataFrame([
            {"滿意度": k, "次數": satisfaction_stats.get(k, 0)}
            for k in sat_order if k in satisfaction_stats
        ])
        
        fig = px.bar(sat_df, x="滿意度", y="次數", color="滿意度",
                     color_discrete_map={"非常不滿意": "#dc3545", "不滿意": "#fd7e14",
                                        "普通": "#ffc107", "滿意": "#90EE90", "非常滿意": "#28a745"})
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


# ============================================
# AI vs 問卷對照分析
# ============================================

# MDASI-LC 症狀項目對照
MDASI_LC_ITEMS = {
    "core_symptoms": {
        "pain": {"name": "疼痛", "mdasi_item": "1. 疼痛程度"},
        "fatigue": {"name": "疲勞", "mdasi_item": "2. 疲勞程度"},
        "nausea": {"name": "噁心", "mdasi_item": "3. 噁心程度"},
        "sleep": {"name": "睡眠障礙", "mdasi_item": "4. 睡眠障礙"},
        "distress": {"name": "情緒困擾", "mdasi_item": "5. 情緒困擾"},
        "dyspnea": {"name": "呼吸困難", "mdasi_item": "6. 呼吸困難"},
        "memory": {"name": "記憶困難", "mdasi_item": "7. 記憶困難"},
        "appetite": {"name": "食慾不振", "mdasi_item": "8. 食慾不振"},
        "drowsy": {"name": "嗜睡", "mdasi_item": "9. 嗜睡程度"},
        "dry_mouth": {"name": "口乾", "mdasi_item": "10. 口乾程度"},
        "sad": {"name": "悲傷", "mdasi_item": "11. 悲傷程度"},
        "vomiting": {"name": "嘔吐", "mdasi_item": "12. 嘔吐程度"},
        "numbness": {"name": "麻木", "mdasi_item": "13. 麻木程度"}
    },
    "lung_specific": {
        "cough": {"name": "咳嗽", "mdasi_item": "LC1. 咳嗽程度"},
        "constipation": {"name": "便秘", "mdasi_item": "LC2. 便秘程度"},
        "sore_throat": {"name": "喉嚨痛", "mdasi_item": "LC3. 喉嚨痛"},
        "chest_tightness": {"name": "胸悶", "mdasi_item": "LC4. 胸悶程度"}
    },
    "interference": {
        "activity": {"name": "日常活動", "mdasi_item": "I1. 日常活動干擾"},
        "mood": {"name": "情緒", "mdasi_item": "I2. 情緒干擾"},
        "work": {"name": "工作", "mdasi_item": "I3. 工作干擾"},
        "relations": {"name": "人際關係", "mdasi_item": "I4. 人際關係干擾"},
        "walking": {"name": "行走", "mdasi_item": "I5. 行走干擾"},
        "enjoyment": {"name": "生活樂趣", "mdasi_item": "I6. 生活樂趣干擾"}
    }
}

def render_ai_vs_questionnaire_analysis(patients, reports):
    """AI vs 問卷對照分析"""
    st.subheader("🤖 AI 對話 vs MDASI-LC 問卷對照分析")
    
    st.markdown("""
    <div style="background-color: #e7f3ff; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
    <h4>📊 研究目的</h4>
    <p>比較 <b>AI 對話式 PRO</b> 與 <b>傳統 MDASI-LC 問卷</b> 的一致性，評估 AI 對話是否能有效捕捉病人症狀。</p>
    <ul>
    <li><b>傳統問卷</b>：結構化數值評分（0-10分）</li>
    <li><b>AI 對話</b>：自然語言對話 + AI 摘要提取分數</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if not reports:
        st.warning("尚無回報資料")
        return
    
    # === 標籤頁 ===
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 趨勢對照", 
        "🔬 相關性分析",
        "📊 Bland-Altman 圖",
        "📋 詳細比較"
    ])
    
    # === 趨勢對照 ===
    with tab1:
        render_trend_comparison(patients, reports)
    
    # === 相關性分析 ===
    with tab2:
        render_correlation_analysis(reports)
    
    # === Bland-Altman 圖 ===
    with tab3:
        render_bland_altman(reports)
    
    # === 詳細比較 ===
    with tab4:
        render_detailed_comparison(patients, reports)


def render_trend_comparison(patients, reports):
    """趨勢對照圖"""
    st.markdown("##### 📈 症狀趨勢對照圖")
    
    # 選擇病人
    patient_options = {f"{p.get('name', '')} ({p.get('patient_id', '')})": p for p in patients}
    selected = st.selectbox("選擇病人", list(patient_options.keys()), key="trend_patient")
    patient = patient_options.get(selected, {})
    
    if not patient:
        return
    
    # 取得該病人的回報
    patient_reports = [r for r in reports if r.get("patient_id") == patient.get("patient_id")]
    patient_reports = sorted(patient_reports, key=lambda x: x.get("date", ""))
    
    if not patient_reports:
        st.info("此病人尚無回報資料")
        return
    
    # 選擇症狀
    symptom_options = ["pain", "dyspnea", "cough", "fatigue", "sleep", "appetite", "mood"]
    symptom_names = {
        "pain": "疼痛", "dyspnea": "呼吸困難", "cough": "咳嗽",
        "fatigue": "疲勞", "sleep": "睡眠", "appetite": "食慾", "mood": "情緒"
    }
    
    selected_symptom = st.selectbox(
        "選擇症狀",
        symptom_options,
        format_func=lambda x: symptom_names.get(x, x)
    )
    
    # 準備資料
    chart_data = []
    for r in patient_reports:
        date = r.get("date", "")
        
        # 問卷分數
        symptoms_str = r.get("symptoms", "{}")
        try:
            symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
            questionnaire_score = symptoms.get(selected_symptom, None)
            if questionnaire_score is not None:
                questionnaire_score = float(questionnaire_score)
        except:
            questionnaire_score = None
        
        # AI 摘要提取分數（從 ai_summary 解析）
        ai_summary = r.get("ai_summary", "")
        ai_score = extract_score_from_summary(ai_summary, selected_symptom)
        
        # 整體分數
        overall_score = r.get("overall_score", None)
        
        chart_data.append({
            "日期": date,
            "問卷分數": questionnaire_score,
            "AI提取分數": ai_score,
            "整體評分": overall_score
        })
    
    df = pd.DataFrame(chart_data)
    
    # 繪製對照圖
    st.markdown(f"**{symptom_names.get(selected_symptom, selected_symptom)} 趨勢對照**")
    
    fig = go.Figure()
    
    # 問卷分數線
    if df["問卷分數"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["日期"],
            y=df["問卷分數"],
            mode='lines+markers',
            name='MDASI 問卷分數',
            line=dict(color='#2196F3', width=2),
            marker=dict(size=8)
        ))
    
    # AI 提取分數線
    if df["AI提取分數"].notna().any():
        fig.add_trace(go.Scatter(
            x=df["日期"],
            y=df["AI提取分數"],
            mode='lines+markers',
            name='AI 對話提取分數',
            line=dict(color='#FF9800', width=2, dash='dash'),
            marker=dict(size=8, symbol='diamond')
        ))
    
    # 整體評分線
    fig.add_trace(go.Scatter(
        x=df["日期"],
        y=df["整體評分"],
        mode='lines+markers',
        name='整體評分',
        line=dict(color='#9C27B0', width=1),
        marker=dict(size=6),
        opacity=0.5
    ))
    
    fig.update_layout(
        height=400,
        xaxis_title="日期",
        yaxis_title="分數 (0-10)",
        yaxis=dict(range=[0, 10]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 顯示統計
    col1, col2, col3 = st.columns(3)
    
    with col1:
        q_scores = df["問卷分數"].dropna()
        if len(q_scores) > 0:
            st.metric("問卷平均分數", f"{q_scores.mean():.1f}")
    
    with col2:
        ai_scores = df["AI提取分數"].dropna()
        if len(ai_scores) > 0:
            st.metric("AI 平均分數", f"{ai_scores.mean():.1f}")
    
    with col3:
        # 計算相關係數
        if len(q_scores) > 2 and len(ai_scores) > 2:
            merged = df.dropna(subset=["問卷分數", "AI提取分數"])
            if len(merged) > 2:
                corr = merged["問卷分數"].corr(merged["AI提取分數"])
                st.metric("相關係數", f"{corr:.3f}")


def render_correlation_analysis(reports):
    """相關性分析"""
    st.markdown("##### 🔬 AI 對話 vs 問卷相關性分析")
    
    # 收集所有配對資料
    symptom_pairs = {
        "pain": [], "dyspnea": [], "cough": [],
        "fatigue": [], "sleep": [], "appetite": [], "mood": []
    }
    
    overall_pairs = []
    
    for r in reports:
        # 問卷分數
        symptoms_str = r.get("symptoms", "{}")
        try:
            symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
        except:
            symptoms = {}
        
        # AI 摘要
        ai_summary = r.get("ai_summary", "")
        
        # 整體分數配對
        overall = r.get("overall_score")
        ai_overall = extract_overall_from_summary(ai_summary)
        if overall is not None and ai_overall is not None:
            overall_pairs.append((float(overall), float(ai_overall)))
        
        # 各症狀配對
        for symptom in symptom_pairs.keys():
            q_score = symptoms.get(symptom)
            ai_score = extract_score_from_summary(ai_summary, symptom)
            if q_score is not None and ai_score is not None:
                symptom_pairs[symptom].append((float(q_score), float(ai_score)))
    
    # === 整體相關性 ===
    st.markdown("**整體評分相關性**")
    
    if len(overall_pairs) > 5:
        q_scores = [p[0] for p in overall_pairs]
        ai_scores = [p[1] for p in overall_pairs]
        
        # 散點圖
        fig = px.scatter(
            x=q_scores, y=ai_scores,
            labels={"x": "問卷整體評分", "y": "AI 提取整體評分"},
            trendline="ols"
        )
        fig.add_trace(go.Scatter(
            x=[0, 10], y=[0, 10],
            mode='lines',
            line=dict(color='red', dash='dash'),
            name='完美一致線'
        ))
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # 統計指標
        from scipy import stats
        corr, p_value = stats.pearsonr(q_scores, ai_scores)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pearson 相關係數", f"{corr:.3f}")
        col2.metric("P 值", f"{p_value:.4f}")
        col3.metric("樣本數", len(overall_pairs))
        
        # 平均絕對誤差
        mae = sum(abs(q - ai) for q, ai in overall_pairs) / len(overall_pairs)
        col4.metric("平均絕對誤差", f"{mae:.2f}")
    else:
        st.info("樣本數不足（需至少 5 筆配對資料）")
    
    # === 各症狀相關性 ===
    st.markdown("---")
    st.markdown("**各症狀相關性摘要**")
    
    correlation_summary = []
    
    symptom_names = {
        "pain": "疼痛", "dyspnea": "呼吸困難", "cough": "咳嗽",
        "fatigue": "疲勞", "sleep": "睡眠", "appetite": "食慾", "mood": "情緒"
    }
    
    for symptom, pairs in symptom_pairs.items():
        if len(pairs) > 5:
            q_scores = [p[0] for p in pairs]
            ai_scores = [p[1] for p in pairs]
            corr, p_value = stats.pearsonr(q_scores, ai_scores)
            mae = sum(abs(q - ai) for q, ai in pairs) / len(pairs)
            
            correlation_summary.append({
                "症狀": symptom_names.get(symptom, symptom),
                "相關係數": f"{corr:.3f}",
                "P 值": f"{p_value:.4f}",
                "平均誤差": f"{mae:.2f}",
                "樣本數": len(pairs),
                "一致性": "✅ 高" if corr > 0.7 else "🟡 中" if corr > 0.4 else "🔴 低"
            })
    
    if correlation_summary:
        corr_df = pd.DataFrame(correlation_summary)
        st.dataframe(corr_df, hide_index=True, use_container_width=True)
        
        # 整體評估
        high_corr = len([c for c in correlation_summary if "✅" in c["一致性"]])
        total = len(correlation_summary)
        
        st.markdown(f"""
        **📊 一致性評估結果**
        - 高一致性症狀: {high_corr}/{total}
        - AI 對話式 PRO 與傳統問卷的整體一致性: {"✅ 良好" if high_corr/total > 0.6 else "🟡 中等" if high_corr/total > 0.3 else "需要改進"}
        """)
    else:
        st.info("樣本數不足，無法進行相關性分析")


def render_bland_altman(reports):
    """Bland-Altman 圖"""
    st.markdown("##### 📊 Bland-Altman 一致性分析")
    
    st.markdown("""
    Bland-Altman 圖用於評估兩種測量方法的一致性：
    - **X 軸**：兩種方法的平均值
    - **Y 軸**：兩種方法的差異
    - **中線**：平均差異（bias）
    - **虛線**：95% 一致性界限 (Limits of Agreement)
    """)
    
    # 收集配對資料
    pairs = []
    for r in reports:
        q_score = r.get("overall_score")
        ai_summary = r.get("ai_summary", "")
        ai_score = extract_overall_from_summary(ai_summary)
        
        if q_score is not None and ai_score is not None:
            pairs.append({
                "questionnaire": float(q_score),
                "ai": float(ai_score),
                "mean": (float(q_score) + float(ai_score)) / 2,
                "diff": float(q_score) - float(ai_score)
            })
    
    if len(pairs) < 10:
        st.warning("樣本數不足（建議至少 10 筆配對資料）")
        return
    
    df = pd.DataFrame(pairs)
    
    # 計算統計量
    mean_diff = df["diff"].mean()
    std_diff = df["diff"].std()
    upper_loa = mean_diff + 1.96 * std_diff
    lower_loa = mean_diff - 1.96 * std_diff
    
    # 繪製 Bland-Altman 圖
    fig = go.Figure()
    
    # 散點
    fig.add_trace(go.Scatter(
        x=df["mean"],
        y=df["diff"],
        mode='markers',
        marker=dict(size=10, color='#2196F3'),
        name='資料點'
    ))
    
    # 平均差異線
    fig.add_hline(y=mean_diff, line_dash="solid", line_color="green",
                  annotation_text=f"Mean: {mean_diff:.2f}")
    
    # 95% 一致性界限
    fig.add_hline(y=upper_loa, line_dash="dash", line_color="red",
                  annotation_text=f"+1.96 SD: {upper_loa:.2f}")
    fig.add_hline(y=lower_loa, line_dash="dash", line_color="red",
                  annotation_text=f"-1.96 SD: {lower_loa:.2f}")
    
    # 零線
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    
    fig.update_layout(
        height=500,
        xaxis_title="平均值 ((問卷 + AI) / 2)",
        yaxis_title="差異 (問卷 - AI)",
        title="Bland-Altman Plot: 問卷 vs AI 對話"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 統計摘要
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("平均差異 (Bias)", f"{mean_diff:.2f}")
    col2.metric("差異標準差", f"{std_diff:.2f}")
    col3.metric("95% LoA 上限", f"{upper_loa:.2f}")
    col4.metric("95% LoA 下限", f"{lower_loa:.2f}")
    
    # 解讀
    st.markdown(f"""
    **📋 解讀**
    - 平均差異 {mean_diff:.2f} 表示 {"問卷分數略高於 AI" if mean_diff > 0 else "AI 分數略高於問卷" if mean_diff < 0 else "兩者平均相近"}
    - 95% 的差異落在 [{lower_loa:.2f}, {upper_loa:.2f}] 範圍內
    - {"✅ 一致性良好" if abs(upper_loa - lower_loa) < 4 else "🟡 一致性中等" if abs(upper_loa - lower_loa) < 6 else "⚠️ 一致性較低，建議進一步分析"}
    """)


def render_detailed_comparison(patients, reports):
    """詳細比較"""
    st.markdown("##### 📋 詳細比較表")
    
    # 選擇病人
    patient_options = {"全部病人": None}
    patient_options.update({f"{p.get('name', '')} ({p.get('patient_id', '')})": p.get("patient_id") for p in patients})
    selected = st.selectbox("選擇病人", list(patient_options.keys()), key="detail_patient")
    patient_id = patient_options.get(selected)
    
    # 篩選
    filtered = reports
    if patient_id:
        filtered = [r for r in reports if r.get("patient_id") == patient_id]
    
    if not filtered:
        st.info("無回報資料")
        return
    
    # 建立比較表
    comparison_data = []
    
    symptom_names = {
        "pain": "疼痛", "dyspnea": "呼吸困難", "cough": "咳嗽",
        "fatigue": "疲勞", "sleep": "睡眠", "appetite": "食慾", "mood": "情緒"
    }
    
    for r in sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)[:50]:
        # 問卷分數
        symptoms_str = r.get("symptoms", "{}")
        try:
            symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
        except:
            symptoms = {}
        
        # AI 摘要
        ai_summary = r.get("ai_summary", "")
        
        row = {
            "日期": r.get("date", ""),
            "病人": r.get("patient_name", ""),
            "問卷整體": r.get("overall_score", ""),
            "AI整體": extract_overall_from_summary(ai_summary) or "-"
        }
        
        # 各症狀比較
        for key, name in list(symptom_names.items())[:4]:
            q_score = symptoms.get(key, "-")
            ai_score = extract_score_from_summary(ai_summary, key)
            row[f"{name}(問卷)"] = q_score
            row[f"{name}(AI)"] = ai_score if ai_score else "-"
        
        comparison_data.append(row)
    
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, hide_index=True, use_container_width=True)
        
        # 匯出按鈕
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 下載比較資料 (CSV)",
            csv,
            "ai_vs_questionnaire_comparison.csv",
            "text/csv"
        )


def extract_score_from_summary(ai_summary, symptom):
    """從 AI 摘要中提取症狀分數"""
    if not ai_summary:
        return None
    
    import re
    
    symptom_patterns = {
        "pain": [r"疼痛[：:]\s*(\d+)", r"疼痛.*?(\d+)\s*分", r"痛.*?(\d+)"],
        "dyspnea": [r"呼吸困難[：:]\s*(\d+)", r"呼吸.*?(\d+)\s*分", r"喘.*?(\d+)"],
        "cough": [r"咳嗽[：:]\s*(\d+)", r"咳嗽.*?(\d+)\s*分", r"咳.*?(\d+)"],
        "fatigue": [r"疲勞[：:]\s*(\d+)", r"疲勞.*?(\d+)\s*分", r"累.*?(\d+)"],
        "sleep": [r"睡眠[：:]\s*(\d+)", r"睡眠.*?(\d+)\s*分", r"失眠.*?(\d+)"],
        "appetite": [r"食慾[：:]\s*(\d+)", r"食慾.*?(\d+)\s*分", r"胃口.*?(\d+)"],
        "mood": [r"情緒[：:]\s*(\d+)", r"情緒.*?(\d+)\s*分", r"心情.*?(\d+)"]
    }
    
    patterns = symptom_patterns.get(symptom, [])
    
    for pattern in patterns:
        match = re.search(pattern, ai_summary)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 10:
                return score
    
    return None


def extract_overall_from_summary(ai_summary):
    """從 AI 摘要中提取整體分數"""
    if not ai_summary:
        return None
    
    import re
    
    patterns = [
        r"整體評分[：:]\s*(\d+)",
        r"整體.*?(\d+)\s*/\s*10",
        r"評分[：:]\s*(\d+)",
        r"(\d+)\s*/\s*10\s*分"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, ai_summary)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 10:
                return score
    
    return None


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
    """資料匯出（完整版）"""
    st.subheader("📥 資料匯出中心")
    
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
    <b>💡 匯出說明</b><br>
    所有資料皆以 CSV 格式匯出，可用 Excel 開啟進行進階分析。
    匯出資料已去識別化處理，符合研究倫理規範。
    </div>
    """, unsafe_allow_html=True)
    
    # === 快速匯出 ===
    st.markdown("### 📦 快速匯出")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**👥 病人資料**")
        st.caption(f"共 {len(patients)} 筆")
        if patients:
            df = pd.DataFrame(patients)
            # 去除敏感欄位
            safe_cols = [c for c in df.columns if c not in ["password", "phone"]]
            df_safe = df[safe_cols] if safe_cols else df
            csv = df_safe.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "⬇️ 下載 CSV",
                csv,
                f"patients_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                key="dl_patients"
            )
    
    with col2:
        st.markdown("**📋 回報資料**")
        st.caption(f"共 {len(reports)} 筆")
        if reports:
            df = pd.DataFrame(reports)
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "⬇️ 下載 CSV",
                csv,
                f"reports_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                key="dl_reports"
            )
    
    with col3:
        st.markdown("**📝 介入紀錄**")
        st.caption(f"共 {len(interventions)} 筆")
        if interventions:
            df = pd.DataFrame(interventions)
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "⬇️ 下載 CSV",
                csv,
                f"interventions_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                key="dl_interventions"
            )
    
    with col4:
        st.markdown("**📊 全部資料**")
        st.caption("打包下載")
        if st.button("📦 產生完整匯出", key="export_all"):
            st.info("請分別下載上方各類資料")
    
    st.divider()
    
    # === 自訂報表 ===
    st.markdown("### 📊 自訂報表產生器")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox(
            "報表類型",
            [
                "期間回報摘要",
                "病人依從性報表",
                "症狀分析報表",
                "介入成效報表",
                "AI vs 問卷比較資料"
            ]
        )
    
    with col2:
        date_range = st.date_input(
            "日期範圍",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now()
        )
    
    if st.button("📊 產生報表", type="primary"):
        try:
            start_date = date_range[0].strftime("%Y-%m-%d")
            end_date = date_range[1].strftime("%Y-%m-%d") if len(date_range) > 1 else start_date
        except:
            start_date = end_date = datetime.now().strftime("%Y-%m-%d")
        
        # 篩選期間資料
        period_reports = [r for r in reports if start_date <= r.get("date", "") <= end_date]
        period_interventions = [i for i in interventions if start_date <= i.get("date", "") <= end_date]
        
        st.markdown(f"### 📋 {start_date} ~ {end_date}")
        
        if report_type == "期間回報摘要":
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
            
            if period_reports:
                df = pd.DataFrame(period_reports)
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "⬇️ 下載期間回報資料",
                    csv,
                    f"reports_{start_date}_{end_date}.csv",
                    "text/csv"
                )
        
        elif report_type == "病人依從性報表":
            adherence_data = []
            for p in patients:
                pid = p.get("patient_id")
                p_reports = [r for r in period_reports if r.get("patient_id") == pid]
                post_op = p.get("post_op_day", 0)
                
                # 計算期間天數
                try:
                    days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days + 1
                except:
                    days = 30
                
                adherence = len(p_reports) / days * 100 if days > 0 else 0
                
                adherence_data.append({
                    "病人ID": pid,
                    "姓名": p.get("name", ""),
                    "術後天數": post_op,
                    "期間回報數": len(p_reports),
                    "期間天數": days,
                    "依從率(%)": f"{adherence:.1f}"
                })
            
            df = pd.DataFrame(adherence_data)
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "⬇️ 下載依從性報表",
                csv,
                f"adherence_{start_date}_{end_date}.csv",
                "text/csv"
            )
        
        elif report_type == "症狀分析報表":
            symptom_names = {
                "pain": "疼痛", "dyspnea": "呼吸困難", "cough": "咳嗽",
                "fatigue": "疲勞", "sleep": "睡眠", "appetite": "食慾", "mood": "情緒"
            }
            
            symptom_data = []
            for r in period_reports:
                symptoms_str = r.get("symptoms", "{}")
                try:
                    symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
                    row = {
                        "日期": r.get("date", ""),
                        "病人": r.get("patient_name", ""),
                        "整體評分": r.get("overall_score", 0),
                        "警示等級": r.get("alert_level", "")
                    }
                    for key, name in symptom_names.items():
                        row[name] = symptoms.get(key, "")
                    symptom_data.append(row)
                except:
                    pass
            
            if symptom_data:
                df = pd.DataFrame(symptom_data)
                st.dataframe(df, hide_index=True, use_container_width=True)
                
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "⬇️ 下載症狀分析資料",
                    csv,
                    f"symptoms_{start_date}_{end_date}.csv",
                    "text/csv"
                )
        
        elif report_type == "介入成效報表":
            if period_interventions:
                df = pd.DataFrame(period_interventions)
                
                # 統計
                col1, col2, col3 = st.columns(3)
                col1.metric("介入總數", len(period_interventions))
                
                improved = len([i for i in period_interventions if i.get("outcome") in ["改善", "部分改善"]])
                col2.metric("改善數", improved)
                col3.metric("改善率", f"{improved/len(period_interventions)*100:.1f}%")
                
                st.dataframe(df, hide_index=True, use_container_width=True)
                
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "⬇️ 下載介入成效資料",
                    csv,
                    f"interventions_{start_date}_{end_date}.csv",
                    "text/csv"
                )
            else:
                st.info("此期間無介入紀錄")
        
        elif report_type == "AI vs 問卷比較資料":
            comparison_data = []
            for r in period_reports:
                ai_summary = r.get("ai_summary", "")
                symptoms_str = r.get("symptoms", "{}")
                
                try:
                    symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
                except:
                    symptoms = {}
                
                comparison_data.append({
                    "日期": r.get("date", ""),
                    "病人": r.get("patient_name", ""),
                    "問卷整體評分": r.get("overall_score", ""),
                    "問卷疼痛": symptoms.get("pain", ""),
                    "問卷呼吸困難": symptoms.get("dyspnea", ""),
                    "問卷咳嗽": symptoms.get("cough", ""),
                    "問卷疲勞": symptoms.get("fatigue", ""),
                    "AI摘要": ai_summary,
                    "警示等級": r.get("alert_level", "")
                })
            
            if comparison_data:
                df = pd.DataFrame(comparison_data)
                st.dataframe(df, hide_index=True, use_container_width=True)
                
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "⬇️ 下載 AI vs 問卷比較資料",
                    csv,
                    f"ai_vs_questionnaire_{start_date}_{end_date}.csv",
                    "text/csv"
                )
    
    st.divider()
    
    # === 研究用匯出 ===
    st.markdown("### 🔬 研究用資料匯出")
    
    st.warning("⚠️ 研究用資料包含詳細資訊，請確保符合 IRB 規範後再下載使用。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 MDASI-LC 格式匯出**")
        st.caption("符合 MD Anderson 格式的症狀資料")
        
        if st.button("產生 MDASI-LC 格式", key="mdasi_export"):
            mdasi_data = []
            for r in reports:
                patient = next((p for p in patients if p.get("patient_id") == r.get("patient_id")), {})
                symptoms_str = r.get("symptoms", "{}")
                try:
                    symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
                except:
                    symptoms = {}
                
                mdasi_data.append({
                    "Subject_ID": r.get("patient_id", ""),
                    "Assessment_Date": r.get("date", ""),
                    "Post_Op_Day": patient.get("post_op_day", ""),
                    "Surgery_Type": patient.get("surgery_type", ""),
                    "Pain": symptoms.get("pain", ""),
                    "Fatigue": symptoms.get("fatigue", ""),
                    "Nausea": symptoms.get("nausea", ""),
                    "Sleep_Disturbance": symptoms.get("sleep", ""),
                    "Distress": symptoms.get("distress", ""),
                    "Shortness_of_Breath": symptoms.get("dyspnea", ""),
                    "Lack_of_Appetite": symptoms.get("appetite", ""),
                    "Drowsiness": symptoms.get("drowsy", ""),
                    "Dry_Mouth": symptoms.get("dry_mouth", ""),
                    "Sadness": symptoms.get("mood", ""),
                    "Cough": symptoms.get("cough", ""),
                    "Overall_Severity": r.get("overall_score", ""),
                    "Alert_Level": r.get("alert_level", "")
                })
            
            if mdasi_data:
                df = pd.DataFrame(mdasi_data)
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "⬇️ 下載 MDASI-LC 格式",
                    csv,
                    f"mdasi_lc_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    key="dl_mdasi"
                )
    
    with col2:
        st.markdown("**📈 縱向追蹤資料**")
        st.caption("適合存活分析、趨勢分析使用")
        
        if st.button("產生縱向追蹤格式", key="longitudinal_export"):
            long_data = []
            for p in patients:
                pid = p.get("patient_id")
                p_reports = sorted(
                    [r for r in reports if r.get("patient_id") == pid],
                    key=lambda x: x.get("date", "")
                )
                
                for i, r in enumerate(p_reports):
                    symptoms_str = r.get("symptoms", "{}")
                    try:
                        symptoms = json.loads(symptoms_str) if isinstance(symptoms_str, str) else symptoms_str
                    except:
                        symptoms = {}
                    
                    long_data.append({
                        "Subject_ID": pid,
                        "Time_Point": i + 1,
                        "Date": r.get("date", ""),
                        "Post_Op_Day": p.get("post_op_day", ""),
                        "Overall_Score": r.get("overall_score", ""),
                        "Pain": symptoms.get("pain", ""),
                        "Dyspnea": symptoms.get("dyspnea", ""),
                        "Cough": symptoms.get("cough", ""),
                        "Fatigue": symptoms.get("fatigue", ""),
                        "Alert_Level": r.get("alert_level", ""),
                        "Handled": r.get("alert_handled", "")
                    })
            
            if long_data:
                df = pd.DataFrame(long_data)
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "⬇️ 下載縱向追蹤資料",
                    csv,
                    f"longitudinal_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    key="dl_long"
                )
