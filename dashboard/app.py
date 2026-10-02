import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from player_ids import BATTER_IDS, PITCHER_IDS, get_headshot_url, get_player_id

st.set_page_config(
    page_title="Brewers 2024 Statcast",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #003087; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    h1, h2, h3 { color: #B6922E !important; font-family: 'Georgia', serif; }
    [data-testid="metric-container"] {
        background-color: #1a1f2e;
        border: 1px solid #003087;
        border-radius: 8px;
        padding: 12px;
    }
    [data-testid="metric-container"] label {
        color: #B6922E !important;
        font-size: 13px !important;
        font-weight: bold !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 24px !important;
        font-weight: bold !important;
    }
    hr { border-color: #003087; }
    .stSelectbox > div > div {
        background-color: #1a1f2e;
        color: white;
        border: 1px solid #003087;
    }
    .stat-card {
        background: linear-gradient(135deg, #1a1f2e, #0e1117);
        border: 1px solid #003087;
        border-left: 4px solid #B6922E;
        border-radius: 8px;
        padding: 16px;
        margin: 4px 0;
    }
    .stat-card-title {
        color: #B6922E;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .stat-card-value {
        color: #ffffff;
        font-size: 28px;
        font-weight: bold;
        font-family: 'Georgia', serif;
    }
    .stat-card-sub { color: #888; font-size: 11px; margin-top: 2px; }
    .player-header {
        background: linear-gradient(135deg, #003087, #001a4d);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        border: 1px solid #B6922E;
    }
    .footer {
        text-align: center;
        color: #666;
        font-size: 12px;
        padding: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

BREWERS_NAVY = '#003087'
BREWERS_GOLD = '#B6922E'
BREWERS_LIGHT = '#4a7fd4'
DARK_BG = '#0e1117'
CARD_BG = '#1a1f2e'

CHART_COLORS = [
    BREWERS_NAVY, BREWERS_GOLD, BREWERS_LIGHT,
    '#4a4a8a', '#8a4a4a', '#4a8a4a', '#8a8a4a'
]

def base_layout(title='', height=400, showlegend=False, margin=None):
    m = margin or dict(l=10, r=20, t=40, b=10)
    return dict(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color='white', family='Georgia, serif'),
        title=dict(text=title, font=dict(color=BREWERS_GOLD, size=16)),
        height=height,
        showlegend=showlegend,
        margin=m
    )

def ax(title_text='', extra=None):
    d = dict(
        gridcolor='#2a2f3e',
        linecolor='#2a2f3e',
        tickcolor='white',
        tickfont=dict(color='white'),
        title=dict(text=title_text, font=dict(color='#aaa'))
    )
    if extra:
        d.update(extra)
    return d

@st.cache_data
def load_batters():
    df = pd.read_csv('data/all_brewers_batters.csv')
    df['game_date'] = pd.to_datetime(df['game_date'])
    return df

@st.cache_data
def load_pitchers():
    df = pd.read_csv('data/all_brewers_pitchers.csv')
    df['game_date'] = pd.to_datetime(df['game_date'])
    return df

batters = load_batters()
pitchers = load_pitchers()

def clean_name(name):
    if ',' in str(name):
        parts = name.split(', ')
        return f"{parts[1]} {parts[0]}"
    return name

batters['player_name'] = batters['player_name'].apply(clean_name)
pitchers['player_name'] = pitchers['player_name'].apply(clean_name)

batter_names = sorted(batters['player_name'].unique())
pitcher_names = sorted(pitchers['player_name'].unique())

with st.sidebar:
    st.markdown(
        "<div style='text-align:center; padding:10px 0 20px 0;'>"
        "<div style='font-size:48px;'>⚾</div>"
        "<div style='font-size:20px; font-weight:bold; color:#B6922E; "
        "letter-spacing:2px;'>BREWERS</div>"
        "<div style='font-size:12px; color:#aaa; letter-spacing:1px;'>"
        "2024 STATCAST ANALYTICS</div></div>",
        unsafe_allow_html=True
    )
    st.divider()
    page = st.radio(
        "Navigate",
        ["🏟️  Team Overview",
         "⚾  Batter Profile",
         "🎯  Pitcher Profile",
         "📊  Player Comparison"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown(
        "<div style='font-size:11px; color:#666; text-align:center;'>"
        "Data: Baseball Savant<br>via pybaseball<br>Apr – Sep 2024</div>",
        unsafe_allow_html=True
    )

def get_batter_summary(df, player_name):
    d = df[df['player_name'] == player_name]
    batted = d[d['launch_speed'].notna()]
    swings = d[d['description'].isin([
        'hit_into_play', 'swinging_strike', 'foul',
        'swinging_strike_blocked', 'foul_tip'
    ])]
    whiffs = d[d['description'].isin([
        'swinging_strike', 'swinging_strike_blocked', 'foul_tip'
    ])]
    pa = d[d['events'].notna() & (d['events'] != '')]
    hard_hit = batted[batted['launch_speed'] >= 95]
    barrels = batted[batted['launch_speed_angle'] == 6]
    return {
        'name': player_name,
        'pa': len(pa),
        'avg_ev': batted['launch_speed'].mean(),
        'max_ev': batted['launch_speed'].max(),
        'avg_la': batted['launch_angle'].mean(),
        'xba': d['estimated_ba_using_speedangle'].mean(),
        'xwoba': d['estimated_woba_using_speedangle'].mean(),
        'xslg': d['estimated_slg_using_speedangle'].mean(),
        'whiff_pct': len(whiffs) / len(swings) * 100 if len(swings) > 0 else 0,
        'hard_hit_pct': len(hard_hit) / len(batted) * 100 if len(batted) > 0 else 0,
        'barrel_pct': len(barrels) / len(batted) * 100 if len(batted) > 0 else 0,
    }

def get_pitcher_summary(df, player_name):
    d = df[df['player_name'] == player_name]
    swings = d[d['description'].isin([
        'hit_into_play', 'swinging_strike', 'foul',
        'swinging_strike_blocked', 'foul_tip'
    ])]
    whiffs = d[d['description'].isin([
        'swinging_strike', 'swinging_strike_blocked', 'foul_tip'
    ])]
    strikes = d[d['type'].isin(['S', 'X'])]
    return {
        'name': player_name,
        'pitches': len(d),
        'avg_velo': d['release_speed'].mean(),
        'max_velo': d['release_speed'].max(),
        'avg_spin': d['release_spin_rate'].mean(),
        'whiff_pct': len(whiffs) / len(swings) * 100 if len(swings) > 0 else 0,
        'strike_pct': len(strikes) / len(d) * 100 if len(d) > 0 else 0,
        'avg_extension': d['release_extension'].mean(),
    }

def stat_card(title, value, subtitle=''):
    st.markdown(
        f"<div class='stat-card'>"
        f"<div class='stat-card-title'>{title}</div>"
        f"<div class='stat-card-value'>{value}</div>"
        f"<div class='stat-card-sub'>{subtitle}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

def player_header_with_photo(name, player_id, subtitle, tags):
    headshot_url = get_headshot_url(player_id) if player_id else None
    col_img, col_info = st.columns([1, 4])
    with col_img:
        if headshot_url:
            st.markdown(
                f"<div style='text-align:center; padding-top:8px;'>"
                f"<img src='{headshot_url}' style='width:140px; "
                f"border-radius:50%; border:3px solid {BREWERS_GOLD}; "
                f"background:{CARD_BG};' "
                f"onerror=\"this.style.display='none'\"/></div>",
                unsafe_allow_html=True
            )
    with col_info:
        tags_html = ''.join([
            f"<span style='background:{BREWERS_NAVY}; color:white; "
            f"padding:3px 10px; border-radius:12px; font-size:12px; "
            f"margin-right:6px;'>{t}</span>"
            for t in tags
        ])
        st.markdown(
            f"<div class='player-header' style='margin-bottom:0;'>"
            f"<h2 style='color:{BREWERS_GOLD} !important; "
            f"margin:0; font-size:30px;'>{name}</h2>"
            f"<p style='color:#aaa; margin:6px 0 0 0; font-size:14px;'>"
            f"{subtitle}</p>"
            f"<div style='margin-top:10px; display:flex; gap:12px; "
            f"flex-wrap:wrap;'>{tags_html}</div></div>",
            unsafe_allow_html=True
        )

def draw_field_outline():
    theta = np.linspace(np.radians(45), np.radians(135), 200)
    x_arc = 330 * np.cos(theta)
    y_arc = 330 * np.sin(theta)
    shapes = [
        dict(type='line', x0=0, y0=0, x1=-220, y1=220,
             line=dict(color='white', width=1, dash='dash')),
        dict(type='line', x0=0, y0=0, x1=220, y1=220,
             line=dict(color='white', width=1, dash='dash')),
    ]
    bases = [(0,0), (-63,63), (0,127), (63,63), (0,0)]
    for i in range(len(bases)-1):
        shapes.append(dict(
            type='line',
            x0=bases[i][0], y0=bases[i][1],
            x1=bases[i+1][0], y1=bases[i+1][1],
            line=dict(color='white', width=2)
        ))
    shapes.append(dict(
        type='circle', x0=-10, y0=50, x1=10, y1=70,
        fillcolor='rgba(139,90,43,0.5)',
        line=dict(color='rgba(139,90,43,0.8)', width=1)
    ))
    annotations = [
        dict(x=-63, y=63, text='3B', showarrow=False,
             font=dict(color='white', size=10)),
        dict(x=0, y=135, text='2B', showarrow=False,
             font=dict(color='white', size=10)),
        dict(x=63, y=63, text='1B', showarrow=False,
             font=dict(color='white', size=10)),
    ]
    return x_arc, y_arc, shapes, annotations

# ─────────────────────────────────────────
# PAGE 1 — Team Overview
# ─────────────────────────────────────────
if page == "🏟️  Team Overview":
    st.markdown(
        "<div style='padding:8px 0 20px 0;'>"
        "<h1 style='margin:0; font-size:32px;'>"
        "Milwaukee Brewers — 2024 Season</h1>"
        "<p style='color:#aaa; margin:4px 0 0 0;'>"
        "Statcast Analytics Dashboard &nbsp;•&nbsp; "
        "18 Players &nbsp;•&nbsp; 24,970 Pitch Events</p></div>",
        unsafe_allow_html=True
    )

    st.subheader("⚾ Hitting — Statcast Leaderboard")
    summaries = [get_batter_summary(batters, n) for n in batter_names]
    batter_df = pd.DataFrame(summaries)

    display = batter_df[[
        'name','pa','avg_ev','max_ev',
        'xba','xwoba','hard_hit_pct','barrel_pct','whiff_pct'
    ]].copy()
    display.columns = [
        'Player','PA','Avg EV','Max EV',
        'xBA','xwOBA','Hard Hit%','Barrel%','Whiff%'
    ]
    display = display.sort_values('xwOBA', ascending=False)
    for col in ['Avg EV','Max EV']:
        display[col] = display[col].round(1)
    for col in ['xBA','xwOBA']:
        display[col] = display[col].round(3)
    for col in ['Hard Hit%','Barrel%','Whiff%']:
        display[col] = display[col].round(1)

    st.dataframe(
        display.style
        .background_gradient(subset=['xwOBA','Hard Hit%','Barrel%'], cmap='YlOrRd')
        .background_gradient(subset=['Whiff%'], cmap='RdYlGn_r'),
        use_container_width=True,
        hide_index=True,
        height=400
    )

    col_l, col_r = st.columns(2)

    with col_l:
        ev_s = batter_df.sort_values('avg_ev', ascending=True)
        colors = [BREWERS_GOLD if v >= 88 else BREWERS_NAVY for v in ev_s['avg_ev']]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=ev_s['name'], x=ev_s['avg_ev'], orientation='h',
            marker=dict(color=colors,
                        line=dict(color='rgba(255,255,255,0.1)', width=0.5)),
            text=ev_s['avg_ev'].round(1), textposition='outside',
            textfont=dict(color='white', size=11)
        ))
        fig.add_vline(x=88.0, line_dash='dash', line_color='#ff4444',
                      line_width=1.5, annotation_text='MLB Avg',
                      annotation_font_color='#ff4444')
        fig.update_layout(
            **base_layout('Average Exit Velocity', height=380),
            xaxis=ax('mph', {'range': [76, 96]}),
            yaxis=ax()
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        xw_s = batter_df.sort_values('xwoba', ascending=True)
        colors2 = [BREWERS_GOLD if v >= 0.320 else BREWERS_NAVY for v in xw_s['xwoba']]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            y=xw_s['name'], x=xw_s['xwoba'], orientation='h',
            marker=dict(color=colors2,
                        line=dict(color='rgba(255,255,255,0.1)', width=0.5)),
            text=xw_s['xwoba'].round(3), textposition='outside',
            textfont=dict(color='white', size=11)
        ))
        fig2.add_vline(x=0.320, line_dash='dash', line_color='#ff4444',
                       line_width=1.5, annotation_text='MLB Avg',
                       annotation_font_color='#ff4444')
        fig2.update_layout(
            **base_layout('xwOBA', height=380),
            xaxis=ax('xwOBA', {'range': [0.24, 0.42]}),
            yaxis=ax()
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("🎯 Pitching — Statcast Leaderboard")
    p_summaries = [get_pitcher_summary(pitchers, n) for n in pitcher_names]
    pitcher_df = pd.DataFrame(p_summaries)

    p_display = pitcher_df[[
        'name','pitches','avg_velo','max_velo','avg_spin','whiff_pct','strike_pct'
    ]].copy()
    p_display.columns = [
        'Player','Pitches','Avg Velo','Max Velo','Avg Spin','Whiff%','Strike%'
    ]
    p_display = p_display.sort_values('Whiff%', ascending=False)
    for col in ['Avg Velo','Max Velo']:
        p_display[col] = p_display[col].round(1)
    p_display['Avg Spin'] = p_display['Avg Spin'].round(0).astype(int)
    for col in ['Whiff%','Strike%']:
        p_display[col] = p_display[col].round(1)

    st.dataframe(
        p_display.style
        .background_gradient(subset=['Whiff%','Strike%'], cmap='YlOrRd')
        .background_gradient(subset=['Avg Velo'], cmap='Blues'),
        use_container_width=True,
        hide_index=True
    )

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        w_s = pitcher_df.sort_values('whiff_pct', ascending=True)
        w_colors = [BREWERS_GOLD if v >= 25 else BREWERS_NAVY for v in w_s['whiff_pct']]
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            y=w_s['name'], x=w_s['whiff_pct'], orientation='h',
            marker=dict(color=w_colors),
            text=w_s['whiff_pct'].round(1), textposition='outside',
            textfont=dict(color='white', size=11)
        ))
        fig3.add_vline(x=25.0, line_dash='dash', line_color='#ff4444',
                       annotation_text='MLB Avg', annotation_font_color='#ff4444')
        fig3.update_layout(
            **base_layout('Whiff Rate', height=320),
            xaxis=ax('%', {'range': [0, 45]}),
            yaxis=ax()
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col_r2:
        v_s = pitcher_df.sort_values('avg_velo', ascending=True)
        v_colors = [BREWERS_GOLD if v >= 93 else BREWERS_NAVY for v in v_s['avg_velo']]
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            y=v_s['name'], x=v_s['avg_velo'], orientation='h',
            marker=dict(color=v_colors),
            text=v_s['avg_velo'].round(1), textposition='outside',
            textfont=dict(color='white', size=11)
        ))
        fig4.add_vline(x=93.0, line_dash='dash', line_color='#ff4444',
                       annotation_text='MLB Avg', annotation_font_color='#ff4444')
        fig4.update_layout(
            **base_layout('Average Fastball Velocity', height=320),
            xaxis=ax('mph', {'range': [84, 100]}),
            yaxis=ax()
        )
        st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────
# PAGE 2 — Batter Profile
# ─────────────────────────────────────────
elif page == "⚾  Batter Profile":

    selected = st.selectbox("Select Batter", batter_names, key='batter_select')
    player_data = batters[batters['player_name'] == selected]
    batted = player_data[player_data['launch_speed'].notna()]
    s = get_batter_summary(batters, selected)
    player_id = BATTER_IDS.get(selected)

    player_header_with_photo(
        name=selected,
        player_id=player_id,
        subtitle=(f"Milwaukee Brewers &nbsp;•&nbsp; 2024 Season "
                  f"&nbsp;•&nbsp; {s['pa']} Plate Appearances"),
        tags=[
            f"Avg EV: {s['avg_ev']:.1f} mph",
            f"xwOBA: {s['xwoba']:.3f}",
            f"Hard Hit%: {s['hard_hit_pct']:.1f}%",
            f"Whiff%: {s['whiff_pct']:.1f}%",
        ]
    )

    st.divider()

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: stat_card("Avg Exit Velo", f"{s['avg_ev']:.1f}", "mph")
    with c2: stat_card("Max Exit Velo", f"{s['max_ev']:.1f}", "mph")
    with c3: stat_card("xBA", f"{s['xba']:.3f}", "expected batting avg")
    with c4: stat_card("xwOBA", f"{s['xwoba']:.3f}", "expected wOBA")
    with c5: stat_card("Hard Hit%", f"{s['hard_hit_pct']:.1f}%", "95+ mph EV")
    with c6: stat_card("Whiff%", f"{s['whiff_pct']:.1f}%", "swing and miss")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=batted['launch_speed'], nbinsx=30,
            marker=dict(color=BREWERS_NAVY,
                        line=dict(color=BREWERS_GOLD, width=0.5)),
            opacity=0.85
        ))
        fig.add_vline(
            x=batted['launch_speed'].mean(), line_dash='dash',
            line_color=BREWERS_GOLD, line_width=2,
            annotation_text=f"Avg: {batted['launch_speed'].mean():.1f}",
            annotation_font_color=BREWERS_GOLD
        )
        fig.add_vline(
            x=95, line_dash='dot', line_color='#44ff44', line_width=1.5,
            annotation_text='Hard Hit (95+)',
            annotation_font_color='#44ff44'
        )
        fig.update_layout(
            **base_layout('Exit Velocity Distribution', height=320),
            xaxis=ax('mph'),
            yaxis=ax('Count')
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=batted['launch_angle'], nbinsx=30,
            marker=dict(color=BREWERS_GOLD,
                        line=dict(color=BREWERS_NAVY, width=0.5)),
            opacity=0.85
        ))
        fig2.add_vline(
            x=batted['launch_angle'].mean(), line_dash='dash',
            line_color='white', line_width=2,
            annotation_text=f"Avg: {batted['launch_angle'].mean():.1f}°",
            annotation_font_color='white'
        )
        fig2.add_vrect(
            x0=10, x1=30, fillcolor='rgba(68,255,68,0.1)', layer='below',
            annotation_text='Sweet Spot', annotation_font_color='#44ff44',
            annotation_position='top left'
        )
        fig2.update_layout(
            **base_layout('Launch Angle Distribution', height=320),
            xaxis=ax('degrees'),
            yaxis=ax('Count')
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Spray chart
    st.subheader("Spray Chart")
    batted_events = batted[
        batted['hc_x'].notna() &
        batted['hc_y'].notna() &
        batted['events'].notna()
    ].copy()

    if len(batted_events) > 0:
        batted_events['hc_y_flip'] = 250 - batted_events['hc_y']
        batted_events['hc_x_c'] = batted_events['hc_x'] - 125

        result_colors = {
            'single': '#2196F3', 'double': '#4CAF50',
            'triple': '#FF9800', 'home_run': '#F44336',
            'field_out': '#555', 'grounded_into_double_play': '#444',
            'force_out': '#555', 'sac_fly': '#9C27B0', 'strikeout': '#222',
        }

        x_arc, y_arc, shapes, annotations = draw_field_outline()

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=x_arc, y=y_arc, mode='lines',
            line=dict(color='rgba(255,255,255,0.4)', width=2),
            showlegend=False
        ))

        for result, group in batted_events.groupby('events'):
            if result in ['', 'nan']:
                continue
            fig3.add_trace(go.Scatter(
                x=group['hc_x_c'], y=group['hc_y_flip'],
                mode='markers',
                name=result.replace('_', ' ').title(),
                marker=dict(
                    size=7, color=result_colors.get(result, '#666'),
                    opacity=0.8,
                    line=dict(color='rgba(255,255,255,0.2)', width=0.5)
                ),
                hovertemplate=(
                    f"<b>{result.replace('_',' ').title()}</b>"
                    "<br>%{text}<extra></extra>"
                ),
                text=group['game_date'].astype(str)
            ))

        fig3.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor='#1a3a1a',
            font=dict(color='white'),
            shapes=shapes,
            annotations=annotations,
            height=500,
            xaxis=dict(range=[-260,260], showgrid=False,
                       zeroline=False, visible=False),
            yaxis=dict(range=[-30,370], showgrid=False,
                       zeroline=False, visible=False,
                       scaleanchor='x', scaleratio=1),
            showlegend=True,
            legend=dict(
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', size=10),
                orientation='h', yanchor='bottom',
                y=1.02, xanchor='right', x=1
            ),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig3, use_container_width=True)

    # EV trend
    st.subheader("Exit Velocity — Season Trend")
    ev_weekly = (
        batted.set_index('game_date')
        .resample('W')['launch_speed']
        .agg(['mean','max'])
        .reset_index()
    )
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=ev_weekly['game_date'], y=ev_weekly['mean'],
        mode='lines+markers', name='Weekly Avg EV',
        line=dict(color=BREWERS_NAVY, width=2), marker=dict(size=5)
    ))
    fig4.add_trace(go.Scatter(
        x=ev_weekly['game_date'], y=ev_weekly['mean'].rolling(4).mean(),
        mode='lines', name='4-Week Rolling Avg',
        line=dict(color=BREWERS_GOLD, width=2.5, dash='dash')
    ))
    fig4.add_hline(
        y=88, line_dash='dot', line_color='#ff4444', line_width=1,
        annotation_text='MLB Avg (88)', annotation_font_color='#ff4444'
    )
    fig4.update_layout(
        **base_layout('Weekly Average Exit Velocity', height=300,
                      showlegend=True),
        xaxis=ax('Date'),
        yaxis=ax('mph'),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    )
    st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────
