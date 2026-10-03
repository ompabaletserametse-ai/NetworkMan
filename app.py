import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import issues
import maintenance
import json
import math
from html import escape
from pathlib import Path
from statistics import mean
from model import PROVINCES, SCENARIOS, fresh_state, site_list, trigger, advance, act, plan, paused, now, audit, ticket_update, series

st.set_page_config(page_title='NOC · Network operations', page_icon='◈', layout='wide', initial_sidebar_state='expanded')
CSS='''
<style>
:root {
  --bg: #f5f1ee;
  --panel: #ffffff;
  --panel-soft: #faf7f4;
  --ink: #2e2724;
  --muted: #685d57;
  --line: #e7dfd9;
  --brand: #6c4d3d;
  --brand-soft: #f0e6df;
  --brand-strong: #3d2c26;
  --green: #2e7d5a;
  --amber: #b77d28;
  --red: #b94d41;
  --shadow: 0 10px 22px rgba(57, 39, 30, 0.05);
}

.stApp {
  background: linear-gradient(180deg, #f5f1ee 0%, #f8f4f2 100%);
  color: var(--ink);
  --text-color: var(--ink);
  --background-color: var(--bg);
  --secondary-background-color: var(--panel);
  --primary-color: var(--brand);
  color-scheme: light;
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #3f302b 0%, #2e2724 100%);
  min-width: 240px;
  max-width: 240px;
  border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] * { color: #f9f3ef; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 1.1rem 1rem; }
[data-testid="stSidebar"] button {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 10px !important;
  text-align: left;
  margin-bottom: 0.35rem;
  transition: all .15s ease;
}
[data-testid="stSidebar"] button:hover { background: rgba(255,255,255,0.08); }
[data-testid="stSidebar"] button[kind="primary"] {
  background: var(--brand-soft) !important;
  color: var(--brand-strong) !important;
  border-color: transparent !important;
}

.block-container {
  padding: 0.8rem 1.3rem 0.9rem;
  max-width: 1800px;
}
[data-testid="stVerticalBlock"] { gap: 0.45rem; }
[data-testid="stHorizontalBlock"] { gap: 0.75rem; }
[data-testid="stForm"] { padding: 0.6rem; border-radius: 12px; }
[data-testid="stMetric"] {
  background: var(--panel) !important;
  border: 1px solid var(--line);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 10px 12px;
}
[data-testid="stMetricValue"] { font-size: 1.55rem; }
[data-testid="stMetricLabel"] { font-size: .76rem; color: var(--muted) !important; }

h1 {
  font-size: 2rem !important;
  letter-spacing: -0.7px;
  margin: 0.1rem 0 0.2rem !important;
}
h2 {
  font-size: 1.25rem !important;
  margin: 0.15rem 0 0.2rem !important;
}
h3 {
  font-size: 1.02rem !important;
  margin: 0.12rem 0 0.18rem !important;
}

.eyebrow {
  color: var(--brand);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2.2px;
  margin-bottom: 0.08rem;
  text-transform: uppercase;
}
.subtle { color: var(--muted); font-size: 12px; }
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: #efe7e2;
  color: var(--brand-strong);
}
.good { background: #e5f1eb; color: var(--green); }
.warn { background: #fdf0d8; color: var(--amber); }
.bad { background: #f8e0de; color: var(--red); }
.muted { background: #ece7e3; color: var(--muted); }

.grid-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
}
.grid-table th {
  text-align: left;
  font-size: 10px;
  letter-spacing: .6px;
  text-transform: uppercase;
  color: var(--muted);
  background: var(--panel-soft);
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
}
.grid-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
.small-table td { padding: 6px 8px; }
.rowtext { padding: 0.25rem 0; font-size: 13px; }

button {
  border-radius: 10px !important;
  transition: transform .1s ease, box-shadow .1s ease;
}
button:hover { transform: translateY(-1px); }
[data-testid="stMain"] button {
  background: #fff !important;
  color: var(--ink) !important;
  border: 1px solid #c9b9ae !important;
}
[data-testid="stMain"] button[kind="primary"] {
  background: var(--brand) !important;
  color: #fff !important;
  border-color: var(--brand) !important;
}
[data-testid="stMain"] button:disabled {
  background: #f1ece9 !important;
  color: #766d69 !important;
  opacity: 1 !important;
}

[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMain"] [data-testid="stForm"],
[data-testid="stMain"] [data-testid="stAlert"] {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  box-shadow: var(--shadow);
}

[data-testid="stMain"] .stAlert {
  background: var(--panel) !important;
  border: 1px solid var(--line) !important;
  color: var(--ink) !important;
}

[data-testid="stMain"] input,
[data-testid="stMain"] textarea,
[data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="input"] {
  background: #fff !important;
  color: var(--ink) !important;
  border-radius: 9px !important;
}
[data-baseweb="popover"] *, [role="option"] { color: var(--ink) !important; }
[role="option"]:hover, [aria-selected="true"][role="option"] { background: #efe5df !important; }

[data-testid="stSidebar"] .stCaptionContainer, [data-testid="stSidebar"] .stCaptionContainer * { color: #f5eee8 !important; }
[data-testid="stMain"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] .subtle,
[data-testid="stMain"] .grid-table th { color: var(--muted) !important; }
[data-testid="stMain"] svg { color: inherit; }
</style>'''
st.markdown(CSS,unsafe_allow_html=True)
ss=st.session_state
if 'model' not in ss: ss.model=fresh_state()
if 'route' not in ss: ss.route=st.query_params.get('view','Overview')
if 'province' not in ss: ss.province='All provinces'
if 'site' not in ss: ss.site='GT-03'
if 'device' not in ss: ss.device='GT-03-RTR'
if 'incident' not in ss: ss.incident='INC-1001'
if 'engineer' not in ss: ss.engineer='Demo engineer'
if 'pending_context' in ss:
 for k,v in ss.pop('pending_context').items():ss[k]=v
s=ss.model
maintenance.ensure(s)
PRIMARY_PAGES=['Overview','Tickets']
SECONDARY_PAGES=['Issues & Response','Network Performance','Device Health','Incidents','Maintenance','Reports']
PAGES=PRIMARY_PAGES+SECONDARY_PAGES
EXTRA=['Maintenance case','Technician findings','Maintenance watch','Preventive order','Issue detail','Issue analysis','Issue recommendation','Issue result','Sites','Link detail','Device detail','Incident detail','Recovery','Ticket detail','Audit','Demo controls']
if ss.route not in PAGES+EXTRA:ss.route='Overview'

def go(page,**values):
 ss.route=page
 for k,v in values.items():ss[k]=v
 st.query_params['view']=page


def cmd(command,iid=None,**kwargs):
 if act(s,s['incidents'][iid or ss.incident],command,ss.engineer,**kwargs):ss.notice='Action recorded.'
 else:ss.notice='Action blocked: check state, approval, capacity, pause, or stability requirements.'


def reset():
 ss.model=fresh_state();ss.route='Overview';ss.province='All provinces';ss.site='GT-03';ss.incident='INC-1001';ss.device='GT-03-RTR'
 for k in list(ss):
  if k.startswith('pg_'):del ss[k]
 st.query_params['view']='Overview'


def badge(text):
 cls='good' if text in ['Healthy','Online','Resolved','Closed','Available'] else 'bad' if text in ['Critical','Unavailable','Offline'] else 'muted' if text in ['Unknown','Stale','Unassigned'] else 'warn'
 return f'<span class="badge {cls}">{escape(str(text))}</span>'


