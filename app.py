"""Three-page Autonomous_Troy concept demonstrator using the uploaded styling."""
import json
import time
from html import escape
from pathlib import Path
from statistics import mean

import pandas as pd
import plotly.graph_objects as pg
import streamlit as st

import demo_engine as demo
from model import PROVINCES
from theme import CSS

st.set_page_config(page_title='Autonomous_Troy',page_icon='◈',layout='wide',initial_sidebar_state='expanded')
st.markdown(CSS,unsafe_allow_html=True)
st.markdown('''<style>
.ticket-card {background:#fff;border:1px solid #e7dfd9;border-radius:12px;padding:.8rem;margin-bottom:.4rem;min-height:190px;}
.ticket-card .repair {font-size:13px;line-height:1.4;margin-top:8px;color:#2e2724;}
.brief-meta {font-size:12px;color:#685d57;line-height:1.5;}
[data-testid="stMain"] [data-testid="stMarkdownContainer"] {color:#2e2724;}
[data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3 {color:#2e2724;}
</style>''',unsafe_allow_html=True)

ss=st.session_state
if 'troy' not in ss:ss.troy=demo.blank_state()
if 'troy_page' not in ss:ss.troy_page='Network Overview'
if 'troy_province' not in ss:ss.troy_province='All provinces'
if 'troy_scenario' not in ss:ss.troy_scenario=demo.SCENARIOS[0]
if 'troy_mode' not in ss:ss.troy_mode='Autonomous'


def advance_clock():
    s=ss.troy
    if not s['running']:return
    now=time.monotonic()
    if s['last_tick'] is None:s['last_tick']=now;return
    steps=min(int(now-s['last_tick']),demo.DURATION-s['elapsed'])
    for _ in range(steps):demo.step(s)
    s['last_tick']+=steps


def start():
    s=ss.troy
    if s['elapsed']<demo.DURATION:
        s['running']=True;s['last_tick']=time.monotonic()


def pause():
    advance_clock();ss.troy['running']=False;ss.troy['last_tick']=None


def reset():
    ss.troy=demo.blank_state(ss.troy_scenario)
    ss.troy['automatic']=ss.troy_mode=='Autonomous'
    ss.pop('ticket_detail',None)


def change_mode():
    advance_clock();demo.set_automatic(ss.troy,ss.troy_mode=='Autonomous')


def override():
    ss.troy_mode='Manual';change_mode()


def approve():
    demo.divert(ss.troy,'Operator approval')


def pick_page(page):
    ss.troy_page=page;st.query_params['view']=page


def pill(text,kind='muted'):
    return f'<span class="badge {kind}">{escape(str(text))}</span>'


def metric_row(items):
    for col,(label,value,helptext) in zip(st.columns(len(items)),items):
        col.metric(label,value,help=helptext)


def title(text,subtitle):
    st.markdown('<div class="eyebrow">AUTONOMOUS_TROY · NETWORK OPERATIONS</div>',unsafe_allow_html=True)
    st.title(text);st.caption(subtitle)


@st.cache_data
def boundaries():
    p=Path(__file__).with_name('provinces.geojson')
    return json.loads(p.read_text()) if p.exists() else None


