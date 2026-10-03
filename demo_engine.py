"""Scripted concept replay. No trained-model inference, messaging or network control.

One real second represents one simulated minute. Replay stops after 180 steps.
Service counters accrue observed intervals, independently of incident durations.
"""
from datetime import datetime, timedelta
import math
from model import PROVINCES, CODES

DURATION = 180
FOCUS = 'GT-06'
SCENARIOS = ['Protected fibre failure', 'Backup capacity constrained']
TECHNICIANS = [
    dict(name='Kabelo Molefe', province='Gauteng', skills=['Fibre'], available=True, workload=0),
    dict(name='Naledi Dube', province='Gauteng', skills=['Fibre'], available=True, workload=1),
    dict(name='Lerato Mokoena', province='North West', skills=['Fibre'], available=True, workload=0),
]


def clock(s):
    return (datetime(2026, 10, 5, 9) + timedelta(minutes=s['elapsed'])).strftime('%H:%M')


def duration(minutes):
    hours, mins = divmod(int(minutes), 60)
    return f'{hours}h {mins:02d}m' if hours else f'{mins} min'


def event(s, text, kind='info'):
    s['events'].append(dict(minute=s['elapsed'], time=clock(s), text=text, kind=kind))


def blank_state(scenario=SCENARIOS[0]):
    s = dict(elapsed=0, running=False, last_tick=None, automatic=True,
             scenario=scenario, route='Primary', diverted=False, repaired=False,
             verified=False, risk=0.08, warning=False, physical_up=True,
             rx=-8.0, tx=-3.0, errors=2, latency=24.0, loss=0.1,
             primary_capacity=1000, backup_capacity=1000, demand=600,
             backup_background=100 if scenario==SCENARIOS[0] else 600,
             backup_healthy=True, diverse=True, sites={}, counters={},
             tickets={}, technicians=[dict(t) for t in TECHNICIANS], inbox={},
             events=[], history=[], service_up=True, repaired_at=None,
             brief_deliveries=0, selected_site=FOCUS)
    for p, (province, towns) in enumerate(PROVINCES.items()):
        for n, (name, lat, lon) in enumerate(towns):
            sid=f'{CODES[p]}-{n+1:02}'
            s['sites'][sid]=dict(id=sid, name=name, province=province, lat=lat, lon=lon,
                                 status='Healthy', service_up=True, affected=0,
                                 customers=1500 if sid==FOCUS else 650+n*85,
                                 latency=18+n*3, loss=.12+n*.04,
                                 traffic=420+n*35, cpu=32+n*3, fresh=True)
            s['counters'][sid]=dict(uptime=0, downtime=0, fibre_downtime=0)
    create_ticket(s, 'TROY-001', 'Connector inspection', 'Fibre', 'NW-03', 'P3',
                  'Inspect and clean connectors; confirm optical loss before replacement.',
                  'Stable service; preventive inspection scheduled.', 'Planned')
    event(s, 'Demo ready · 72 sites across 9 provinces')
    snapshot(s)
    return s


def brief(s, t):
    site=s['sites'][t['site']]
    return '\n'.join([
        'AUTONOMOUS_TROY · TECHNICIAN BRIEF',
        f"Ticket: {t['id']} | Priority: {t['priority']} | Status: {t['status']}",
        f"Fault: {t['fault']} | Type: {t['type']}",
        f"Place: {site['name']}, {site['province']} | Site: {t['site']}",
        f"Asset: {t['site']} router / primary fibre span to aggregation hub",
        f"Assigned technician: {t['owner']}",
        f"Evidence: {t['evidence']}",
        f"Recommended repair/check: {t['repair']}",
        f"Service: {'Connected' if site['service_up'] else 'Unavailable'}",
        f"Repair finding: {t.get('finding') or 'Not confirmed'}",
        'SIMULATED BRIEF DELIVERY · No external message has been sent.',
    ])


def deliver(s, t):
    if t['owner']=='Unassigned':
        return
    s['inbox'].setdefault(t['owner'], {})[t['id']]=dict(time=clock(s), brief=brief(s,t))
    t['delivered']=clock(s)
    s['brief_deliveries']+=1
    event(s, f"{t['id']} · brief delivered to {t['owner']} (simulated)")


def create_ticket(s, tid, fault, kind, sid, priority, repair, evidence, status='Assigned'):
    if tid in s['tickets']:
        return s['tickets'][tid]
    eligible=[t for t in s['technicians'] if t['available'] and kind in t['skills']
              and t['province']==s['sites'][sid]['province']]
    tech=min(eligible, key=lambda t:(t['workload'],t['name'])) if eligible else None
    t=dict(id=tid, fault=fault, type=kind, site=sid, priority=priority,
           repair=repair, evidence=evidence, owner=tech['name'] if tech else 'Unassigned',
           status=status if tech else 'Awaiting assignment', created=s['elapsed'],
           delivered=None, finding='', tests_passed=False, closed_at=None, history=[])
    s['tickets'][tid]=t
    if tech:
        tech['workload']+=1
    update_ticket(s,t,t['status'],'Ticket prioritised and technician selected by skill, region and workload.')
    deliver(s,t)
    return t