def table(rows,small=False):
 if not rows:st.caption('No matching records.');return
 keys=list(rows[0]);html='<table class="grid-table '+('small-table' if small else '')+'"><thead><tr>'+''.join(f'<th>{escape(k)}</th>' for k in keys)+'</tr></thead><tbody>'
 for row in rows:html+='<tr>'+''.join(f'<td>{escape(str(row[k]))}</td>' for k in keys)+'</tr>'
 st.markdown(html+'</tbody></table>',unsafe_allow_html=True)


def metrics(items):
 for col,(label,value,helptext) in zip(st.columns(len(items)),items):
  col.metric(label,value,help=helptext or None)


def heading(title,subtitle=''):
 st.markdown('<div class="eyebrow">NETWORK OPERATIONS CENTRE</div>',unsafe_allow_html=True)
 st.title(title)
 if subtitle:st.caption(subtitle)
 st.markdown('<div style="height: 0.2rem"></div>',unsafe_allow_html=True)


def paginate(rows,key,size=6):
 pages=max(1,math.ceil(len(rows)/size));k='pg_'+key
 ss[k]=min(ss.get(k,0),pages-1)
 a,b,c=st.columns([1,3,1])
 if a.button('← Previous',key=k+'prev',disabled=ss[k]==0):ss[k]-=1;st.rerun()
 b.caption(f'Page {ss[k]+1} of {pages} · {len(rows)} records')
 if c.button('Next →',key=k+'next',disabled=ss[k]>=pages-1):ss[k]+=1;st.rerun()
 return rows[ss[k]*size:(ss[k]+1)*size]


def selected_sites():return site_list(s,ss.province)

def valid_links():return [s['links'][x['id']] for x in selected_sites() if s['links'][x['id']]['fresh'] and s['links'][x['id']]['up']]

def fmt(value,unit='',digits=1):return 'No reading' if value is None else f'{value:.{digits}f}{unit}'


def network_downtime_label():
 total=0
 for incident in s['incidents'].values():
  start=incident.get('start')
  if start is None: continue
  end=incident.get('resolved', s['minute'])
  total += max(0, end - start)
 if total < 60: return f'{total} min'
 hours, mins = divmod(total, 60)
 return f'{hours}h {mins}m' if hours else f'{mins}m'


def chart(points,label,height=235,threshold=None):
 from plotly import graph_objects as pg
 f=pg.Figure(pg.Scatter(x=[x[0] for x in points],y=[x[1] for x in points],mode='lines+markers',line=dict(color='#8a6347',width=2),marker=dict(size=4),connectgaps=False))
 if threshold is not None:f.add_hline(y=threshold,line_dash='dot',line_color='#b58324',annotation_text='Demo threshold')
 f.update_layout(height=height,margin=dict(l=35,r=10,t=10,b=35),paper_bgcolor='#fff',plot_bgcolor='#fff',font=dict(color='#514137',size=12),xaxis_title='Simulation minute',yaxis_title=label,showlegend=False)
 f.update_xaxes(gridcolor='#f0ece7');f.update_yaxes(gridcolor='#f0ece7')
 st.plotly_chart(f,width='stretch',config={'displayModeBar':False})


@st.cache_data
def boundaries():
 p=Path(__file__).with_name('provinces.geojson')
 return json.loads(p.read_text()) if p.exists() else None


def map_view(rows,height=400):
 from plotly import graph_objects as pg
 f=pg.Figure();geo=boundaries()
 if geo:
  for feature in geo['features']:
   geom=feature['geometry'];polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
   for poly in polys:
    outer=poly[0]
    f.add_trace(pg.Scatter(x=[p[0] for p in outer],y=[p[1] for p in outer],mode='lines',fill='toself',fillcolor='#e8e3dc',line=dict(color='#b9aaa0',width=.7),hoverinfo='skip',showlegend=False))
 colours={'Healthy':'#3c8864','Degraded':'#bd8b26','Unavailable':'#b7493f','Stale':'#8d8580'}
 for status,color in colours.items():
  pts=[x for x in rows if ('Stale' if not x['fresh'] else x['status'])==status]
  if not pts:continue
  f.add_trace(pg.Scatter(x=[x['lon'] for x in pts],y=[x['lat'] for x in pts],mode='markers',name=status,marker=dict(color=color,size=10,line=dict(color='white',width=1)),text=[f"{x['id']} · {x['name']}<br>{status}<br>{x['affected']:,} affected customers" for x in pts],customdata=[x['id'] for x in pts],hovertemplate='%{text}<extra></extra>'))
 if rows and ss.province!='All provinces':
  xs=[x['lon'] for x in rows];ys=[x['lat'] for x in rows];pad=max(.18,(max(xs)-min(xs))*.15)
  f.update_xaxes(range=[min(xs)-pad,max(xs)+pad]);f.update_yaxes(range=[min(ys)-pad,max(ys)+pad])
 else:f.update_xaxes(range=[15.5,33.5]);f.update_yaxes(range=[-35.5,-21.5])
 f.update_layout(height=height,margin=dict(l=0,r=0,t=0,b=15),paper_bgcolor='#fff',plot_bgcolor='#fff',legend=dict(orientation='h',y=0,x=0,font=dict(size=11)),clickmode='event+select')
 f.update_xaxes(visible=False);f.update_yaxes(visible=False,scaleanchor='x',scaleratio=1.15)
 event=st.plotly_chart(f,width='stretch',key='site_map',on_select='rerun',selection_mode='points',config={'displayModeBar':False})
 if event.selection.points:
  sid=event.selection.points[0].get('customdata')
  if sid in s['sites']:
   ss.pending_context=dict(route='Device Health',site=sid,province=s['sites'][sid]['province']);st.query_params['view']='Device Health';st.rerun()


def inc_rows():
 return [i for i in s['incidents'].values() if ss.province=='All provinces' or s['sites'][i['site']]['province']==ss.province]


def event_rows(iid=None):
 return [dict(Time=e['time'],Actor=e['actor'],Event=e['event']) for e in reversed(s['audit']) if iid is None or e['incident']==iid]


def open_issue(kind):
 ss.issue_kind=kind
 rows=issues.affected(s,kind,ss.province)
 if rows:
  ss.site=rows[0]['site'];ss.incident=rows[0]['incident'] or ''
 else:ss.incident=''
 go('Issue detail')


def start_issue_demo(kind):
 i=issues.ensure_demo(s,kind)
 go('Issue detail',issue_kind=kind,incident=i['id'],site=i['site'],province=s['sites'][i['site']]['province'])


def issue_action(command):
 i=s['incidents'].get(ss.incident)
 if not i:return
 kind=ss.get('issue_kind','Congestion');ok=False
 if command=='analyse':
  ok=issues.analyse(s,i,kind,ss.engineer)
  if ok:go('Issue analysis')
 elif command=='review':
  ok=issues.review(s,i,ss.engineer)
  if ok:go('Issue recommendation')
 elif command=='approve':
  ok=issues.approve(s,i,ss.engineer)
  if ok:go('Issue result')
 elif command=='execute':ok=issues.execute(s,i)
 elif command=='verify':ok=issues.verify(s,i,ss.engineer)
 if not ok:ss.notice='Step blocked: check telemetry, approval, capacity, pause status, or verification results.'


def load_fibre():
 trigger(s,'Fibre damage')
 i=next(i for i in reversed(list(s['incidents'].values())) if i['scenario']=='Fibre damage')
 go('Maintenance case',incident=i['id'],site=i['site'],province=s['sites'][i['site']]['province'])


def maintenance_tests():
 i=s['incidents'][ss.incident]
 ss.notice='Post-repair tests passed.' if maintenance.field_tests(s,i) else 'Tests failed or repair has not been recorded.'


