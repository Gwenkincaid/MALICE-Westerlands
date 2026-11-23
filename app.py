import io,re
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='MALICE | The Westerlands',page_icon='🐉',layout='wide',initial_sidebar_state='expanded')
GOLD='#c6a66a'; RED='#a73e3b'; BG='#101213'; PANEL='#1b1d1c'; INK='#e9dfc9'; MUTED='#a69b86'
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=EB+Garamond:wght@400;500;600&display=swap');
:root{color-scheme:dark}
.stApp,[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 75% 0%,#29241e 0%,#131616 46%,#0d1011 100%);color:#e9dfc9}
[data-testid="stHeader"]{background:rgba(15,17,18,.85)}
[data-testid="stSidebar"]{background:#151817;border-right:1px solid #655338}
[data-testid="stSidebar"] *{color:#d8c9aa}
.block-container{padding-top:2rem;max-width:1450px}
h1,h2,h3{font-family:'Cinzel',Georgia,serif!important;color:#d6b77a!important;letter-spacing:.06em}
h1{font-size:clamp(2rem,4vw,3.8rem)!important;text-shadow:0 2px 18px #000}
h2,h3{border-bottom:1px solid #67563c;padding-bottom:.55rem}
p,label,div{font-family:'EB Garamond',Georgia,serif;font-size:1.09rem}
[data-testid="stMetric"]{background:linear-gradient(145deg,#292722,#191c1c);border:1px solid #6e5736;border-top:2px solid #b99a60;border-radius:3px;padding:18px;box-shadow:0 8px 24px #0005}
[data-testid="stMetricLabel"]{color:#c8b58d!important}
[data-testid="stMetricValue"]{color:#f0dfb6!important;font-family:'Cinzel',serif;font-size:clamp(1.1rem,2vw,1.7rem)}
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"]{border:1px solid #4c4234;border-radius:3px;background:#171b1b}
[data-baseweb="select"]>div,[data-baseweb="input"]>div{background:#242725!important;border:1px solid #786344!important;color:#f0dfb6!important}
[data-testid="stFileUploader"]{border:1px dashed #7e6541}
[data-testid="stAlert"]{background:#24251f;color:#e5d7b8}
hr{border-color:#685436}
.banner{background:linear-gradient(90deg,#1d211f 0%,#29251e 65%,#351c1b 100%);border:1px solid #7b623e;border-left:5px solid #a43e37;padding:22px 28px;margin:0 0 24px;box-shadow:0 12px 30px #0006}
.banner .eyebrow{font-family:'Cinzel',serif;font-size:.85rem;letter-spacing:.32em;color:#bb9b63}
.banner .subtitle{font-family:'EB Garamond',serif;color:#c2b49c;font-size:1.2rem}
[data-testid="stMultiSelect"] span{color:#ead9b6!important}
</style>''',unsafe_allow_html=True)

@st.cache_data
def read_data(raw):
    df=pd.read_excel(io.BytesIO(raw),sheet_name='Player Progress',header=0)
    df=df.rename(columns={df.columns[0]:'Player'})
    df=df[df.Player.notna()].copy();df['Player']=df.Player.astype(str).str.strip()
    df=df[(df.Player!='') & (df.Player.str.lower()!='nan')]
    records=[]
    for col in df.columns[1:]:
        label=str(col);match=re.fullmatch(r'Day\s*(\d+)(?:\s*\([^)]*\))?',label.strip(),re.I)
        if not match:continue
        day=int(match.group(1))
        date_match=re.search(r'(\d{1,2}/\d{1,2}/\d{4})',label)
        date=pd.to_datetime(date_match.group(1),errors='coerce') if date_match else pd.NaT
        values=pd.to_numeric(df[col].astype(str).str.replace(',','',regex=False),errors='coerce')
        for name,power in zip(df.Player,values):
            if pd.notna(power) and power>0:records.append((name,day,date,int(power)))
    out=pd.DataFrame(records,columns=['Player','Day','Date','Power'])
    if out.empty:return out
    try:
        overview=pd.read_excel(io.BytesIO(raw),sheet_name='Overview',header=2)
        date_map={}
        for _, row in overview.iterrows():
            match=re.fullmatch(r'Day\s*(\d+)',str(row.iloc[0]).strip(),re.I)
            if match:
                dt=pd.to_datetime(row.iloc[1],errors='coerce')
                if pd.notna(dt):date_map[int(match.group(1))]=dt
        for day,dt in date_map.items():
            out.loc[(out.Day==day)&(out.Date.isna()),'Date']=dt
    except Exception:
        pass
    # Alliance Power is a summary row, never an individual warrior.
    # Excluding it here automatically fixes rankings, charts, counts and gains.
    out=out[~out['Player'].str.fullmatch(r'Alliance\s+Power',case=False,na=False)].copy()
    out=out.drop_duplicates(['Player','Day'],keep='last')
    # Ignore template columns with only a stray value; real reports contain multiple members.
    valid=out.groupby('Day').Player.nunique();out=out[out.Day.isin(valid[valid>=2].index)]
    return out.sort_values(['Player','Day'])

def themed(fig,height=390):
    fig.update_layout(height=height,paper_bgcolor='#171b1b',plot_bgcolor='#171b1b',font=dict(color=INK,family='Georgia'),title_font=dict(color=GOLD),legend=dict(bgcolor='rgba(0,0,0,0)',font=dict(color=INK)),margin=dict(l=25,r=25,t=25,b=30),hoverlabel=dict(bgcolor='#282923',font_color=INK,bordercolor=GOLD))
    fig.update_xaxes(gridcolor='#37352f',zerolinecolor='#37352f',linecolor='#776448',tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor='#37352f',zerolinecolor='#37352f',linecolor='#776448',tickfont=dict(color=MUTED))
    return fig

# --- Private War Council entrance ---
# Set WAR_COUNCIL_PASSWORD in Streamlit Community Cloud > App settings > Secrets.
# Never commit the password to GitHub.
import hmac

def require_war_council_access():
    try:
        expected = st.secrets.get("WAR_COUNCIL_PASSWORD", "")
    except Exception:
        expected = ""

    if not expected:
        st.error("The gates are not configured. The app owner must add WAR_COUNCIL_PASSWORD to Streamlit Secrets.")
        st.stop()

    if st.session_state.get("war_council_authenticated", False):
        with st.sidebar:
            if st.button("🚪 Leave the War Council", use_container_width=True):
                st.session_state["war_council_authenticated"] = False
                st.rerun()
        return

    st.markdown("""
    <div class="banner" style="text-align:center;max-width:760px;margin:6vh auto 24px">
      <div class="eyebrow">MALICE · ALLIANCE INTELLIGENCE</div>
      <h1>🛡️ THE GATES OF THE REALM</h1>
      <div class="subtitle">Only those sworn to MALICE may enter.</div>
    </div>
    """, unsafe_allow_html=True)
    _, center, _ = st.columns([1, 2, 1])
    with center:
        with st.form("war_council_login", clear_on_submit=False):
            password = st.text_input("The alliance passphrase", type="password",
                                     placeholder="Speak the words of entry")
            submitted = st.form_submit_button("⚔️ Enter the War Council", use_container_width=True)
        if submitted:
            if hmac.compare_digest(password.encode("utf-8"), str(expected).encode("utf-8")):
                st.session_state["war_council_authenticated"] = True
                st.rerun()
            else:
                st.error("The gates remain closed. Incorrect passphrase.")
    st.stop()

require_war_council_access()

with st.sidebar:
    st.markdown('## ⚔️ THE ARCHIVES')
    st.caption('MALICE · ALLIANCE INTELLIGENCE')
    uploaded=st.file_uploader('Load a new Excel ledger',type=['xlsx'])
    st.caption('An uploaded file updates only your current session. To update the public dashboard, replace progress.xlsx in GitHub.')
    st.divider()
    st.markdown('**THE CODE OF THE REALM**')
    st.caption('Missing days remain missing. Power gains are absolute values, not percentages. Player names must match between reports.')

try:raw=uploaded.getvalue() if uploaded else Path(__file__).with_name('progress.xlsx').read_bytes();data=read_data(raw)
except Exception as exc:st.error(f'Unable to read the Player Progress sheet: {exc}');st.stop()
if data.empty:st.error('No completed daily reports found in Player Progress.');st.stop()
# Only actual Day columns are read; computed ranks and growth columns are never snapshots.
if data.duplicated(['Player','Day']).any():
    st.error('Duplicate member/day values detected. Please review the Excel ledger.');st.stop()
days=sorted(data.Day.unique());latest_day=days[-1];prior_day=days[-2] if len(days)>1 else None
latest=data[data.Day==latest_day].set_index('Player').Power
prior=data[data.Day==prior_day].set_index('Player').Power if prior_day is not None else pd.Series(dtype=float)
shared=latest.index.intersection(prior.index);gains=(latest.loc[shared]-prior.loc[shared]).sort_values(ascending=False)
report_date=data.loc[data.Day==latest_day,'Date'].dropna()
date_label=report_date.iloc[0].strftime('%B %d, %Y') if len(report_date) else f'Day {latest_day}'
st.markdown('<div class="banner"><div class="eyebrow">THE WESTERLANDS · POWER & CONQUEST</div><h1>🦁 MALICE</h1><div class="subtitle">Hear me roar. &nbsp;✦&nbsp; Alliance intelligence and the chronicles of power.</div></div>',unsafe_allow_html=True)
metrics=st.columns(4)
for col,label,val in zip(metrics,['LATEST CHRONICLE','WARRIORS COUNTED','POWER OF THE REALM','POWER GAINED'],[f'Day {latest_day}',f'{len(latest):,}',f'{latest.sum():,}',f'{gains.sum():+,}' if len(gains) else '—']):col.metric(label,val)
st.caption(f'Latest recorded report: {date_label} · Gains compare Day {prior_day} with Day {latest_day}' if prior_day else f'Baseline snapshot: November 23, 2026 · Day {latest_day}')
st.markdown('### ⚔️ Rise of the Dragons')
players=sorted(data.Player.unique(),key=str.casefold)
default=[p for p in ['Power','Daybed','warian'] if p in players] or players[:2]
selected=st.multiselect('Choose warriors to compare',players,default=default)
if selected:
    view=data[data.Player.isin(selected)]
    fig=px.line(view,x='Day',y='Power',color='Player',markers=True,color_discrete_sequence=['#d2ae68','#ad4b44','#a9b0ac','#866f50','#a97c67','#d7c8a4','#6d8b85'])
    fig.update_traces(line_width=3,marker_size=8)
    fig.update_xaxes(tickmode='array',tickvals=days,ticktext=[f'Day {x}' for x in days],title=None)
    fig.update_yaxes(title='Power')
    st.plotly_chart(themed(fig,430),use_container_width=True)
else:st.info('Choose a warrior to view their power history.')
left,right=st.columns([1,1])
with left:
    st.markdown('### ♛ The Great Houses')
    leaders=latest.sort_values(ascending=False).rename('Power').reset_index();leaders.insert(0,'Rank',range(1,len(leaders)+1))
    st.dataframe(leaders,hide_index=True,use_container_width=True,height=480,column_config={'Power':st.column_config.NumberColumn(format='%d')})
with right:
    st.markdown('### 🔥 The Conquest Ledger')
    if len(gains):
        top=gains.head(15).sort_values()
        fig=go.Figure(go.Bar(x=top.values,y=top.index,orientation='h',marker=dict(color=[RED if v<0 else GOLD for v in top.values],line=dict(color='#66563b',width=.5)),hovertemplate='%{y}<br>Power gained: %{x:+,}<extra></extra>'))
        fig.update_xaxes(title='Power gained')
        st.plotly_chart(themed(fig,480),use_container_width=True)
    else:st.info('At least two matching reports are needed for gains.')
st.markdown('### 🗺️ The Campaign Map · Daily Gains')
wide=data.pivot(index='Player',columns='Day',values='Power').reindex(columns=days)
if len(days)>1:
    delta=wide.diff(axis=1)
    for i in range(1,len(days)):
        delta.loc[wide[days[i-1]].isna()|wide[days[i]].isna(),days[i]]=float('nan')
    delta=delta.reindex(latest.sort_values(ascending=False).index)
    fig=go.Figure(go.Heatmap(z=delta.values,x=[f'Day {d}' for d in days],y=delta.index,colorscale=[[0,'#272827'],[.3,'#6d5139'],[.7,'#ad7d46'],[1,'#ead2a0']],hovertemplate='%{y}<br>%{x}<br>Gain: %{z:+,.0f}<extra></extra>',colorbar=dict(title='Gain',tickfont=dict(color=INK)),hoverongaps=False))
    fig.update_yaxes(autorange='reversed')
    st.plotly_chart(themed(fig,max(490,len(delta)*22)),use_container_width=True)
else:st.info('The campaign map appears once a second report is available.')
st.markdown('### 📜 The Hall of Records · Rank Movement')
if prior_day is not None:
    rank_now=latest.rank(ascending=False,method='min').astype(int);rank_prior=prior.rank(ascending=False,method='min').astype(int)
    common=rank_now.index.intersection(rank_prior.index)
    movement=pd.DataFrame({'Warrior':common,'Previous rank':rank_prior.loc[common].values,'Current rank':rank_now.loc[common].values})
    movement['Places gained']=movement['Previous rank']-movement['Current rank']
    st.dataframe(movement.sort_values('Current rank'),hide_index=True,use_container_width=True)
else:st.info('Rank changes require two reports.')
st.caption('THE MAESTERS’ NOTE · Alliance Power is calculated from recorded warriors and excluded from individual rankings. Missing reports are never filled with zero. Names are matched exactly. Gains are not adjusted for unequal reporting intervals.')