def update_ticket(s,t,status,note):
    t['status']=status
    t['history'].append(dict(time=clock(s),minute=s['elapsed'],status=status,note=note))
    event(s, f"{t['id']} · {status}")


def reprioritise(s,t,priority,evidence):
    if t['priority']==priority:
        return
    t['priority']=priority
    t['evidence']=evidence
    event(s, f"{t['id']} escalated to {priority}", 'bad' if priority=='P1' else 'warn')
    deliver(s,t)


def route_check(s):
    spare=max(0,s['backup_capacity']-s['backup_background'])
    if not s['backup_healthy']:
        return False, 'Backup route unavailable', spare
    if not s['diverse']:
        return False, 'Backup shares the failed corridor', spare
    if spare<s['demand']:
        return False, f"Blocked · {spare} Mbps spare / {s['demand']} Mbps required", spare
    if (s['backup_background']+s['demand'])/s['backup_capacity']>.8:
        return False, 'Blocked · backup exceeds the 80% demo operating margin', spare
    return True, 'Healthy, diverse route · sufficient capacity', spare


def divert(s, actor='Autonomous control'):
    if not s['warning'] or s['diverted'] or s['verified']:
        return False
    safe, reason, _=route_check(s)
    if not safe:
        event(s,reason,'bad')
        return False
    s['route']='Backup';s['diverted']=True
    event(s,f'{actor} · 600 Mbps diverted to backup (simulation)','good')
    refresh_site(s)
    return True


def set_automatic(s, value):
    s['automatic']=bool(value)
    event(s,'Autonomous traffic control enabled' if value else 'Operator override · manual traffic approval','warn')


def refresh_site(s):
    connected=(s['diverted'] and s['backup_healthy']) or s['physical_up']
    s['service_up']=connected
    if not connected:
        s['latency']=None;s['loss']=None
    elif s['diverted']:
        s['latency']=27+math.sin(s['elapsed']/8)
        s['loss']=.15+.025*math.sin(s['elapsed']/5)
    else:
        s['latency']=24+.6*math.sin(s['elapsed']/8)
        s['loss']=.1+max(0,-s['rx']-12)*.025 if s['rx'] is not None else .1
    status=('Unavailable' if not connected else 'Healthy' if s['verified'] or not s['warning']
            else 'Protected' if s['diverted'] else 'At risk')
    focus=s['sites'][FOCUS]
    focus.update(status=status,service_up=connected,affected=0 if connected else focus['customers'],
                 latency=s['latency'],loss=s['loss'],traffic=s['demand'] if connected else 0)


def snapshot(s):
    primary=s['demand'] if s['physical_up'] and not s['diverted'] else 0
    diverted=s['demand'] if s['diverted'] else 0
    s['history'].append(dict(minute=s['elapsed'],rx=s['rx'],errors=s['errors'],
                             primary=primary,backup=s['backup_background']+diverted,
                             latency=s['latency'],loss=s['loss'],risk=s['risk'],
                             service_up=s['service_up'],physical_up=s['physical_up']))


def phase(s):
    t=s['elapsed']
    if t==DURATION: return 'Demo complete'
    if t>=135: return 'Repair verified · primary restored'
    if t>=125: return 'Post-repair verification'
    if t>=95: return 'Technician repairing fibre'
    if t>=75: return 'Primary failed · '+('service protected' if s['diverted'] else 'service unavailable')
    if s['diverted']:return 'Traffic protected on backup'
    if t>=45:return 'Warning · '+('capacity check' if s['automatic'] else 'awaiting operator')
    if t>=20:return 'Optical deterioration developing'
    return 'Normal operation'