with st.sidebar:
 st.markdown('## ◈ NOC')
 st.caption('Observe · Understand · Recover')
 st.divider()
 for page in PRIMARY_PAGES:
  st.button(page,key='nav_'+page,width='stretch',use_container_width=True,type='primary' if ss.route==page else 'secondary',on_click=go,args=(page,))
 st.divider()
 st.button('Demo controls',width='stretch',use_container_width=True,on_click=go,args=('Demo controls',))
 st.caption(f'SIMULATION CLOCK · {now(s)} SAST')
 st.button('Advance +5 minutes',width='stretch',use_container_width=True,on_click=advance,args=(s,))
 if s['stop']:
  st.error('Emergency stop active')
 else:
  st.caption('Session-local simulated operations')
 st.caption('All values and AI outputs are illustrative.')

# Shared widgets render on every view, retaining context across navigation.
a,b=st.columns([2,3])
a.selectbox('Province',['All provinces']+list(PROVINCES),key='province')
options=[x['id'] for x in selected_sites()]
if ss.site not in options:ss.site=options[0]
b.markdown(f'<div style="padding-top:31px;text-align:right"><span class="badge">SIMULATED DATA</span> <span class="subtle">{now(s)} SAST</span></div>',unsafe_allow_html=True)
if ss.get('notice'):
 st.caption(ss.pop('notice'))
route=ss.route

if route=='Overview':
 rows=selected_sites();active=[i for i in inc_rows() if i['state']!='Resolved']
 heading('Network overview',ss.province+' · Select a map marker to inspect its equipment')
 metrics([('Sites available',f"{sum(x['status']!='Unavailable' and x['fresh'] for x in rows)} / {len(rows)}",'Current reachable sites; stale sites excluded from numerator.'),('Degraded sites',sum(x['status']=='Degraded' for x in rows),''),('Network downtime',network_downtime_label(),'Unplanned downtime across the simulated 24h window from incident durations.'),('Active incidents',len(active),''),('Affected customers',f"{sum(x['affected'] for x in rows):,}",'Fictional non-overlapping customer groups.')])
 left,right=st.columns([1.6,1])
 with left:
  with st.container(border=True):
   st.subheader('Geographic health');map_view(rows,340)
   st.caption('Boundaries: geoBoundaries / OCHA ROSEA / South African Municipal Demarcation Board · CC BY 3.0 IGO')
 with right:
  with st.container(border=True):
   st.subheader('Provincial health')
   table([{'Province':p,'Available':f"{sum(x['fresh'] and x['status']!='Unavailable' for x in site_list(s,p))}/8",'Affected':sum(x['affected'] for x in site_list(s,p))} for p in PROVINCES],small=True)
 a,b=st.columns([4,1]);a.subheader('Priority incidents');b.button('All incidents →',on_click=go,args=('Incidents',))
 table([{'Incident':i['id'],'Issue':i['title'],'Site':i['site'],'Severity':i['severity'],'Customers':s['sites'][i['site']]['affected'],'State':i['state']} for i in sorted(active,key=lambda i:-s['sites'][i['site']]['affected'])[:2]],small=True)
 st.button('Search all sites →',on_click=go,args=('Sites',))

elif route=='Sites':
 heading('Site directory','Search and filter sites; open equipment on a dedicated page')
 a,b,c,d=st.columns(4)
 query=a.text_input('Search name / ID').lower();technology=b.selectbox('Technology',['All','4G','5G']);status=c.selectbox('Condition',['All','Healthy','Degraded','Unavailable','Stale']);impact=d.selectbox('Customer impact',['All','Affected customers only'])
 rows=[x for x in selected_sites() if (query in x['name'].lower() or query in x['id'].lower()) and (technology=='All' or technology==x['technology']) and (status=='All' or (status=='Stale' and not x['fresh']) or status==x['status']) and (impact=='All' or x['affected']>0)]
 for x in paginate(rows,'sites',7):
  a,b,c,d=st.columns([3,2,2,1]);a.write(f"**{x['id']} · {x['name']}**");b.write(x['technology']+' · '+('Stale' if not x['fresh'] else x['status']));c.write(f"{x['affected']:,} affected");d.button('Open →',key='site_'+x['id'],on_click=go,args=('Device Health',),kwargs={'site':x['id']})

elif route=='Network Performance':
 heading('Network performance',ss.province+' · Transport links; CPU is shown under Device Health')
 links=valid_links();coverage=f'{len(links)}/{len(selected_sites())} fresh, available links';avg=lambda k:fmt(mean(x[k] for x in links)) if links else '—'
 metrics([('Latency',avg('latency')+' ms','Arithmetic mean; '+coverage),('Packet loss',avg('loss')+'%','Arithmetic mean of link percentages; '+coverage),('Traffic',fmt(sum(x['traffic'] for x in links)/1000,' Gbps'),'Sum of sampled primary links; not unique end-to-end traffic.'),('Link utilisation',fmt(100*sum(x['traffic'] for x in links)/sum(x['capacity'] for x in links),'%') if links else '—','Capacity-weighted; '+coverage)])
 st.caption(coverage+' · Select a site above to change the plotted link.')
 a,b=st.columns(2)
 with a:st.subheader(f'{ss.site} · Latency');chart(series(s,ss.site,'latency'),'ms',210,100)
 with b:st.subheader(f'{ss.site} · Packet loss');chart(series(s,ss.site,'loss'),'%',210,2)
 st.subheader('Transport links')
 rows=[s['links'][x['id']] for x in selected_sites()]
 for x in paginate(rows,'links',4):
  a,b,c,d=st.columns([3,2,2,1]);a.write(f"**{x['id']} → {x['endpoint']}**");b.write('Stale' if not x['fresh'] else f"{fmt(x['latency'],' ms')} · {fmt(x['loss'],'% loss')}");c.write(f"{x['traffic']:.0f}/{x['capacity']} Mbps");d.button('Inspect →',key=x['id'],on_click=go,args=('Link detail',),kwargs={'site':x['site']})

elif route=='Link detail':
 l=s['links'][ss.site];heading(l['id']+' · Link detail',f"{ss.site} → {l['endpoint']} · Fictional alternate transport topology")
 st.button('← Network performance',on_click=go,args=('Network Performance',))
 if 'physical_up' in l:st.caption('Effective service path shown below. Original physical fibre: '+('UP' if l['physical_up'] else 'DOWN — field repair outstanding'))
 metrics([('State','Stale' if not l['fresh'] else 'Up' if l['up'] else 'Down',''),('Traffic',fmt(l['traffic'],' Mbps'),''),('Capacity',f"{l['capacity']} Mbps",''),('Interface error rate',fmt(l['error'],'%'),'% of observed frames with interface errors; simulated.')])
 a,b=st.columns(2)
 with a:st.subheader('Traffic history');chart(series(s,ss.site,'traffic'),'Mbps',250)
 with b:st.subheader('Interface errors');chart(series(s,ss.site,'error'),'%',250)
 for i in inc_rows():
  if i['site']==ss.site:st.button(i['id']+' · '+i['title'],on_click=go,args=('Incident detail',),kwargs={'incident':i['id']})