def map_figure(rows,height=340,province='All provinces'):
    f=pg.Figure();geo=boundaries()
    if geo:
        for feature in geo['features']:
            geom=feature['geometry']
            polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
            for poly in polys:
                outer=poly[0]
                f.add_trace(pg.Scatter(x=[p[0] for p in outer],y=[p[1] for p in outer],
                    mode='lines',fill='toself',fillcolor='#e8e3dc',
                    line=dict(color='#b9aaa0',width=.7),hoverinfo='skip',showlegend=False))
    colours={'Healthy':'#3c8864','At risk':'#bd8b26','Protected':'#6c4d3d','Unavailable':'#b7493f'}
    for status,color in colours.items():
        pts=[x for x in rows if x['status']==status]
        if not pts:continue
        f.add_trace(pg.Scatter(x=[x['lon'] for x in pts],y=[x['lat'] for x in pts],
            mode='markers',name=status,marker=dict(color=color,size=10,line=dict(color='white',width=1)),
            text=[f"{x['id']} · {x['name']}<br>{status}<br>{x['affected']:,} affected customers" for x in pts],
            customdata=[x['id'] for x in pts],hovertemplate='%{text}<extra></extra>'))
    if rows and province!='All provinces':
        xs=[x['lon'] for x in rows];ys=[x['lat'] for x in rows]
        pad=max(.18,(max(xs)-min(xs))*.15)
        f.update_xaxes(range=[min(xs)-pad,max(xs)+pad]);f.update_yaxes(range=[min(ys)-pad,max(ys)+pad])
    else:
        f.update_xaxes(range=[15.5,33.5]);f.update_yaxes(range=[-35.5,-21.5])
    f.update_layout(height=height,margin=dict(l=0,r=0,t=0,b=18),paper_bgcolor='#fff',plot_bgcolor='#fff',
                    legend=dict(orientation='h',y=0,x=0,font=dict(size=11)),clickmode='event+select')
    f.update_xaxes(visible=False);f.update_yaxes(visible=False,scaleanchor='x',scaleratio=1.15)
    return f


def trend(s,keys,label,height=205):
    f=pg.Figure()
    colors=['#6c4d3d','#2e7d5a','#b94d41']
    for (key,name),color in zip(keys,colors):
        f.add_trace(pg.Scatter(x=[x['minute'] for x in s['history']],y=[x[key] for x in s['history']],
                    mode='lines',name=name,line=dict(color=color,width=2),connectgaps=False))
    f.update_layout(height=height,margin=dict(l=35,r=10,t=8,b=25),paper_bgcolor='#fff',plot_bgcolor='#fff',
                    font=dict(color='#514137',size=12),xaxis_title='Simulated minute',yaxis_title=label,
                    legend=dict(orientation='h',y=1.12,font=dict(size=10)),showlegend=len(keys)>1)
    f.update_xaxes(gridcolor='#f0ece7');f.update_yaxes(gridcolor='#f0ece7')
    return f


def route_diagram(s):
    f=pg.Figure();primary_good=s['physical_up'];backup_active=s['diverted']
    primary_color='#6c4d3d' if primary_good else '#b94d41'
    backup_color='#2e7d5a' if backup_active else '#b9aaa0'
    for xs,ys,color,dash in [([.5,2.2],[1,1],'#b9aaa0','dot'),
        ([2.2,3.5,5,6.5],[1,1.8,1.8,1],primary_color,'solid' if primary_good else 'dash'),
        ([2.2,3.5,5,6.5],[1,.2,.2,1],backup_color,'solid' if backup_active else 'dash'),
        ([6.5,8],[1,1],'#6c4d3d','solid')]:
        f.add_trace(pg.Scatter(x=xs,y=ys,mode='lines',line=dict(color=color,width=3,dash=dash),hoverinfo='skip',showlegend=False))
    f.add_trace(pg.Scatter(x=[.5,2.2,6.5,8],y=[1,1,1,1],mode='markers',
        marker=dict(size=[18,23,23,23],symbol=['circle','triangle-up','square','square'],
                    color=['#2e7d5a' if s['service_up'] else '#b94d41','#6c4d3d','#6c4d3d','#6c4d3d']),
        text=['Customers','Cell tower','Aggregation hub','Core'],hovertemplate='%{text}<extra></extra>',showlegend=False))
    annotations=[(.5,.64,'Customers'),(2.2,.64,'Tower GT-06'),(6.5,.64,'Aggregation hub'),(8,.64,'Core / services'),
                 (4.3,2.12,'Primary fibre · '+('UP' if primary_good else 'DOWN')),
                 (4.3,-.12,'Backup fibre · '+('CARRYING TRAFFIC' if backup_active else 'STANDBY'))]
    for x,y,text in annotations:
        f.add_annotation(x=x,y=y,text=text,showarrow=False,font=dict(color='#514137',size=12))
    if not primary_good:
        f.add_annotation(x=4.3,y=1.8,text='×',showarrow=False,font=dict(color='#b94d41',size=26),bgcolor='#fff')
    f.update_layout(height=225,margin=dict(l=0,r=0,t=10,b=10),paper_bgcolor='#fff',plot_bgcolor='#fff')
    f.update_xaxes(range=[0,8.7],visible=False);f.update_yaxes(range=[-.45,2.35],visible=False)
    return f