def step(s):
    if s['elapsed']>=DURATION:
        s['running']=False
        return False
    # Integrate the preceding interval; incident duration is never downtime.
    for sid,site in s['sites'].items():
        counter=s['counters'][sid]
        counter['uptime' if site['service_up'] else 'downtime']+=1
        if sid==FOCUS and not s['physical_up']:
            counter['fibre_downtime']+=1
    s['elapsed']+=1
    t=s['elapsed']
    if t<20:
        s['rx']=-8+.06*math.sin(t/4);s['risk']=.08+.01*math.sin(t/7)
    elif t<75:
        progress=(t-20)/55
        s['rx']=-8-6.2*progress+.04*math.sin(t/3)
        s['risk']=min(.98,.08+.9*progress)
    elif not s['repaired']:
        s['physical_up']=False;s['rx']=None;s['risk']=None
    else:
        s['rx']=-8+.04*math.sin(t/4);s['risk']=.07
    s['errors']=0 if s['rx'] is None else max(1,round(2+20*max(0,-s['rx']-11)**2))
    for sid,site in s['sites'].items():
        if sid!=FOCUS:
            n=int(sid.rsplit('-',1)[1])
            site.update(latency=18+n*2+.6*math.sin(t/8+n),
                        loss=.15+.03*math.sin(t/7+n),traffic=400+n*30+8*math.sin(t/9+n))
    if t==45:
        s['warning']=True
        event(s,'Scripted AI warning · optical deterioration / inspect primary fibre','warn')
        create_ticket(s,'TROY-002','Suspected optical deterioration','Fibre',FOCUS,'P2',
                      'Inspect connectors, bends and splices; repair the confirmed defect.',
                      f"Receive light {s['rx']:.1f} dBm and rising errors; powered endpoints.")
    if t>=50 and s['warning'] and not s['diverted'] and not s['repaired'] and s['automatic']:
        safe,reason,_=route_check(s)
        if safe:divert(s)
        elif t==50:event(s,reason,'bad')
    if t==60 and 'TROY-002' in s['tickets']:
        update_ticket(s,s['tickets']['TROY-002'],'En route','Technician acknowledged brief (simulated).')
    if t==75:
        refresh_site(s)
        event(s,'Primary fibre lost optical signal','bad')
        ticket=s['tickets']['TROY-002']
        ticket['fault']='Suspected fibre-path interruption'
        ticket['evidence']='Loss of optical signal; both endpoints powered; physical cause unconfirmed.'
        if not s['diverted']:
            reprioritise(s,ticket,'P1','Service unavailable; no eligible traffic diversion.')
        else:
            event(s,'Customer service verified on backup','good')
        deliver(s,ticket)
    if t==95:
        update_ticket(s,s['tickets']['TROY-002'],'In progress','Crew locating the defect and inspecting fibre (simulated).')
    if t==125:
        s['repaired']=True;s['repaired_at']=t;s['physical_up']=True;s['rx']=-8;s['errors']=2;s['risk']=.07
        ticket=s['tickets']['TROY-002']
        ticket['finding']='Damaged splice enclosure and fibre section confirmed; section replaced and respliced (simulation).'
        update_ticket(s,ticket,'Verifying','Repair recorded; optical and service tests started.')
        event(s,'Physical fibre repair recorded · verification pending','good')
    if t>=135 and not s['verified']:
        stable=s['physical_up'] and s['rx'] is not None and s['rx']>-12 and s['errors']<10
        if stable and t-s['repaired_at']>=10:
            s['verified']=True;s['diverted']=False;s['route']='Primary'
            ticket=s['tickets']['TROY-002'];ticket['tests_passed']=True;ticket['closed_at']=t
            update_ticket(s,ticket,'Closed','Optical/service checks passed for 10 simulated minutes; primary restored.')
            next(x for x in s['technicians'] if x['name']==ticket['owner'])['workload']-=1
            deliver(s,ticket)
            event(s,'Primary restored · backup capacity released','good')
    if t==65:
        update_ticket(s,s['tickets']['TROY-001'],'In progress','Preventive connector inspection started (simulated).')
    if t==110:
        ticket=s['tickets']['TROY-001'];ticket.update(tests_passed=True,closed_at=t,
            finding='Connector cleaned; optical-loss test passed (simulation).')
        update_ticket(s,ticket,'Closed','Preventive work and post-work tests complete.')
        next(x for x in s['technicians'] if x['name']==ticket['owner'])['workload']-=1
        deliver(s,ticket)
    refresh_site(s)
    snapshot(s)
    if t==DURATION:
        s['running']=False
        event(s,'Demo complete · hold final results until Reset','good')
    return True


def scope_sites(s, province):
    return [x for x in s['sites'].values() if province=='All provinces' or x['province']==province]


def scope_counters(s,province):
    # Only the focus site has outages in this demo, so its counter is also
    # the duration when any service in a containing scope was unavailable.
    included=province in ['All provinces',s['sites'][FOCUS]['province']]
    down=s['counters'][FOCUS]['downtime'] if included else 0
    return dict(uptime=s['elapsed']-down,downtime=down,
                availability=100*(s['elapsed']-down)/s['elapsed'] if s['elapsed'] else None)


def ticket_list(s,province='All provinces'):
    rows=[t for t in s['tickets'].values()
          if province=='All provinces' or s['sites'][t['site']]['province']==province]
    return sorted(rows,key=lambda t:(t['status']=='Closed',t['priority'],t['created']))