elif route=='Device Health':
 site=s['sites'][ss.site];devices=[d for d in s['equipment'].values() if d['site']==ss.site]
 heading('Site equipment',site['name']+' · '+ss.site+' · Each equipment item opens a separate page')
 metrics([('Equipment online',f"{sum(d['online'] and d['fresh'] for d in devices)} / 7",'Stale telemetry is not counted as confirmed online.'),('Warnings',sum(d['status']!='Healthy' for d in devices),''),('Mains power','Available' if site['mains'] else 'Failed',''),('Battery charge',fmt(site['charge'],'%',0),'')])
 cols=st.columns([3,1.1,1.5,2,1.2])
 for col,label in zip(cols,['EQUIPMENT','GROUP','STATUS','KEY READING','ACTION']):col.caption(label)
 for d in devices:
  a,b,c,e,f=st.columns([3,1.1,1.5,2,1.2])
  a.markdown(f'<div class="rowtext"><b>{escape(d["label"])}</b><br><span class="subtle">{d["id"]}</span></div>',unsafe_allow_html=True)
  b.markdown('<div class="rowtext">'+d['group']+'</div>',unsafe_allow_html=True)
  c.markdown(badge('Stale' if not d['fresh'] else d['status']),unsafe_allow_html=True)
  e.write(d['metric']+' · '+(fmt(d['value'],d['unit']) if d['fresh'] else 'Stale'))
  f.button('Open device →',key=d['id'],on_click=go,args=('Device detail',),kwargs={'device':d['id']})
 st.caption('7 equipment items · Simulated configuration: one baseband, three radio sectors, router, rectifier and battery.')

elif route=='Device detail':
 if ss.device not in s['equipment'] or s['equipment'][ss.device]['site']!=ss.site:ss.device=ss.site+'-RTR'
 d=s['equipment'][ss.device];heading(d['label'],d['id']+' · '+s['sites'][d['site']]['name'])
 st.button('← Site equipment',on_click=go,args=('Device Health',))
 extra=('Memory usage',f"{d['memory']}%",'') if d['kind']=='RTR' else ('Temperature',f"{d['temperature']}°C",'')
 metrics([('Status','Stale' if not d['fresh'] else d['status'],''),(d['metric'],fmt(d['value'],d['unit']),''),extra,('Last reading','25 min ago' if not d['fresh'] else 'Current demo step','Controlled simulated clock.')])
 a,b=st.columns([1.5,1])
 with a:
  st.subheader(d['metric']+' history');chart(series(s,d['id'],'value',True),d['unit'],310,85 if d['kind']=='RTR' else None)
 with b:
  st.subheader('Related events');related=[i for i in inc_rows() if i['site']==d['site']]
  if not related:st.info('No active equipment alarms in this scenario.')
  for i in related[:2]:
   st.markdown(badge(i['severity']),unsafe_allow_html=True);st.write(i['title']);st.button('Inspect '+i['id'],on_click=go,args=('Incident detail',),kwargs={'incident':i['id']})
  if d['kind']=='BAT':st.caption('Estimated runtime: '+('unknown' if d['value'] is None else f"{d['value']*2:.0f} minutes at assumed constant load")+' · illustrative assumption')
  if d['kind']=='RTR':st.caption('Uptime: 3 days 14 hours · illustrative inventory field')

elif route=='Incidents':
 heading('Incident centre','Correlated alarms · Customer impact · Operator response')
 a,b=st.columns(2);severity=a.selectbox('Severity',['All','Critical','Major']);state=b.selectbox('State',['Active','All','Resolved'])
 rows=[i for i in inc_rows() if (severity=='All' or i['severity']==severity) and (state=='All' or (state=='Resolved')==(i['state']=='Resolved'))]
 for i in paginate(rows,'incidents',5):
  a,b,c,d=st.columns([4,1.4,1.8,1]);a.write(f"**{i['id']} · {i['title']}**");a.caption(i['site']+' · '+s['sites'][i['site']]['province']);b.markdown(badge(i['severity']),unsafe_allow_html=True);c.write(i['state']);d.button('Open →',key='inc_'+i['id'],on_click=go,args=('Incident detail',),kwargs={'incident':i['id'],'site':i['site']})

elif route in ['Incident detail','Recovery']:
 if ss.incident not in s['incidents']:ss.incident=next(iter(s['incidents']))
 i=s['incidents'][ss.incident];site=s['sites'][i['site']]
 heading(i['id']+' · '+('Recovery' if route=='Recovery' else 'Diagnosis'),i['title']+' · '+i['site'])
 a,b,c=st.columns([1,1,3]);a.button('← Incidents',on_click=go,args=('Incidents',));b.button('Diagnosis' if route=='Recovery' else 'Recovery →',on_click=go,args=('Incident detail' if route=='Recovery' else 'Recovery',))
 metrics([('State',i['state'],''),('Affected customers',f"{site['affected']:,}",'Current simulated impact'),('Controller',i['controller'],''),('Priority service',site['priority'],'')])
 if route=='Incident detail':
  a,b=st.columns(2)
  with a:
   with st.container(border=True):
    st.subheader('Likely cause');st.write(i['cause']);st.caption(i['method']+' · scripted demo output')
    st.write('**Evidence:** '+i['evidence']);st.write('**Alternatives:** '+i['alternatives']);st.caption(f"Illustrative confidence: {i['confidence']}% · not a calibrated model probability")
  with b:
   with st.container(border=True):
    st.subheader('Site signals');l=s['links'][i['site']]
    table([{'Signal':'Mains','Reading':'Available' if site['mains'] else 'Failed'},{'Signal':'Battery','Reading':fmt(site['charge'],'%')},{'Signal':'Backhaul','Reading':'Up' if l['up'] else 'Down'},{'Signal':'Security','Reading':'Suspected tampering' if i['scenario']=='Suspected tampering' else 'No alarm'}],True)
  st.subheader('Recent timeline');table(event_rows(i['id'])[:3],True)
  a,b=st.columns(2)
  with a:
   if i['ticket']:st.button('Open maintenance ticket →',on_click=go,args=('Ticket detail',))
  b.button('Full audit →',on_click=go,args=('Audit',))
 else:
  p=plan(s,i);a,b=st.columns([1.3,1])
  with a:
   st.subheader('Proposed response');st.write('**'+p['action']+'**');st.caption(p['reason'])
   st.write(f"Alternate site: **{p['neighbor']}** · Spare: **{p['spare']:.0f} Mbps** · Required: **{p['need']} Mbps**")
   st.caption('Alternative: retain current routing and dispatch an engineer. Radio coverage is not inferred from geographic proximity.')
   x,y=st.columns(2);x.metric('Predicted affected after action',p['predicted']);y.metric('Observed in simulation',site['affected'])
   a1,a2,a3=st.columns(3)
   a1.button('Assess proposal',on_click=cmd,args=('assess',i['id']),disabled=i['state'] not in ['Assessing','Needs intervention'])
   a2.button('Approve',on_click=cmd,args=('approve',i['id']),disabled=i['state']!='Awaiting approval' or bool(paused(s,i)) or not p['safe'])
   a3.button('Reject',on_click=cmd,args=('reject',i['id']),disabled=i['state']!='Awaiting approval')
   with st.form('modify'):
    amount=st.number_input('Proposed traffic shift (Mbps)',100,400,i['desired'],50)
    if st.form_submit_button('Update proposal',disabled=i['state'] not in ['Assessing','Awaiting approval','Needs intervention']):
     i['desired']=amount;i['state']='Assessing';audit(s,f'Proposal modified: {amount} Mbps',i['id'],ss.engineer);st.rerun()
  with b:
   st.subheader('Operator control');st.caption(paused(s,i) or f"{i['risk']} risk · {i['stable']}/3 stability checks")
   x,y=st.columns(2);x.button('Take manual control',on_click=cmd,args=('override',i['id']));y.button('Roll back',on_click=cmd,args=('rollback',i['id']),disabled=not i['before'])
   with st.form('pause'):
    x,y=st.columns(2);scope=x.selectbox('Pause scope',['Incident','Site','Province']);minutes=y.selectbox('Duration (minutes)',[5,15,30,60])
    if st.form_submit_button('Pause automation'):
     target={'Incident':i['id'],'Site':i['site'],'Province':site['province']}[scope];s['pauses'].append(dict(scope=target,until=s['minute']+minutes));audit(s,f'{scope} automation paused for {minutes} minutes',i['id'],ss.engineer);st.rerun()
   confirm=st.checkbox('Confirm handover to automation')
   st.button('Health check & hand back',on_click=cmd,args=('handover',i['id']),disabled=not confirm)
   if st.button('EMERGENCY STOP',type='primary'):
    s['stop']=True;audit(s,'Emergency stop: further automated actions blocked',i['id'],ss.engineer);st.rerun()
   st.caption('Use Advance +5 minutes to execute and verify. Use Demo controls to release an emergency stop.')