def overview(s):
    rows=demo.scope_sites(s,ss.troy_province);counter=demo.scope_counters(s,ss.troy_province)
    if s['selected_site'] not in [row['id'] for row in rows]:s['selected_site']=rows[0]['id']
    available=[r for r in rows if r['service_up']]
    title('Network overview',f"{ss.troy_province} · {len(rows)} sites · cumulative service measures since demo start")
    metric_row([
        ('Service uptime',demo.duration(counter['uptime']),'Time when all sites in the selected scope had service.'),
        ('Service downtime',demo.duration(counter['downtime']),'Elapsed time with at least one site unavailable; not summed incident durations.'),
        ('Availability','—' if counter['availability'] is None else f"{counter['availability']:.2f}%",'Service uptime / observed elapsed time.'),
        ('Sites connected',f"{len(available)} / {len(rows)}",'Current simulated customer-path reachability.'),
        ('Customers affected',f"{sum(r['affected'] for r in rows):,}",'Fictional service groups.'),
    ])
    left,right=st.columns([1.6,1.05])
    with left:
        with st.container(border=True):
            st.subheader('Geographic health')
            selected=st.plotly_chart(map_figure(rows,340,ss.troy_province),width='stretch',key='troy_map',
                                    on_select='rerun',selection_mode='points',config={'displayModeBar':False})
            if selected.selection.points:
                sid=selected.selection.points[0].get('customdata')
                if sid in s['sites']:s['selected_site']=sid
            st.caption('Province boundaries: geoBoundaries / OCHA / Municipal Demarcation Board · CC BY 3.0 IGO')
    with right:
        with st.container(border=True):
            st.subheader('Service quality')
            a,b,c=st.columns(3)
            a.metric('Latency',f"{mean(r['latency'] for r in available):.1f} ms" if available else 'Unavailable',help='Mean RTT across currently connected sites; outages are excluded.')
            b.metric('Packet loss',f"{mean(r['loss'] for r in available):.2f}%" if available else 'Unavailable',help='Mean of simulated probe-loss measurements on connected sites.')
            c.metric('Traffic',f"{sum(r['traffic'] for r in available)/1000:.1f} Gbps",help='Sum of carried traffic across selected sites.')
            st.plotly_chart(trend(s,[('latency','Demo site RTT')],'GT-06 RTT (ms)',150),width='stretch',config={'displayModeBar':False},key='overview_trend')
            st.markdown('**Latest autonomous activity**')
            event=s['events'][-1]
            st.caption(f"{event['time']} · {event['text']}")
        sid=s['selected_site'];site=s['sites'][sid]
        st.caption(f"Selected: {sid} · {site['name']} · Router CPU {site['cpu']:.0f}% · {site['status']}")