# PAGE 3 — Pitcher Profile
# ─────────────────────────────────────────
elif page == "🎯  Pitcher Profile":

    selected = st.selectbox("Select Pitcher", pitcher_names,
                            key='pitcher_select')
    player_data = pitchers[pitchers['player_name'] == selected]
    s = get_pitcher_summary(pitchers, selected)
    player_id = PITCHER_IDS.get(selected)

    player_header_with_photo(
        name=selected,
        player_id=player_id,
        subtitle=(f"Milwaukee Brewers &nbsp;•&nbsp; 2024 Season "
                  f"&nbsp;•&nbsp; {s['pitches']:,} Pitches Tracked"),
        tags=[
            f"Avg Velo: {s['avg_velo']:.1f} mph",
            f"Whiff%: {s['whiff_pct']:.1f}%",
            f"Strike%: {s['strike_pct']:.1f}%",
            f"Avg Spin: {s['avg_spin']:.0f} rpm",
        ]
    )

    st.divider()

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: stat_card("Avg Velocity", f"{s['avg_velo']:.1f}", "mph")
    with c2: stat_card("Max Velocity", f"{s['max_velo']:.1f}", "mph")
    with c3: stat_card("Avg Spin", f"{s['avg_spin']:.0f}", "rpm")
    with c4: stat_card("Whiff%", f"{s['whiff_pct']:.1f}%", "swing and miss")
    with c5: stat_card("Strike%", f"{s['strike_pct']:.1f}%", "all pitches")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        pitch_counts = player_data['pitch_name'].value_counts()
        pitch_counts = pitch_counts[
            (pitch_counts.index != 'null') & (pitch_counts > 5)
        ]
        fig = go.Figure(go.Pie(
            labels=pitch_counts.index, values=pitch_counts.values,
            hole=0.5,
            marker=dict(colors=CHART_COLORS[:len(pitch_counts)],
                        line=dict(color=DARK_BG, width=2)),
            textfont=dict(color='white', size=12),
            textinfo='label+percent'
        ))
        fig.add_annotation(
            text="Pitch<br>Arsenal", x=0.5, y=0.5,
            font=dict(size=13, color=BREWERS_GOLD), showarrow=False
        )
        fig.update_layout(
            **base_layout('', height=460, showlegend=True,
            margin=dict(l=40, r=40, t=20, b=40)
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        velo_data = player_data[
            player_data['release_speed'].notna() &
            (player_data['pitch_name'] != 'null') &
            player_data['pitch_name'].notna()
        ]
        pitch_order = (velo_data.groupby('pitch_name')['release_speed']
                       .median().sort_values(ascending=False).index.tolist())
        fig2 = go.Figure()
        for i, pitch in enumerate(pitch_order):
            pd_p = velo_data[velo_data['pitch_name'] == pitch]
            fig2.add_trace(go.Box(
                y=pd_p['release_speed'], name=pitch,
                marker_color=CHART_COLORS[i % len(CHART_COLORS)],
                line_color='white', boxmean=True
            ))
        fig2.update_layout(
            **base_layout('Velocity by Pitch Type', height=350),
            xaxis=ax(),
            yaxis=ax('mph')
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Pitch movement
    st.subheader("Pitch Movement Chart")
    movement_data = player_data[
        player_data['api_break_x_arm'].notna() &
        player_data['api_break_z_with_gravity'].notna() &
        (player_data['pitch_name'] != 'null') &
        player_data['pitch_name'].notna()
    ]

    if len(movement_data) > 0:
        avg_mov = (movement_data.groupby('pitch_name')[[
            'api_break_x_arm', 'api_break_z_with_gravity', 'release_speed'
        ]].mean().reset_index())

        fig3 = go.Figure()
        for i, row in avg_mov.iterrows():
            fig3.add_trace(go.Scatter(
                x=[row['api_break_x_arm']],
                y=[row['api_break_z_with_gravity']],
                mode='markers+text',
                name=row['pitch_name'],
                marker=dict(
                    size=max(20, row['release_speed']/3),
                    color=CHART_COLORS[i % len(CHART_COLORS)],
                    opacity=0.85,
                    line=dict(color='white', width=1.5)
                ),
                text=[row['pitch_name']],
                textposition='top center',
                textfont=dict(color='white', size=11),
                hovertemplate=(
                    f"<b>{row['pitch_name']}</b><br>"
                    f"H Break: {row['api_break_x_arm']:.1f} in<br>"
                    f"V Break: {row['api_break_z_with_gravity']:.1f} in<br>"
                    f"Avg Velo: {row['release_speed']:.1f} mph"
                    "<extra></extra>"
                )
            ))
        fig3.add_hline(y=0, line_color='rgba(255,255,255,0.3)', line_width=1)
        fig3.add_vline(x=0, line_color='rgba(255,255,255,0.3)', line_width=1)
        fig3.update_layout(
            **base_layout(
                'Pitch Movement — Pitcher POV (bubble size = velocity)',
                height=420
            ),
            xaxis=ax('Horizontal Break (inches) — Arm Side →'),
            yaxis=ax('Vertical Break (inches)')
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Pitch location heatmap
    st.subheader("Pitch Location Heatmap")
    pitch_filter = st.selectbox(
        "Filter by pitch type",
        ['All Pitches'] + list(
            player_data['pitch_name'].value_counts().index[:6]
        )
    )
    loc_data = player_data[
        player_data['plate_x'].notna() & player_data['plate_z'].notna()
    ]
    if pitch_filter != 'All Pitches':
        loc_data = loc_data[loc_data['pitch_name'] == pitch_filter]

    fig4 = go.Figure(go.Histogram2dContour(
        x=loc_data['plate_x'], y=loc_data['plate_z'],
        colorscale=[
            [0, 'rgba(0,48,135,0)'], [0.3, BREWERS_NAVY],
            [0.7, BREWERS_GOLD], [1, '#ff4444']
        ],
        ncontours=20, showscale=False
    ))
    fig4.add_shape(
        type='rect', x0=-0.85, x1=0.85, y0=1.5, y1=3.5,
        line=dict(color='white', width=2)
    )
    fig4.add_shape(
        type='path',
        path='M -0.85 0.15 L 0.85 0.15 L 0.85 0 L 0 -0.2 L -0.85 0 Z',
        line=dict(color='white', width=1.5),
        fillcolor='rgba(255,255,255,0.1)'
    )
    fig4.update_layout(
        **base_layout(f'Pitch Location — {pitch_filter}', height=480),
        xaxis=ax('Horizontal (ft)', {'range': [-2.5, 2.5]}),
        yaxis=ax('Vertical (ft)', {
            'range': [-0.5, 5],
            'scaleanchor': 'x',
            'scaleratio': 1
        })
    )
    st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────
# PAGE 4 — Player Comparison
# ─────────────────────────────────────────
elif page == "📊  Player Comparison":
    st.title("📊 Player Comparison")

    comp_type = st.radio(
        "Compare", ["⚾ Batters", "🎯 Pitchers"], horizontal=True
    )

    if comp_type == "⚾ Batters":
        col1, col2 = st.columns(2)
        with col1:
            p1 = st.selectbox("Player 1", batter_names,
                              index=0, key='comp_b1')
        with col2:
            p2 = st.selectbox("Player 2", batter_names,
                              index=min(1, len(batter_names)-1),
                              key='comp_b2')

        s1 = get_batter_summary(batters, p1)
        s2 = get_batter_summary(batters, p2)
        p1_id = BATTER_IDS.get(p1)
        p2_id = BATTER_IDS.get(p2)

        st.divider()

        metrics = [
            ('Avg Exit Velocity', 'avg_ev', '{:.1f} mph', False),
            ('xBA', 'xba', '{:.3f}', False),
            ('xwOBA', 'xwoba', '{:.3f}', False),
            ('Hard Hit%', 'hard_hit_pct', '{:.1f}%', False),
            ('Barrel%', 'barrel_pct', '{:.1f}%', False),
            ('Whiff%', 'whiff_pct', '{:.1f}%', True),
        ]

        col1, col2 = st.columns(2)

        with col1:
            p1_url = get_headshot_url(p1_id) if p1_id else None
            photo = (
                f"<img src='{p1_url}' style='width:80px; border-radius:50%; "
                f"border:2px solid {BREWERS_GOLD};'/>"
                if p1_url else '👤'
            )
            st.markdown(
                f"<div style='text-align:center; background:{CARD_BG}; "
                f"border:2px solid {BREWERS_NAVY}; border-radius:12px; "
                f"padding:16px; margin-bottom:12px;'>{photo}"
                f"<div style='color:{BREWERS_GOLD}; font-weight:bold; "
                f"font-size:16px; margin-top:8px;'>🔵 {p1}</div></div>",
                unsafe_allow_html=True
            )
            for label, key, fmt, _ in metrics:
                stat_card(label, fmt.format(s1[key]))

        with col2:
            p2_url = get_headshot_url(p2_id) if p2_id else None
            photo2 = (
                f"<img src='{p2_url}' style='width:80px; border-radius:50%; "
                f"border:2px solid {BREWERS_NAVY};'/>"
                if p2_url else '👤'
            )
            st.markdown(
                f"<div style='text-align:center; background:{CARD_BG}; "
                f"border:2px solid {BREWERS_GOLD}; border-radius:12px; "
                f"padding:16px; margin-bottom:12px;'>{photo2}"
                f"<div style='color:{BREWERS_GOLD}; font-weight:bold; "
                f"font-size:16px; margin-top:8px;'>🟠 {p2}</div></div>",
                unsafe_allow_html=True
            )
            for label, key, fmt, inverse in metrics:
                delta = s2[key] - s1[key]
                better = delta > 0 if not inverse else delta < 0
                arrow = '▲' if delta > 0 else '▼'
                color = '#44ff44' if better else '#ff4444'
                fmt_val = fmt.format(s2[key])
                is_dec = 'xb' in key or 'xw' in key or 'xl' in key
                delta_str = f"{abs(delta):.3f}" if is_dec else f"{abs(delta):.1f}"
                st.markdown(
                    f"<div class='stat-card'>"
                    f"<div class='stat-card-title'>{label}</div>"
                    f"<div class='stat-card-value'>{fmt_val} "
                    f"<span style='font-size:14px; color:{color};'>"
                    f"{arrow} {delta_str}</span></div></div>",
                    unsafe_allow_html=True
                )

        st.divider()

        # Radar chart
        st.subheader("Percentile Radar Chart")
        all_s = [get_batter_summary(batters, n) for n in batter_names]
        all_df = pd.DataFrame(all_s)

        radar_metrics = [
            ('avg_ev', 'Exit Velo'), ('xba', 'xBA'),
            ('xwoba', 'xwOBA'), ('hard_hit_pct', 'Hard Hit%'),
            ('barrel_pct', 'Barrel%'),
        ]

        def pct_rank(val, col):
            series = all_df[col].dropna()
            return (series < val).sum() / len(series)

        vals1 = [pct_rank(s1[m], m) for m, _ in radar_metrics]
        vals2 = [pct_rank(s2[m], m) for m, _ in radar_metrics]
        labels = [l for _, l in radar_metrics]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=vals1 + [vals1[0]], theta=labels + [labels[0]],
            fill='toself', name=p1,
            line=dict(color=BREWERS_NAVY, width=2),
            fillcolor='rgba(0,48,135,0.25)'
        ))
        fig.add_trace(go.Scatterpolar(
            r=vals2 + [vals2[0]], theta=labels + [labels[0]],
            fill='toself', name=p2,
            line=dict(color=BREWERS_GOLD, width=2),
            fillcolor='rgba(182,146,46,0.25)'
        ))
        fig.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor=CARD_BG,
            font=dict(color='white', family='Georgia, serif'),
            polar=dict(
                bgcolor=CARD_BG,
                radialaxis=dict(
                    visible=True, range=[0,1],
                    tickvals=[0.25,0.5,0.75],
                    ticktext=['25th','50th','75th'],
                    tickfont=dict(color='#aaa', size=9),
                    gridcolor='#2a2f3e', linecolor='#2a2f3e'
                ),
                angularaxis=dict(
                    gridcolor='#2a2f3e', linecolor='#2a2f3e'
                )
            ),
            showlegend=True,
            legend=dict(
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                orientation='h', yanchor='bottom',
                y=-0.15, xanchor='center', x=0.5
            ),
            height=460,
            margin=dict(l=40, r=40, t=20, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

        # EV overlay
        st.subheader("Exit Velocity Distribution")
        p1_bat = batters[
            (batters['player_name'] == p1) & batters['launch_speed'].notna()
        ]
        p2_bat = batters[
            (batters['player_name'] == p2) & batters['launch_speed'].notna()
        ]
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=p1_bat['launch_speed'], name=p1, opacity=0.65, nbinsx=25,
            marker=dict(color=BREWERS_NAVY,
                        line=dict(color='white', width=0.3))
        ))
        fig2.add_trace(go.Histogram(
            x=p2_bat['launch_speed'], name=p2, opacity=0.65, nbinsx=25,
            marker=dict(color=BREWERS_GOLD,
                        line=dict(color='white', width=0.3))
        ))
        fig2.update_layout(
            **base_layout('', height=320, showlegend=True),
            barmode='overlay',
            xaxis=ax('Exit Velocity (mph)'),
            yaxis=ax('Count'),
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        )
        st.plotly_chart(fig2, use_container_width=True)

    else:  # Pitchers
        col1, col2 = st.columns(2)
        with col1:
            p1 = st.selectbox("Pitcher 1", pitcher_names,
                              index=0, key='comp_p1')
        with col2:
            p2 = st.selectbox("Pitcher 2", pitcher_names,
                              index=min(1, len(pitcher_names)-1),
                              key='comp_p2')

        s1 = get_pitcher_summary(pitchers, p1)
        s2 = get_pitcher_summary(pitchers, p2)
        p1_id = PITCHER_IDS.get(p1)
        p2_id = PITCHER_IDS.get(p2)

        st.divider()

        p_metrics = [
            ('Avg Velocity', 'avg_velo', '{:.1f} mph', False),
            ('Max Velocity', 'max_velo', '{:.1f} mph', False),
            ('Avg Spin Rate', 'avg_spin', '{:.0f} rpm', False),
            ('Whiff%', 'whiff_pct', '{:.1f}%', False),
            ('Strike%', 'strike_pct', '{:.1f}%', False),
        ]

        col1, col2 = st.columns(2)

        with col1:
            p1_url = get_headshot_url(p1_id) if p1_id else None
            photo = (
                f"<img src='{p1_url}' style='width:80px; border-radius:50%; "
                f"border:2px solid {BREWERS_GOLD};'/>"
                if p1_url else '👤'
            )
            st.markdown(
                f"<div style='text-align:center; background:{CARD_BG}; "
                f"border:2px solid {BREWERS_NAVY}; border-radius:12px; "
                f"padding:16px; margin-bottom:12px;'>{photo}"
                f"<div style='color:{BREWERS_GOLD}; font-weight:bold; "
                f"font-size:16px; margin-top:8px;'>🔵 {p1}</div></div>",
                unsafe_allow_html=True
            )
            for label, key, fmt, _ in p_metrics:
                stat_card(label, fmt.format(s1[key]))

        with col2:
            p2_url = get_headshot_url(p2_id) if p2_id else None
            photo2 = (
                f"<img src='{p2_url}' style='width:80px; border-radius:50%; "
                f"border:2px solid {BREWERS_NAVY};'/>"
                if p2_url else '👤'
            )
            st.markdown(
                f"<div style='text-align:center; background:{CARD_BG}; "
                f"border:2px solid {BREWERS_GOLD}; border-radius:12px; "
                f"padding:16px; margin-bottom:12px;'>{photo2}"
                f"<div style='color:{BREWERS_GOLD}; font-weight:bold; "
                f"font-size:16px; margin-top:8px;'>🟠 {p2}</div></div>",
                unsafe_allow_html=True
            )
            for label, key, fmt, _ in p_metrics:
                delta = s2[key] - s1[key]
                arrow = '▲' if delta > 0 else '▼'
                color = '#44ff44' if delta > 0 else '#ff4444'
                st.markdown(
                    f"<div class='stat-card'>"
                    f"<div class='stat-card-title'>{label}</div>"
                    f"<div class='stat-card-value'>{fmt.format(s2[key])} "
                    f"<span style='font-size:14px; color:{color};'>"
                    f"{arrow} {abs(delta):.1f}</span></div></div>",
                    unsafe_allow_html=True
                )

        st.divider()
        st.subheader("Pitch Arsenal Comparison")
        col1, col2 = st.columns(2)

        for col, player in [(col1, p1), (col2, p2)]:
            with col:
                pd_p = pitchers[pitchers['player_name'] == player]
                pc = pd_p['pitch_name'].value_counts()
                pc = pc[(pc.index != 'null') & (pc > 5)]
                fig = go.Figure(go.Pie(
                    labels=pc.index, values=pc.values, hole=0.45,
                    marker=dict(colors=CHART_COLORS[:len(pc)],
                                line=dict(color=DARK_BG, width=2)),
                    textfont=dict(color='white'),
                    textinfo='label+percent'
                ))
                fig.add_annotation(
                    text=player.split()[-1], x=0.5, y=0.5,
                    font=dict(size=12, color=BREWERS_GOLD),
                    showarrow=False
                )
                fig.update_layout(
                    **base_layout('', height=300),
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────
# Footer
# ─────────────────────────────────────────
st.markdown(
    "<div class='footer'>Data: Baseball Savant via pybaseball &nbsp;|&nbsp; "
    "Built with Streamlit + Plotly &nbsp;|&nbsp; "
    "github.com/PiotrWarchol &nbsp;|&nbsp; "
    "2024 Regular Season</div>",
    unsafe_allow_html=True
)