elif route=='Tickets':
 heading('Field response','Faults requiring physical investigation or repair')
 rows=[t for t in s['tickets'].values() if ss.province=='All provinces' or s['sites'][t['site']]['province']==ss.province]
 for t in paginate(rows,'tickets',5):
  a,b,c,d=st.columns([3,2,2,1]);a.write(f"**{t['id']} · {t['site']}**");b.write(t['owner']);c.write(t['status']);d.button('Open →',key=t['id'],on_click=go,args=('Ticket detail',),kwargs={'incident':t['incident'],'site':t['site']})
 if not rows:st.info('No field tickets yet. Load a power failure, outage, or tampering scenario in Demo controls.')

elif route=='Ticket detail':
 i=s['incidents'][ss.incident];t=s['tickets'].get(i['id'])
 if not t:heading('No maintenance ticket','This incident currently uses remote investigation.');st.button('← Tickets',on_click=go,args=('Tickets',))
 else:
  heading(t['id']+' · Field repair',t['site']+' · '+i['title'])
  back,brief=st.columns(2);back.button('← Tickets',on_click=go,args=('Tickets',));brief.button('Maintenance evidence & technician brief →',on_click=go,args=('Maintenance case',))
  m=maintenance.init_case(s,i)
  a,b=st.columns(2)
  with a:
   st.write('**Suspected cause:** '+i['cause']);st.write('**Evidence:** '+i['evidence']);st.caption(f"Urgency: {i['severity']} · Customers initially affected: {i['affected']} · Linked incident: {i['id']}")
   with st.form('ticketform'):
    owner=st.text_input('Assigned engineer',t['owner']);status=st.selectbox('Dispatch status',['Open','Assigned','Dispatched','On site','Repair recorded'],index=['Open','Assigned','Dispatched','On site','Repair recorded'].index(t['status']) if t['status'] in ['Open','Assigned','Dispatched','On site','Repair recorded'] else 0);eta=st.text_input('Estimated restoration',t['eta']);note=st.text_input('Technician update')
    if st.form_submit_button('Save update',disabled=t['closed']):
     t.update(owner=owner,status=status,eta=eta);ticket_update(s,i,note or status);audit(s,'Ticket updated: '+(note or status),i['id'],ss.engineer);st.rerun()
  with b:
   st.subheader('Repair verification');st.write(f"Incident: **{i['state']}** · Stability: **{i['stable']}/3**")
   st.button('Record physical repair',on_click=cmd,args=('repair',i['id']),disabled=i['repair'] or t['closed'] or not all(m[k] for k in ['confirmed_cause','technician','action','evidence_ref']))
   st.button('Close ticket',on_click=cmd,args=('close',i['id']),disabled=not maintenance.ready_to_close(s,i) or t['closed'])
   if st.button('Run post-repair tests',disabled=not i['repair'] or t['closed']):
    maintenance.field_tests(s,i);st.rerun()
   st.caption('Record findings in the maintenance brief, record repair, pass post-repair tests, then advance three stability checks.')
   st.subheader('Latest technician updates')
   for note in t['updates'][-4:]:st.caption(note)

elif route=='Reports':
 heading('Operations report','Metrics derive from this session’s recorded events')
 rows=inc_rows();resolved=[i for i in rows if i['resolved'] is not None];rest=[i['resolved']-i['start'] for i in resolved];overrides=[e for e in s['audit'] if e['event']=='Manual override taken'];repeats=len(rows)-len(set(i['site'] for i in rows))
 metrics([('Mean detection delay',fmt(mean(i['detected']-i['start'] for i in rows),' min') if rows else '—','Measured from scenario fault time to detection.'),('Mean restoration',fmt(mean(rest),' min') if rest else '—','Resolved incidents only; temporary mitigation excluded.'),('Resolved / total',f'{len(resolved)} / {len(rows)}',''),('Manual overrides',sum(e['incident'] in {i['id'] for i in rows} for e in overrides),'Count within selected province.')])
 st.caption(f'Repeat incidents in selected scope: {repeats}')
 restored=[i for i in rows if i.get('maintenance',{}).get('service_restored_at') is not None]
 open_repairs=sum(i['ticket'] and not s['tickets'][i['id']]['closed'] for i in rows)
 st.caption(f'Service restored before physical repair: {len(restored)} incidents · Maintenance tickets still open: {open_repairs}')
 chosen=st.selectbox('Incident briefing',[i['id'] for i in rows] or ['None'])
 if chosen!='None':
  i=s['incidents'][chosen];site=s['sites'][i['site']]
  recent=[e['event'] for e in s['audit'] if e['incident']==chosen][-3:]
  briefing=f"{chosen} | {site['province']} / {site['name']}\n{site['affected']} customers currently affected. Service: {site['status']}. Recovery: {i['state']}.\nActions: {'; '.join(recent)}.\nNext: {'Monitor normal service' if i['state']=='Resolved' else 'Complete repair and verification' if i['repair'] else 'Review incident and recovery proposal'}."
  st.text(briefing)
  st.download_button('Download briefing',briefing,file_name=chosen+'.txt')
  a,b=st.columns([3,1]);feedback=a.selectbox('Operator feedback',['Diagnosis correct','Incorrect diagnosis','Ineffective action','Needs investigation'])
  if b.button('Record feedback'):
   i['feedback']=feedback;audit(s,'Operator feedback: '+feedback,chosen,ss.engineer);st.success('Feedback recorded.')
 st.button('Open audit history →',on_click=go,args=('Audit',))
 st.download_button('Export session audit CSV',pd.DataFrame(s['audit']).to_csv(index=False),'noc_audit.csv','text/csv')

elif route=='Audit':
 heading('Audit history','Timestamped decisions, simulated actions, overrides and results')
 ids=['All']+list(s['incidents']);iid=st.selectbox('Incident filter',ids)
 table(paginate(event_rows(None if iid=='All' else iid),'audit',8),True)
 st.button('← Reports',on_click=go,args=('Reports',))