def fibre(s):
    title('Fibre & traffic','Demo link: Boksburg tower GT-06 → aggregation hub · independent primary and backup corridors')
    physical_down=s['counters'][demo.FOCUS]['fibre_downtime'];observed=s['elapsed']
    metric_row([
        ('Received light','No signal' if s['rx'] is None else f"{s['rx']:.2f} dBm",'Synthetic received optical power.'),
        ('Input errors',f"{s['errors']} / min",'Synthetic errored frames per interval; not end-to-end packet loss.'),
        ('Primary uptime',demo.duration(observed-physical_down),'Physical-link observed uptime.'),
        ('Primary downtime',demo.duration(physical_down),'Physical outage persists even when customers use backup.'),
        ('Active route',s['route'],'Current simulated forwarding choice.'),
    ])
    a,b=st.columns([1.65,1])
    with a:
        with st.container(border=True):
            st.subheader('Service protection')
            st.plotly_chart(route_diagram(s),width='stretch',config={'displayModeBar':False},key='topology')
    with b:
        with st.container(border=True):
            st.subheader('Decision & capacity')
            safe,reason,spare=demo.route_check(s)
            st.markdown(pill('Service connected' if s['service_up'] else 'Service unavailable','good' if s['service_up'] else 'bad'),unsafe_allow_html=True)
            risk='Link already failed' if s['risk'] is None else f"{s['risk']:.2f} · illustrative risk score"
            st.caption(risk+' · scripted, not live model inference')
            total=s['backup_background']+(s['demand'] if s['diverted'] else 0)
            st.metric('Backup utilisation',f"{100*total/s['backup_capacity']:.0f}%",help='Background plus diverted traffic / backup capacity.')
            st.caption(f"{spare} Mbps spare before diversion · {s['demand']} Mbps required")
            st.caption(reason)
            if not s['automatic'] and s['warning'] and not s['diverted'] and not s['repaired']:
                st.button('Approve traffic diversion',on_click=approve,disabled=not safe,type='primary')
    a,b=st.columns(2)
    with a:st.plotly_chart(trend(s,[('rx','Received optical power')],'Received power (dBm)',180),width='stretch',config={'displayModeBar':False},key='optical')
    with b:st.plotly_chart(trend(s,[('primary','Primary'),('backup','Backup incl. background')],'Traffic (Mbps)',180),width='stretch',config={'displayModeBar':False},key='traffic')


def ticket_card(s,t):
    site=s['sites'][t['site']]
    service='Connected' if site['service_up'] else 'Unavailable'
    html=f'''<div class="ticket-card">{pill(t['priority'],'bad' if t['priority']=='P1' else 'warn' if t['priority']=='P2' else 'muted')}
    <strong> {escape(t['id'])}</strong><h3>{escape(t['fault'])}</h3>
    <div class="brief-meta">{escape(t['type'])} · {escape(site['name'])}, {escape(site['province'])}<br>
    Technician: {escape(t['owner'])}<br>Service: {service} · Repair: {'verified' if t['tests_passed'] else 'pending'}</div>
    <div class="repair"><strong>Recommended repair:</strong> {escape(t['repair'])}</div></div>'''
    st.markdown(html,unsafe_allow_html=True)
    a,b=st.columns(2)
    a.button('Open brief',key='brief_'+t['id'],on_click=lambda tid=t['id']:ss.update(ticket_detail=tid))
    b.download_button('Download',demo.brief(s,t),file_name=t['id']+'_brief.txt',mime='text/plain',key='download_'+t['id'])


def ticket_detail(s,t):
    title(t['id']+' · technician brief',t['fault'])
    st.button('← Ticket board',on_click=lambda:ss.pop('ticket_detail',None))
    site=s['sites'][t['site']]
    metric_row([('Priority',t['priority'],'P1 service impact; P2 service risk/redundancy; P3 preventive.'),
                ('Technician',t['owner'],'Automatic regional skill/workload match.'),
                ('Status',t['status'],'Simulated technician workflow.'),
                ('Brief delivery',t['delivered'] or 'Pending','Delivery to the local simulated technician inbox.')])
    a,b=st.columns([1.4,1])
    with a:
        with st.container(border=True):
            st.subheader('Fault card')
            st.write(f"**Type:** {t['type']} · **Place:** {site['name']}, {site['province']}")
            st.write(f"**Asset:** {t['site']} primary fibre / router")
            st.write('**Evidence:** '+t['evidence'])
            st.write('**Recommended repair:** '+t['repair'])
            st.write('**Field finding:** '+(t['finding'] or 'Awaiting inspection'))
            st.caption('No external message has been sent. Inbox delivery and technician activity are simulated.')
            st.download_button('Download technician brief',demo.brief(s,t),file_name=t['id']+'_brief.txt',mime='text/plain')
    with b:
        with st.container(border=True):
            st.subheader('Progress tracking')
            for item in t['history'][-6:]:
                st.markdown(f"**{item['time']} · {item['status']}**")
                st.caption(item['note'])


