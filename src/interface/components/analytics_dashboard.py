import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

class AnalyticsDashboard:
    """Analytics dashboard component for displaying search statistics and insights"""
    
    def __init__(self):
        self.css_styles = """
        <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            margin: 0.5rem 0;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .trend-up {
            color: #4caf50;
        }
        
        .trend-down {
            color: #f44336;
        }
        
        .trend-neutral {
            color: #ff9800;
        }
        
        .chart-container {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        </style>
        """
    
    def render_dashboard(self, search_stats: Dict[str, Any] = None) -> None:
        """
        Render the complete analytics dashboard
        
        Args:
            search_stats: Dictionary containing search statistics
        """
        # Apply CSS styles
        st.markdown(self.css_styles, unsafe_allow_html=True)
        
        # Use sample data if none provided
        if search_stats is None:
            search_stats = self._get_sample_stats()
        
        # Render dashboard sections
        self._render_overview_metrics(search_stats)
        self._render_search_trends(search_stats)
        self._render_source_performance(search_stats)
        self._render_job_insights(search_stats)
        self._render_user_activity(search_stats)
    
    def _get_sample_stats(self) -> Dict[str, Any]:
        """Generate sample statistics for demonstration"""
        return {
            "total_searches": 156,
            "total_jobs_found": 1247,
            "avg_response_time": 2.3,
            "success_rate": 94.2,
            "active_sources": 4,
            "search_trends": self._generate_sample_trends(),
            "source_performance": {
                "BDJobs": {"jobs": 456, "success_rate": 96.5, "avg_time": 1.8},
                "LinkedIn": {"jobs": 389, "success_rate": 92.1, "avg_time": 2.1},
                "Indeed": {"jobs": 234, "success_rate": 89.7, "avg_time": 2.5},
                "Web Search": {"jobs": 168, "success_rate": 85.3, "avg_time": 3.2}
            },
            "top_locations": [
                {"location": "Dhaka", "jobs": 567, "percentage": 45.5},
                {"location": "Chittagong", "jobs": 234, "percentage": 18.8},
                {"location": "Sylhet", "jobs": 123, "percentage": 9.9},
                {"location": "Remote", "jobs": 98, "percentage": 7.9},
                {"location": "Rajshahi", "jobs": 87, "percentage": 7.0}
            ],
            "top_job_types": [
                {"type": "Software Engineer", "jobs": 234, "percentage": 18.8},
                {"type": "Marketing Manager", "jobs": 156, "percentage": 12.5},
                {"type": "UI/UX Designer", "jobs": 123, "percentage": 9.9},
                {"type": "Data Analyst", "jobs": 98, "percentage": 7.9},
                {"type": "Project Manager", "jobs": 87, "percentage": 7.0}
            ],
            "salary_distribution": [
                {"range": "0-50K", "jobs": 234, "percentage": 18.8},
                {"range": "50K-100K", "jobs": 456, "percentage": 36.6},
                {"range": "100K-200K", "jobs": 345, "percentage": 27.7},
                {"range": "200K-500K", "jobs": 156, "percentage": 12.5},
                {"range": "500K+", "jobs": 56, "percentage": 4.5}
            ],
            "user_activity": self._generate_sample_user_activity()
        }
    
    def _generate_sample_trends(self) -> List[Dict[str, Any]]:
        """Generate sample search trends data"""
        trends = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            trends.append({
                "date": date.strftime("%Y-%m-%d"),
                "searches": max(0, 5 + (i % 7) * 2 + (i % 3)),
                "jobs_found": max(0, 20 + (i % 7) * 8 + (i % 5) * 3),
                "avg_response_time": 1.5 + (i % 5) * 0.3
            })
        
        return trends
    
    def _generate_sample_user_activity(self) -> List[Dict[str, Any]]:
        """Generate sample user activity data"""
        return [
            {"hour": "00:00", "searches": 12, "users": 8},
            {"hour": "06:00", "searches": 8, "users": 6},
            {"hour": "12:00", "searches": 45, "users": 32},
            {"hour": "18:00", "searches": 67, "users": 48},
            {"hour": "24:00", "searches": 15, "users": 12}
        ]
    
    def _render_overview_metrics(self, stats: Dict[str, Any]) -> None:
        """Render overview metrics cards"""
        st.header("📊 Overview Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Searches</div>
                <div class="metric-value">{stats['total_searches']:,}</div>
                <div class="trend-up">↗️ +12% this week</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Jobs Found</div>
                <div class="metric-value">{stats['total_jobs_found']:,}</div>
                <div class="trend-up">↗️ +8% this week</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Response Time</div>
                <div class="metric-value">{stats['avg_response_time']}s</div>
                <div class="trend-down">↘️ -15% this week</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value">{stats['success_rate']}%</div>
                <div class="trend-up">↗️ +2% this week</div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_search_trends(self, stats: Dict[str, Any]) -> None:
        """Render search trends chart"""
        st.header("📈 Search Trends")
        
        # Create DataFrame for trends
        df_trends = pd.DataFrame(stats['search_trends'])
        df_trends['date'] = pd.to_datetime(df_trends['date'])
        
        # Create trend chart
        fig = go.Figure()
        
        # Add searches line
        fig.add_trace(go.Scatter(
            x=df_trends['date'],
            y=df_trends['searches'],
            mode='lines+markers',
            name='Searches',
            line=dict(color='#667eea', width=3),
            marker=dict(size=6)
        ))
        
        # Add jobs found line
        fig.add_trace(go.Scatter(
            x=df_trends['date'],
            y=df_trends['jobs_found'],
            mode='lines+markers',
            name='Jobs Found',
            line=dict(color='#764ba2', width=3),
            marker=dict(size=6),
            yaxis='y2'
        ))
        
        # Update layout
        fig.update_layout(
            title="Search Activity Over Time",
            xaxis_title="Date",
            yaxis_title="Number of Searches",
            yaxis2=dict(title="Jobs Found", overlaying='y', side='right'),
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_source_performance(self, stats: Dict[str, Any]) -> None:
        """Render data source performance metrics"""
        st.header("🌐 Data Source Performance")
        
        # Create performance DataFrame
        sources_data = []
        for source, metrics in stats['source_performance'].items():
            sources_data.append({
                'Source': source,
                'Jobs Found': metrics['jobs'],
                'Success Rate (%)': metrics['success_rate'],
                'Avg Response Time (s)': metrics['avg_time']
            })
        
        df_sources = pd.DataFrame(sources_data)
        
        # Display metrics table
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Performance Metrics")
            st.dataframe(df_sources, use_container_width=True)
        
        with col2:
            st.subheader("Success Rates")
            
            # Create success rate chart
            fig = px.pie(
                df_sources, 
                values='Success Rate (%)', 
                names='Source',
                title="Success Rate by Source"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_job_insights(self, stats: Dict[str, Any]) -> None:
        """Render job insights and analysis"""
        st.header("💼 Job Market Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top Locations")
            
            # Location chart
            df_locations = pd.DataFrame(stats['top_locations'])
            fig = px.bar(
                df_locations,
                x='location',
                y='jobs',
                title="Jobs by Location",
                color='jobs',
                color_continuous_scale='viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top Job Types")
            
            # Job types chart
            df_job_types = pd.DataFrame(stats['top_job_types'])
            fig = px.pie(
                df_job_types,
                values='jobs',
                names='type',
                title="Jobs by Type"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        # Salary distribution
        st.subheader("💰 Salary Distribution")
        df_salary = pd.DataFrame(stats['salary_distribution'])
        
        fig = px.bar(
            df_salary,
            x='range',
            y='jobs',
            title="Jobs by Salary Range",
            color='jobs',
            color_continuous_scale='plasma'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_user_activity(self, stats: Dict[str, Any]) -> None:
        """Render user activity patterns"""
        st.header("👥 User Activity Patterns")
        
        # Create activity DataFrame
        df_activity = pd.DataFrame(stats['user_activity'])
        
        # Activity by hour chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_activity['hour'],
            y=df_activity['searches'],
            name='Searches',
            marker_color='#667eea'
        ))
        
        fig.add_trace(go.Bar(
            x=df_activity['hour'],
            y=df_activity['users'],
            name='Active Users',
            marker_color='#764ba2'
        ))
        
        fig.update_layout(
            title="Activity by Hour of Day",
            xaxis_title="Hour",
            yaxis_title="Count",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_realtime_stats(self) -> None:
        """Render real-time statistics"""
        st.header("⚡ Real-time Statistics")
        
        # Simulate real-time data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Active Searches",
                value="12",
                delta="+3"
            )
        
        with col2:
            st.metric(
                label="Jobs Found Today",
                value="156",
                delta="+23"
            )
        
        with col3:
            st.metric(
                label="Active Users",
                value="8",
                delta="+2"
            )
        
        # Real-time activity feed
        st.subheader("🔄 Recent Activity")
        
        activities = [
            {"time": "2 min ago", "action": "Software Engineer search", "user": "User123"},
            {"time": "5 min ago", "action": "Marketing jobs found", "user": "User456"},
            {"time": "8 min ago", "action": "Remote developer search", "user": "User789"},
            {"time": "12 min ago", "action": "UI/UX Designer search", "user": "User101"},
        ]
        
        for activity in activities:
            st.write(f"🕐 **{activity['time']}** - {activity['action']} by {activity['user']}")
    
    def export_analytics(self, stats: Dict[str, Any]) -> None:
        """Export analytics data"""
        st.header("📤 Export Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export as CSV"):
                # Convert stats to CSV format
                df_export = pd.DataFrame(stats['search_trends'])
                csv = df_export.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"job_search_analytics_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📈 Export as JSON"):
                # Export as JSON
                json_data = json.dumps(stats, indent=2, default=str)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"job_search_analytics_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