elif route=='Demo controls':
 heading('Demonstration controls','Each browser session has independent state. Advance time explicitly; Reset starts a new demonstration.')
 a,b=st.columns(2)
 with a:
  st.subheader('Load a scenario');scenario=st.selectbox('Scenario',list(SCENARIOS))
  st.caption('Target site: '+SCENARIOS[scenario][0])
  if st.button('Start scenario',type='primary'):
   if trigger(s,scenario):st.success('Scenario loaded. Open Incidents to investigate.')
   else:st.info('This site already has an active incident.')
  name=st.text_input('Operator name',value=ss.engineer,key='operator_input')
  ss.engineer=name.strip() or 'Demo engineer'
  auto=st.checkbox('Allow automatic low-risk recovery',value=s['auto'])
  if auto!=s['auto']:s['auto']=auto;audit(s,'Low-risk automation '+('enabled' if auto else 'disabled'),actor=ss.engineer)
  st.caption('Only the allowlisted router diagnostic-process restart is low risk. Advance time to run it.')
  st.button('Reset demonstration',on_click=reset)
 with b:
  st.subheader('Verification and repair');iid=st.selectbox('Target incident',list(s['incidents']))
  i=s['incidents'][iid]
  if st.button('Make recovery verification fail',disabled=i['state'] not in ['Acting','Verifying'] or i['repair']):
   i['quality_fail']=True;audit(s,'Injected service regression for rollback demonstration',iid,'Demo operator');st.success('The next verification step will trigger rollback.')
  st.button('Record physical repair',key='demo_repair',on_click=cmd,args=('repair',iid),disabled=i['repair'] or i['state']=='Resolved')
  confirm=st.checkbox('Confirm resuming after emergency stop')
  if st.button('Release emergency stop',disabled=not s['stop'] or not confirm):
   s['stop']=False;audit(s,'Emergency stop released after explicit confirmation',actor=ss.engineer);st.rerun()
  if st.button('Clear timed pauses'):
   s['pauses']=[];audit(s,'Timed pauses cleared by operator',actor=ss.engineer);st.success('Pauses cleared.')
  if i['ticket']:st.button('Record technician findings →',on_click=go,args=('Technician findings',),kwargs={'incident':iid,'site':i['site']})
  st.caption('Backhaul alternatives are fictional connected paths. Radio coverage is never assumed from distance alone.')

elif route=='Issues & Response':
 heading('Issues & Response','Six core problems · Evidence → Analysis → Recommendation → Measured result')
 st.caption('Analysis uses explicit demonstration rules. Named AI methods describe the proposed production capability.')
 names=list(issues.ISSUES)
 for offset in (0,3):
  for col,kind in zip(st.columns(3),names[offset:offset+3]):
   spec=issues.ISSUES[kind];rows=issues.affected(s,kind,ss.province)
   with col:
    with st.container(border=True):
     st.subheader(kind)
     st.markdown(f"**{len(rows)} affected {'devices' if kind=='Device offline' else 'routers' if kind=='High CPU' else 'interfaces' if kind=='Interface errors' else 'links'}** · {ss.province}")
     st.caption(('Offline equipment' if kind=='Device offline' else f"Demo alert limit: >{spec['threshold']}{spec['unit']}")+' · '+spec['scope'])
     st.write(spec['response'])
     st.caption(('Critical' if any(r['severity']=='Critical' for r in rows) else 'Major')+' · '+', '.join(sorted(set(r['status'] for r in rows))) if rows else 'No current threshold breaches')
     st.button('Open '+kind,key='issuecard_'+kind,on_click=open_issue,args=(kind,),width='stretch')
 runs=[i for i in s['incidents'].values() if i.get('issue_analysis') and (ss.province=='All provinces' or s['sites'][i['site']]['province']==ss.province)]
 if runs:
  last=runs[-1]
  st.button('Latest analysed incident: '+last['id']+' · '+last['state'],on_click=go,args=('Issue result',),kwargs={'incident':last['id'],'issue_kind':last['issue_analysis']['kind'],'site':last['site']})
 st.caption('An incident can breach several metrics; counts represent affected assets, not separate incidents. Stale readings are excluded.')