def maintenance(s):
    if ss.get('ticket_detail') in s['tickets']:
        ticket_detail(s,s['tickets'][ss.ticket_detail]);return
    rows=demo.ticket_list(s,ss.troy_province)
    title('Maintenance & tickets','Automatic priority, technician assignment and brief delivery · simulated field progress')
    metric_row([('Open tickets',sum(t['status']!='Closed' for t in rows),'Selected province scope.'),
                ('P1 urgent',sum(t['priority']=='P1' and t['status']!='Closed' for t in rows),'Service unavailable or critical impact.'),
                ('Assigned',sum(t['owner']!='Unassigned' and t['status']!='Closed' for t in rows),'Matched by fibre skills, region and workload.'),
                ('Verified / closed',sum(t['status']=='Closed' for t in rows),'Repair evidence and post-work checks passed.')])
    st.caption('P1 · service outage     P2 · protected service / high risk     P3 · preventive work')
    stages=[('Assigned',['Assigned','Planned','En route','Awaiting assignment']),('In progress',['In progress','Verifying']),('Verified / closed',['Closed'])]
    for col,(label,statuses) in zip(st.columns(3),stages):
        with col:
            st.subheader(label)
            tickets=[t for t in rows if t['status'] in statuses]
            if not tickets:st.caption('No tickets')
            for t in tickets[:2]:ticket_card(s,t)
    if not rows:st.info('No tickets in this province. Select All provinces or Gauteng for the main scenario.')
    st.caption('Assignment and brief delivery use a local simulated inbox. No email, SMS or external dispatch occurs.')


with st.sidebar:
    st.markdown('## ◈ Autonomous_Troy')
    st.caption('Protect service · coordinate repair')
    st.divider()
    for page in ['Network Overview','Fibre & Traffic','Maintenance & Tickets']:
        st.button(page,key='nav_'+page,use_container_width=True,
                  type='primary' if ss.troy_page==page else 'secondary',on_click=pick_page,args=(page,))
    st.divider()
    st.selectbox('Province',['All provinces']+list(PROVINCES),key='troy_province')
    st.selectbox('Demo scenario',demo.SCENARIOS,key='troy_scenario',on_change=reset)
    st.radio('Traffic control',['Autonomous','Manual'],key='troy_mode',on_change=change_mode)
    st.button('Manual override',on_click=override,use_container_width=True,disabled=not ss.troy['automatic'])
    st.caption('Simulated demo · no live network control')


@st.fragment(run_every='1s')
def screen():
    advance_clock();s=ss.troy
    a,b,c,d=st.columns([1,1,1,5])
    a.button('Resume' if s['elapsed'] and s['elapsed']<demo.DURATION else 'Start',on_click=start,disabled=s['running'] or s['elapsed']>=demo.DURATION,key='start',use_container_width=True)
    b.button('Pause',on_click=pause,disabled=not s['running'],key='pause',use_container_width=True)
    c.button('Reset',on_click=reset,key='reset',use_container_width=True)
    d.markdown(f"{pill('SIMULATED DEMO','warn')} {pill(clock_label(s))} <span class='subtle'>{escape(demo.phase(s))}</span>",unsafe_allow_html=True)
    st.progress(s['elapsed']/demo.DURATION)
    if ss.troy_page=='Network Overview':overview(s)
    elif ss.troy_page=='Fibre & Traffic':fibre(s)
    else:maintenance(s)


def clock_label(s):
    state='Playing' if s['running'] else 'Complete' if s['elapsed']==demo.DURATION else 'Paused'
    return f"{demo.clock(s)} SAST · {state} · {s['elapsed']}/{demo.DURATION}"


screen()
