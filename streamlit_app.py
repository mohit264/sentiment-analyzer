import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Configuration
API_URL = "https://i9djmwh1h8.execute-api.us-west-2.amazonaws.com/prod/"
DATA_FILE = "sentiment_data.txt"

# Emoji mappings
SENTIMENT_EMOJIS = {
    'positive': ['😊', '👍', '✨'],
    'negative': ['😞', '👎', '❌'],
    'neutral': ['😐', '⚖️', '🤔']
}

def analyze_sentiment(message):
    """Call the sentiment analysis API"""
    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"message": message}
        )
        if response.status_code == 200:
            return response.json()['result']
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def save_to_file(message, sentiment):
    """Save analysis to text file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp}|{sentiment}|{message}\n")

def load_data():
    """Load data from text file"""
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=['timestamp', 'sentiment', 'message'])
    
    data = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|", 2)
            if len(parts) == 3:
                data.append({
                    'timestamp': parts[0],
                    'sentiment': parts[1],
                    'message': parts[2]
                })
    return pd.DataFrame(data)

def clear_history():
    """Clear all stored data"""
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

def export_data():
    """Export data as CSV"""
    df = load_data()
    return df.to_csv(index=False)

# Streamlit App
st.set_page_config(page_title="Sentiment Analyzer", page_icon="🎭", layout="wide")
st.title("🎭 Sentiment Analysis Dashboard")

# Create tabs
tab1, tab2 = st.tabs(["📝 Analyze Sentiment", "📊 Insights & Analytics"])

with tab1:
    st.header("Analyze Your Message")
    
    # Input section
    message = st.text_area("Enter your message:", placeholder="Type your message here...")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        analyze_btn = st.button("🔍 Analyze Sentiment", type="primary")
    
    with col2:
        clear_btn = st.button("🗑️ Clear History")
    
    if clear_btn:
        clear_history()
        st.success("History cleared!")
        st.rerun()
    
    # Analysis results
    if analyze_btn and message:
        with st.spinner("Analyzing sentiment..."):
            sentiment = analyze_sentiment(message)
            
            if sentiment:
                # Save to file
                save_to_file(message, sentiment)
                
                # Display result with emojis
                emojis = " ".join(SENTIMENT_EMOJIS[sentiment])
                
                if sentiment == 'positive':
                    st.success(f"**Sentiment: {sentiment.upper()}** {emojis}")
                elif sentiment == 'negative':
                    st.error(f"**Sentiment: {sentiment.upper()}** {emojis}")
                else:
                    st.info(f"**Sentiment: {sentiment.upper()}** {emojis}")
                
                st.write(f"**Message:** {message}")
    
    # Recent messages
    st.subheader("📋 Recent Messages")
    df = load_data()
    if not df.empty:
        # Show last 5 messages
        recent_df = df.tail(5).iloc[::-1]  # Reverse to show newest first
        for _, row in recent_df.iterrows():
            emojis = " ".join(SENTIMENT_EMOJIS[row['sentiment']])
            st.write(f"**{row['timestamp']}** - {row['sentiment'].upper()} {emojis}")
            st.write(f"_{row['message']}_")
            st.divider()

with tab2:
    st.header("📊 Sentiment Analytics")
    
    df = load_data()
    
    if df.empty:
        st.info("No data available. Analyze some messages first!")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_messages = len(df)
        positive_count = len(df[df['sentiment'] == 'positive'])
        negative_count = len(df[df['sentiment'] == 'negative'])
        neutral_count = len(df[df['sentiment'] == 'neutral'])
        
        with col1:
            st.metric("Total Messages", total_messages)
        with col2:
            st.metric("Positive 😊", positive_count)
        with col3:
            st.metric("Negative 😞", negative_count)
        with col4:
            st.metric("Neutral 😐", neutral_count)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            sentiment_counts = df['sentiment'].value_counts()
            fig_pie = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                title="Sentiment Distribution",
                color_discrete_map={
                    'positive': '#00ff00',
                    'negative': '#ff0000',
                    'neutral': '#ffff00'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart
            fig_bar = px.bar(
                x=sentiment_counts.index,
                y=sentiment_counts.values,
                title="Sentiment Counts",
                color=sentiment_counts.index,
                color_discrete_map={
                    'positive': '#00ff00',
                    'negative': '#ff0000',
                    'neutral': '#ffff00'
                }
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Time series (if we have enough data)
        if len(df) > 1:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df_time = df.set_index('timestamp').resample('H')['sentiment'].count().reset_index()
            
            fig_line = px.line(
                df_time,
                x='timestamp',
                y='sentiment',
                title="Messages Over Time"
            )
            st.plotly_chart(fig_line, use_container_width=True)
        
        # Export section
        st.subheader("📤 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = export_data()
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"sentiment_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            if st.button("🗑️ Clear All Data"):
                clear_history()
                st.success("All data cleared!")
                st.rerun()
        
        # Data table
        st.subheader("📋 All Messages")
        st.dataframe(df.iloc[::-1], use_container_width=True)  # Newest first