elif route in ['Issue detail','Issue analysis','Issue recommendation','Issue result']:
 kind=ss.get('issue_kind','Congestion');spec=issues.ISSUES[kind]
 i=s['incidents'].get(ss.incident)
 # A changed site selection must never show another site's incident under that header.
 if i and i['site']!=ss.site:
  i=next((x for x in reversed(list(s['incidents'].values())) if x['site']==ss.site and x['state']!='Resolved'),None)
  ss.incident=i['id'] if i else ''
 heading(kind+' · '+{'Issue detail':'Problem','Issue analysis':'Analysis','Issue recommendation':'Recommendation','Issue result':'Result'}[route],spec['scope']+' · '+ss.site+' · Simulated analysis, no trained model')
 stages=[('Problem','Issue detail'),('Analysis','Issue analysis'),('Recommendation','Issue recommendation'),('Result','Issue result')]
 nav=st.columns([1.3,1,1,1.3,1])
 nav[0].button('← All issues',on_click=go,args=('Issues & Response',))
 a=i.get('issue_analysis') if i else None
 if a and a['kind']!=kind:a=None
 for col,(label,dest) in zip(nav[1:],stages):
  col.button(label,key='step_'+label,on_click=go,args=(dest,),disabled=dest!='Issue detail' and (not a or (dest=='Issue recommendation' and not a['reviewed'])),type='primary' if route==dest else 'secondary')
 if not i:
  left,right=st.columns(2)
  with left:
   with st.container(border=True):
    st.subheader('What this issue means');st.write(spec['impact']);st.write('**Operator response:** '+spec['response'])
    st.caption('No linked active incident for the selected site.')
  with right:
   with st.container(border=True):
    st.subheader('How analysis would help');st.write('**Proposed method:** '+spec['method']);st.write('**Inputs:** '+spec['inputs']);st.caption(spec['purpose'])
    st.button('Load '+kind+' example',on_click=start_issue_demo,args=(kind,),type='primary')
    st.caption('Loads fictional measurements and switches to the example site. Time advances only when you click.')
 elif route=='Issue detail':
  value=issues.measure(s,kind,i['site']);site=s['sites'][i['site']]
  metrics([('Current reading',('Online' if value else 'Offline') if kind=='Device offline' and value is not None else fmt(value,spec['unit']),''),('Demo target','Reachable' if kind=='Device offline' else f"≤{spec['threshold']}{spec['unit']}",'Illustrative operating limit, not a universal industry standard.'),('Customers affected',f"{site['affected']:,}",''),('Response status',i['state'],'')])
  left,right=st.columns(2)
  with left:
   with st.container(border=True):
    st.subheader('Problem and service impact');st.write(spec['impact']);st.write('**Incident:** '+i['id']+' · '+i['title']);st.caption('Severity: '+i['severity']+' · '+site['priority'])
    st.button('Analyse evidence →',on_click=issue_action,args=('analyse',),disabled=i['state'] not in ['Assessing','Awaiting approval','Needs intervention'],type='primary')
  with right:
   with st.container(border=True):
    st.subheader('Analysis approach');st.write('**Proposed AI method:** '+spec['method']);st.write('**Inputs:** '+spec['inputs']);st.caption(spec['purpose']);st.caption('Implemented now: deterministic rules evaluated against the current simulated readings.')
    st.button('Load '+kind+' example',on_click=start_issue_demo,args=(kind,),disabled=i['site']==SCENARIOS[spec['scenario']][0] and i['state']!='Resolved')
  rows=issues.affected(s,kind,ss.province)
  st.caption(f'{len(rows)} affected assets in this province scope. Use the site selector above to inspect another site.')
 elif not a:
  st.info('Open Problem and analyse the evidence first.')
 elif route=='Issue analysis':
  left,right=st.columns(2)
  with left:
   with st.container(border=True):
    st.subheader('1 · Evidence used')
    labels={'latency':('Latency','ms'),'loss':('Packet loss','%'),'utilisation':('Link utilisation','%'),'error':('Interface errors','%'),'cpu':('Router CPU','%'),'online':('Router online','')}
    keys=['cpu','online','utilisation','latency'] if kind=='High CPU' else ['online','cpu','latency','loss'] if kind=='Device offline' else ['utilisation','latency','loss','error']
    table([{'Measurement':labels[k][0],'At analysis':('Yes' if a['before'][k] else 'No') if k=='online' else fmt(a['before'][k],labels[k][1],2 if k in ['error','loss'] else 1)} for k in keys],True)
    st.caption('Captured at '+a['time']+' · Snapshot retained for the before/after comparison.')
  with right:
   with st.container(border=True):
    st.subheader('2 · Reasoning and uncertainty');st.write('**'+a['cause']+'**');st.write(a['rule']);st.caption('Alternative: '+a['alternative']);st.caption('No calibrated confidence score: this is rule-based demonstration evidence.')
    st.write('**Proposed AI:** '+a['method']);st.caption(spec['purpose'])
  st.button('Review recommendation →',on_click=issue_action,args=('review',),type='primary')
  st.caption('Analysis and recommendations are recorded in the incident audit history.')
 elif route=='Issue recommendation':
  p=plan(s,i);left,right=st.columns(2)
  with left:
   with st.container(border=True):
    st.subheader('3 · Recommended action');st.write('**'+p['action']+'**');st.write(p['reason'])
    st.caption('Why: '+a['cause']+' · Alternative: retain current operation and investigate physically.')
    st.caption('Approval: '+i['risk']+' risk · '+('Human approval required' if i['risk']=='High' else 'Allowlisted demo action'))
    if i['ticket']:st.button('Open repair ticket →',on_click=go,args=('Ticket detail',))
  with right:
   with st.container(border=True):
    st.subheader('Capacity and expected effect')
    if kind not in ['High CPU','Device offline','Interface errors']:
     source=s['links'][i['site']];target=s['links'][p['neighbor']]
     table([{'Path':'Primary '+i['site'],'Now':fmt(source['traffic']/source['capacity']*100,'%'),'Projected':fmt((source['traffic']-p['need'])/source['capacity']*100,'%')},{'Path':'Alternate '+p['neighbor'],'Now':fmt(target['traffic']/target['capacity']*100,'%'),'Projected':fmt((target['traffic']+p['need'])/target['capacity']*100,'%')}],True)
     st.caption(f"Move {p['need']} Mbps on the fictional connected path. Congestion targets require both paths ≤80%.")
    st.write('**Projected affected customers:** '+str(p['predicted']));st.caption('Illustrative estimate; success must be checked after execution.')
  x,y,z=st.columns(3)
  x.button('Approve action →',on_click=issue_action,args=('approve',),disabled=not a['reviewed'] or i['state']!='Awaiting approval' or not p['safe'] or bool(paused(s,i)),type='primary')
  y.button('Reject proposal',on_click=cmd,args=('reject',i['id']),disabled=i['state']!='Awaiting approval')
  z.button('Operator controls →',on_click=go,args=('Recovery',))
  st.caption(paused(s,i) or 'No background execution: approve here, then execute on the Result page.')
 elif route=='Issue result':
  current=issues.capture(s,i)
  metrics([('Response state',i['state'],''),('Stable samples',f"{i['stable']} / 3",''),('Affected before',a['before']['customers'],''),('Affected now',current['customers'],'')])
  left,right=st.columns(2)
  with left:
   with st.container(border=True):
    st.subheader('4 · Measured comparison')
    units={'latency':' ms','loss':'%','utilisation':'%','error':'%','cpu':'%'}
    keys=['cpu','latency','loss'] if kind=='High CPU' else ['error','loss','latency'] if kind=='Interface errors' else ['utilisation','latency','loss','error']
    table([{'Metric':k.title(),'Before':fmt(a['before'][k],units[k],2 if k in ['error','loss'] else 1),'Current':fmt(current[k],units[k],2 if k in ['error','loss'] else 1)} for k in keys],True)
    if kind=='Device offline':st.write('Router: '+('Online' if a['before']['online'] else 'Offline')+' → '+('Online' if current['online'] else 'Offline'))
    st.caption('Current values are also used by the map, network metrics and equipment pages.')
  with right:
   with st.container(border=True):
    st.subheader('Verification checks')
    for name,ok in issues.checks(s,i):st.write(('✓ ' if ok else '✕ ')+name)
    st.caption('Three consecutive explicit verification steps are required. A failed check triggers rollback when a change snapshot exists.')
    if i['state']=='Resolved':st.success('Verified. Congestion routing is retained.' if kind=='Congestion' else 'Verified. Incident resolved.')
    elif i['state']=='Mitigated':st.info('Service restored on an alternate path. Original fault still needs repair.')
    elif i['state']=='Needs intervention':st.warning('Recovery blocked or failed. Review the incident before another action.')
  x,y,z=st.columns(3)
  x.button('Execute approved action',on_click=issue_action,args=('execute',),disabled=i['state']!='Acting' or bool(paused(s,i)),type='primary')
  y.button('Verify next sample (+5 min)',on_click=issue_action,args=('verify',),disabled=i['state']!='Verifying' or bool(paused(s,i)))
  z.button('Open incident / audit →',on_click=go,args=('Incident detail',))
  st.caption(paused(s,i) or 'Simulation only. Each execution or verification click advances the shared simulation by five minutes.')

elif route=='Maintenance':
 heading('Maintenance centre','Restore service · Repair the asset · Verify the work · Learn from the outcome')
 cases=[i for i in inc_rows() if i['ticket']]
 watch=[w for w in s['watch'].values() if ss.province=='All provinces' or s['sites'][w['site']]['province']==ss.province]
 metrics([('Open repair tickets',sum(not s['tickets'][i['id']]['closed'] for i in cases),''),('Service mitigated / repair open',sum(i['state']=='Mitigated' and not s['tickets'][i['id']]['closed'] for i in cases),''),('Condition warnings',sum(maintenance.watch_result(w)['priority']=='High' for w in watch),'Demonstration condition rules; not predicted failure probabilities.')])
 a,b,c=st.columns(3)
 a.button('Load fibre-damage example',on_click=load_fibre,type='primary')
 b.button('Predictive maintenance / condition watch →',on_click=go,args=('Maintenance watch',))
 c.button('All field tickets →',on_click=go,args=('Tickets',))
 st.subheader('Corrective maintenance')
 if not cases:st.info('Load the fibre example to see evidence, a technician brief, traffic mitigation and physical repair tracked together.')
 for i in paginate(cases,'maintenance',4):
  t=s['tickets'][i['id']];a,b,c,d=st.columns([3,2,2,1])
  a.write('**'+t['id']+' · '+i['title']+'**');a.caption(i['site'])
  b.write('Service: '+i['state']);c.write('Repair: '+('Closed' if t['closed'] else 'Verifying' if i['repair'] else 'Outstanding'))
  d.button('Brief →',key='maint_'+i['id'],on_click=go,args=('Maintenance case',),kwargs={'incident':i['id'],'site':i['site']})
 st.caption('Traffic restoration does not close the repair ticket. Confirmed cause, corrective work, post-repair tests and stable service are required.')

elif route in ['Maintenance case','Technician findings']:
 i=s['incidents'].get(ss.incident);t=s['tickets'].get(ss.incident)
 if not i or not t:
  heading('Select a maintenance case');st.button('← Maintenance',on_click=go,args=('Maintenance',))
 else:
  m=maintenance.init_case(s,i);brief=maintenance.corrective_brief(s,i)
  heading(t['id']+' · '+('Technician findings' if route=='Technician findings' else 'Maintenance brief'),i['site']+' · '+i['title'])
  a,b,c,d=st.columns(4)
  a.button('← Maintenance',on_click=go,args=('Maintenance',))
  b.button('Evidence / repair plan',on_click=go,args=('Maintenance case',))
  c.button('Technician findings',on_click=go,args=('Technician findings',))
  d.button('Traffic recovery →',on_click=go,args=('Recovery',))
  if route=='Maintenance case':
   metrics([('Customer service','Restored on alternate' if i['state']=='Mitigated' else 'Restored' if s['sites'][i['site']]['affected']==0 else 'Affected',''),('Physical repair','Closed' if t['closed'] else 'Recorded / verify' if i['repair'] else 'Outstanding',''),('Cause','Field recorded' if m['confirmed_cause'] else 'Unconfirmed','')])
   a,b=st.columns([1.15,1])
   with a:
    st.subheader('Failure evidence');st.caption('Captured at '+m['captured_at']+' · incident snapshot retained after repair')
    table([{'Signal':label,'Observation':value,'Source':source} for label,value,source in brief['evidence']],True)
    st.caption(brief['unknown'])
    if i['scenario']=='Fibre damage':
     if st.button('Attach simulated OTDR result',disabled=m['otdr_km'] is not None or t['closed']):
      m['otdr_km']=8.2;audit(s,'Simulated OTDR event imported: 8.2 km from GT-06; physical cause unconfirmed',i['id'],ss.engineer);st.rerun()
   with b:
    st.subheader('Suggested corrective work');st.write('**Working diagnosis:** '+brief['cause'])
    for n,step in enumerate(brief['steps'],1):st.write(f'{n}. {step}')
    st.caption('Crew / kit: '+brief['kit'])
    st.caption('Proposed AI: '+brief['method']+'. Current output is an explicit demonstration template.')
   st.download_button('Download technician brief',maintenance.briefing(s,i),file_name=t['id']+'_brief.txt')
  else:
   a,b=st.columns([1.2,1])
   with a:
    with st.form('findings_form'):
     st.subheader('Record actual field findings')
     tech=st.text_input('Technician',m['technician'])
     cause=st.text_input('Confirmed cause',m['confirmed_cause'],placeholder='e.g. fire-damaged fibre sheath and broken strands')
     action=st.text_input('Corrective work performed',m['action'],placeholder='Describe the component repaired or replaced')
     ref=st.text_input('Test / photo / work report reference',m['evidence_ref'],placeholder='Reference to supporting evidence; demo text only')
     if st.form_submit_button('Save findings',disabled=t['closed']):
      if maintenance.record_findings(s,i,cause,tech,action,ref):st.success('Findings saved. Record the repair and run post-repair tests.')
      else:st.error('Complete all four fields.')
   with b:
    st.subheader('Repair and closure gates')
    st.write('**1 · Field evidence:** '+('Recorded' if all(m[k] for k in ['confirmed_cause','technician','action','evidence_ref']) else 'Required'))
    st.button('Record physical repair',key='maint_repair',on_click=cmd,args=('repair',i['id']),disabled=i['repair'] or t['closed'] or not all(m[k] for k in ['confirmed_cause','technician','action','evidence_ref']))
    st.write('**2 · Post-repair tests:** '+('Passed' if m['tests'] else 'Awaiting measurements'))
    st.button('Run post-repair tests',on_click=maintenance_tests,disabled=not i['repair'] or t['closed'])
    st.write(f"**3 · Stability:** {i['stable']}/3 samples")
    st.button('Verify next sample (+5 min)',on_click=advance,args=(s,),disabled=not m['tests'] or i['state']!='Verifying')
    st.button('Close maintenance ticket',on_click=cmd,args=('close',i['id']),disabled=t['closed'] or not maintenance.ready_to_close(s,i),type='primary')
    st.caption('Tests use simulated optical/link readings. Three stable checks restore primary routing and release temporary capacity. Closure retains the findings for future diagnosis.')
   if m['test_values']:st.caption('Latest post-repair evidence: '+str(m['test_values']))

elif route=='Maintenance watch':
 heading('Predictive maintenance · Condition watch','Historical sample data → Explainable warning → Preventive work order')
 st.button('← Maintenance',on_click=go,args=('Maintenance',))
 watch=[w for w in s['watch'].values() if ss.province=='All provinces' or s['sites'][w['site']]['province']==ss.province]
 if not watch:st.info('No demonstration histories in this province. Select All provinces to see the three condition examples.')
 else:
  selected=st.selectbox('Asset / condition',[w['id'] for w in watch],format_func=lambda k:s['watch'][k]['asset']+' · '+s['watch'][k]['kind'])
  w=s['watch'][selected];r=maintenance.watch_result(w)
  metrics([('Latest recorded sample',fmt(r['latest'],w['unit']),''),('Change over 7 days',fmt(r['change'],w['unit']),''),('Review priority',r['priority'],'Condition-based triage, not a failure probability.')])
  a,b=st.columns(2)
  with a:
   st.subheader('Recorded condition history')
   from plotly import graph_objects as pg
   f=pg.Figure(pg.Scatter(x=list(range(-7,1)),y=w['values'],mode='lines+markers',line=dict(color='#745039',width=3)))
   f.add_hline(y=w['limit'],line_dash='dot',line_color='#966511',annotation_text='Demo warning limit')
   f.update_layout(height=240,margin=dict(l=35,r=15,t=10,b=40),paper_bgcolor='#fff',plot_bgcolor='#fff',font=dict(color='#302b27'),xaxis_title='Days before last recorded sample',yaxis_title=w['unit'])
   st.plotly_chart(f,width='stretch',config={'displayModeBar':False})
   st.caption('Separate historical maintenance dataset; these are not live device readings. Limits depend on actual equipment specifications.')
  with b:
   st.subheader('Why maintenance is recommended');st.write(w['rule']);st.write('**Suggested action:** '+w['action']);st.caption('Crew equipment: '+w['tools']);st.caption('Proposed AI: '+w['method'])
   if st.button('Create / open preventive order',type='primary'):
    maintenance.create_order(s,w,ss.engineer);go('Preventive order',watch_id=selected);st.rerun()
   st.caption('No estimated failure date is claimed. Abrupt fire/cable cuts may have no detectable precursor. A production model needs labelled failure and repair histories.')

elif route=='Preventive order':
 key=ss.get('watch_id','WATCH-01');w=s['watch'][key];o=s['preventive_orders'].get(key)
 heading('Preventive work order',w['asset']+' · '+w['kind']);st.button('← Condition watch',on_click=go,args=('Maintenance watch',))
 if o:
  a,b=st.columns(2)
  with a:
   st.write('**'+o['id']+' · '+o['status']+'**');st.write(w['action']);st.caption('Recommendation: '+maintenance.watch_result(w)['recommendation'])
   with st.form('preventive_form'):
    owner=st.text_input('Assigned technician',o['owner']);window=st.text_input('Planned work window',o['window']);status=st.selectbox('Work status',['Planned','Assigned','In progress','Completed'],index=['Planned','Assigned','In progress','Completed'].index(o['status']));notes=st.text_input('Work performed / outcome',o['notes'])
    if st.form_submit_button('Save preventive order'):
     if status=='Completed' and (not notes.strip() or not owner.strip() or owner=='Unassigned'):st.error('Completion requires an assigned technician and a recorded outcome.')
     else:o.update(owner=owner,window=window,status=status,notes=notes);audit(s,'Preventive order '+o['id']+' updated: '+status,actor=ss.engineer);st.success('Work order updated.')
  with b:
   st.subheader('Follow-up');st.write('Collect new condition measurements after the work. A completed work order does not automatically clear the original warning.');st.caption('Record confirmed cause, work, parts and test outcomes to support later model training and evaluation.')
   st.download_button('Download preventive brief','\n'.join([o['id'],w['asset'],w['rule'],w['action'],w['tools'],str(o)]),file_name=o['id']+'.txt')
