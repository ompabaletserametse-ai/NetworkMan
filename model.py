"""Deterministic, session-local demonstration model. No network actions are performed."""
from copy import deepcopy
from datetime import datetime, timedelta
import math

PROVINCES = {
 'Eastern Cape': [('Gqeberha',-33.96,25.60),('East London',-33.01,27.91),('Mthatha',-31.59,28.78),('Makhanda',-33.31,26.52),('Komani',-31.90,26.88),('Graaff-Reinet',-32.25,24.53),('Cradock',-32.16,25.62),('Butterworth',-32.33,28.15)],
 'Free State': [('Bloemfontein',-29.12,26.21),('Welkom',-27.98,26.74),('Bethlehem',-28.23,28.31),('Kroonstad',-27.65,27.23),('Sasolburg',-26.81,27.82),('Parys',-26.90,27.46),('Harrismith',-28.27,29.13),('Ficksburg',-28.87,27.88)],
 'Gauteng': [('Johannesburg',-26.20,28.04),('Pretoria',-25.75,28.19),('Roodepoort',-26.16,27.87),('Sandton',-26.11,28.05),('Midrand',-25.99,28.13),('Boksburg',-26.21,28.26),('Vereeniging',-26.67,27.93),('Centurion',-25.86,28.19)],
 'KwaZulu-Natal': [('Durban',-29.86,31.02),('Pietermaritzburg',-29.60,30.38),('Richards Bay',-28.78,32.04),('Newcastle',-27.76,29.93),('Ladysmith',-28.56,29.78),('Port Shepstone',-30.74,30.45),('Vryheid',-27.77,30.80),('Kokstad',-30.55,29.42)],
 'Limpopo': [('Polokwane',-23.90,29.45),('Tzaneen',-23.83,30.16),('Musina',-22.35,30.04),('Thohoyandou',-22.95,30.48),('Mokopane',-24.19,29.01),('Bela-Bela',-24.88,28.29),('Lephalale',-23.67,27.74),('Phalaborwa',-23.94,31.14)],
 'Mpumalanga': [('Mbombela',-25.47,30.97),('Emalahleni',-25.87,29.23),('Middelburg',-25.77,29.46),('Secunda',-26.52,29.20),('Ermelo',-26.53,29.98),('Standerton',-26.94,29.24),('Barberton',-25.79,31.05),('Piet Retief',-27.01,30.81)],
 'North West': [('Mahikeng',-25.86,25.64),('Rustenburg',-25.67,27.24),('Potchefstroom',-26.71,27.10),('Klerksdorp',-26.85,26.67),('Brits',-25.63,27.78),('Vryburg',-26.96,24.73),('Lichtenburg',-26.15,26.16),('Zeerust',-25.54,26.08)],
 'Northern Cape': [('Kimberley',-28.73,24.76),('Upington',-28.45,21.26),('Springbok',-29.67,17.88),('De Aar',-30.65,24.01),('Kuruman',-27.46,23.43),('Kathu',-27.70,23.05),('Prieska',-29.67,22.75),('Colesberg',-30.72,25.10)],
 'Western Cape': [('Cape Town',-33.92,18.42),('Stellenbosch',-33.94,18.86),('Paarl',-33.73,18.96),('Worcester',-33.65,19.45),('George',-33.96,22.46),('Mossel Bay',-34.18,22.15),('Beaufort West',-32.35,22.58),('Vredenburg',-32.91,17.99)]}
CODES = ['EC','FS','GT','KZN','LP','MP','NW','NC','WC']
SCENARIOS = {
 'Congestion': ('GT-05','Transport congestion','Major','Demand forecasting and anomaly detection (proposed)','Traffic demand exceeds the preferred operating margin.', 'Utilisation, latency and packet loss rise together.', 'Interface fault; upstream restriction', 940),
 'High latency': ('FS-03','Excessive path latency','Major','Multivariate anomaly detection (proposed)','Delay on the primary transport path.', 'High latency despite moderate load and low interface errors.', 'Upstream queueing; longer route', 430),
 'Interface errors': ('MP-03','Persistent interface errors','Major','Error-pattern classification (proposed)','Possible interface or optical degradation.', 'Interface error rate is elevated while load is moderate.', 'Optical fault; connector issue; counter anomaly', 570),
 'Device offline': ('LP-02','Backhaul router offline','Critical','Dependency-aware alarm correlation (proposed)','Router is unreachable while mains remains available.', 'Router and primary backhaul are down; other equipment is powered.', 'Router hardware fault; local power feed fault', 760),
 'Packet loss': ('GT-03','Backhaul packet loss','Major','Isolation Forest (proposed)','Queue congestion on the primary transport link.', 'Link utilisation and loss increased together; optical alarm absent.', 'Optical degradation; upstream policing', 820),
 'High router CPU': ('WC-02','Router CPU saturation','Major','Multivariate anomaly detection (proposed)','Excess control-plane workload.', 'CPU 94%; memory stable; interfaces remain up.', 'Routing update burst; software defect', 350),
 'Power failure': ('EC-02','Mains failure / battery depletion','Critical','Time-series runtime forecasting (proposed)','Mains supply failed; battery is discharging.', 'Mains absent; rectifier supply lost; battery charge falling.', 'Rectifier fault; battery sensor error', 1200),
 'Insufficient capacity': ('KZN-01','Backhaul outage / no safe alternate','Critical','Constrained path optimisation (proposed)','Primary backhaul path failed.', 'Primary link is down; alternate route has only 5% spare capacity.', 'Optical failure; upstream outage', 1650),
 'Suspected tampering': ('NW-01','Suspected battery tampering','Critical','Alarm correlation (proposed)','Possible unauthorised battery access.', 'Door alarm and battery disconnect coincide; cause unconfirmed.', 'Authorised maintenance; sensor fault', 460)}


def now(s):
 return (datetime(2026,9,30,9,0)+timedelta(minutes=s['minute'])).strftime('%H:%M')


def audit(s, what, incident='—', actor='Platform'):
 s['audit'].append(dict(time=now(s),minute=s['minute'],incident=incident,actor=actor,event=what))


def fresh_state():
 s=dict(minute=0,sites={},equipment={},links={},incidents={},tickets={},audit=[],history=[],pauses=[],stop=False,auto=False)
 for p,(province,towns) in enumerate(PROVINCES.items()):
  for n,(name,lat,lon) in enumerate(towns):
   sid=f'{CODES[p]}-{n+1:02}'
   s['sites'][sid]=dict(id=sid,name=name,province=province,lat=lat,lon=lon,technology='5G' if n%3 else '4G',status='Healthy',affected=0,priority='Hospital / emergency' if n==0 else 'Consumer / business',fresh=not(sid=='LP-08'),mains=True,charge=86.,stable=0)
   specs=[('BBU','Baseband','RAN','Processing load',44+n*2,'%'),('RU1','Radio · Sector A','RAN','Temperature',42+n,'°C'),('RU2','Radio · Sector B','RAN','Temperature',44+n,'°C'),('RU3','Radio · Sector C','RAN','Temperature',43+n,'°C'),('RTR','Backhaul router','Backhaul','CPU utilisation',32+n*3,'%'),('PWR','Rectifier / controller','Power','DC voltage',53.5,'V'),('BAT','Battery system','Power','Charge',86,'%')]
   for kind,label,group,metric,value,unit in specs:
    eid=f'{sid}-{kind}'
    s['equipment'][eid]=dict(id=eid,site=sid,kind=kind,label=label,group=group,metric=metric,value=value,unit=unit,status='Healthy',online=True,memory=42+n*2,temperature=28+n,fresh=not(sid=='LP-08'))
   s['links'][sid]=dict(id=f'L-{sid}',site=sid,endpoint=f'{CODES[p]}-{(n+1)%8+1:02}',up=True,latency=18+n*3,loss=.12+n*.04,traffic=420+n*35,capacity=1000,error=.02+n*.01,fresh=not(sid=='LP-08'))
 audit(s,'Demo initialised: 72 sites / 504 equipment records')
 trigger(s,'Packet loss'); trigger(s,'High router CPU')
 snapshot(s)
 return s


def snapshot(s):
 s['history'].append(dict(minute=s['minute'],links=deepcopy(s['links']),values={k:v['value'] for k,v in s['equipment'].items()}))
 s['history']=s['history'][-73:]


def ticket_update(s,i,text):
 if i['id'] in s['tickets']:
  t=s['tickets'][i['id']];t['updates'].append(f'{now(s)} · {text}');t['updated']=now(s)


def trigger(s,scenario):
 sid,title,severity,method,cause,evidence,alternatives,affected=SCENARIOS[scenario]
 if any(i['site']==sid and i['state']!='Resolved' for i in s['incidents'].values()): return False
 iid=f'INC-{len(s["incidents"])+1001}'
 i=dict(id=iid,scenario=scenario,site=sid,title=title,severity=severity,method=method,cause=cause,evidence=evidence,alternatives=alternatives,affected=affected,confidence=87,state='Assessing',controller='Automation',start=s['minute']-1,detected=s['minute'],resolved=None,feedback='',ticket=False,repair=False,stable=0,route=False,before=None,allocation=0,reserved_on=None,desired=200,quality_fail=False,approval='',risk='Low' if scenario=='High router CPU' else 'High')
 s['incidents'][iid]=i
 site=s['sites'][sid];site.update(status='Degraded',affected=affected,stable=0)
 if scenario=='Packet loss': s['links'][sid].update(loss=4.8,latency=128,traffic=930,error=.3)
 elif scenario=='Congestion': s['links'][sid].update(loss=3.6,latency=115,traffic=960,error=.04)
 elif scenario=='High latency': s['links'][sid].update(latency=145,loss=.4,error=.03)
 elif scenario=='Interface errors': s['links'][sid].update(error=1.2,loss=2.4,latency=42)
 elif scenario=='Device offline':
  s['equipment'][sid+'-RTR'].update(online=False,status='Offline',value=None);site['status']='Unavailable'
  s['links'][sid].update(up=False,traffic=0,latency=None,loss=None,error=None)
 elif scenario=='High router CPU': s['equipment'][sid+'-RTR'].update(value=94,status='Warning')
 elif scenario=='Power failure':
  site.update(mains=False,charge=24.);s['equipment'][sid+'-BAT'].update(value=24,status='Warning');s['equipment'][sid+'-PWR'].update(status='Critical',value=48.)
 elif scenario=='Insufficient capacity':
  site['status']='Unavailable';s['links'][sid].update(up=False,latency=None,loss=None,traffic=0,error=None)
  s['links'][s['links'][sid]['endpoint']]['traffic']=950
 elif scenario=='Suspected tampering':
  s['equipment'][sid+'-BAT'].update(online=False,value=None,status='Critical');site['charge']=None
 audit(s,f'Fault detected: {title}',iid)
 audit(s,'Related alarms grouped; simulated diagnosis recorded',iid)
 if scenario in ['Power failure','Insufficient capacity','Suspected tampering','Interface errors','Device offline']:
  s['tickets'][iid]=dict(id=f'TKT-{len(s["tickets"])+201}',incident=iid,site=sid,owner='Unassigned',status='Open',eta='Not set',updated=now(s),updates=[f'{now(s)} · Confirmed fault; investigation required.'],closed=False)
  i['ticket']=True;audit(s,'Field ticket created',iid)
 snapshot(s)
 return True


def paused(s,i):
 if s['stop']: return 'Emergency stop active'
 for p in s['pauses']:
  if p['until']>s['minute'] and (p['scope']=='All' or p['scope']==i['id'] or p['scope']==i['site'] or p['scope']==s['sites'][i['site']]['province']): return 'Automation paused'
 return ''


def plan(s,i):
 sid=i['site'];neighbor=s['links'][sid]['endpoint'];link=s['links'][neighbor]
 need=i['desired'];spare=max(0,link['capacity']-link['traffic'])
 eligible=i['scenario'] not in ['Power failure','Suspected tampering','Interface errors','Device offline']
 safe=eligible and link['up'] and link['fresh'] and spare>=need
 if i['scenario']=='Congestion':
  source=s['links'][sid]
  safe=safe and (source['traffic']-need)/source['capacity']<=.8 and (link['traffic']+need)/link['capacity']<=.8
 if i['scenario']=='High router CPU': safe=True;reason='Allowlisted diagnostic process restart; no traffic migration.'
 elif not eligible: reason='Field repair required; neighbouring radio coverage has not been validated.'
 elif not link['up'] or not link['fresh']: reason='Alternate link is down or has stale telemetry.'
 elif spare<need: reason=f'Insufficient spare capacity: {spare:.0f} Mbps available, {need} Mbps required.'
 elif i['scenario']=='Congestion' and not safe: reason='The shift must leave both paths at or below the 80% demo operating limit.'
 else: reason='Fictional alternate transport path is available; reserved capacity stays within its limit.'
 return dict(neighbor=neighbor,need=need,spare=spare,safe=safe,reason=reason,action=('Inspect and repair affected equipment' if not eligible else 'Restart allowlisted diagnostic process' if i['scenario']=='High router CPU' else 'Shift traffic to alternate backhaul path'),predicted=0 if safe else i['affected'])


def resolve(s,i):
 i.update(state='Resolved',resolved=s['minute'],before=None);s['sites'][i['site']].update(status='Healthy',affected=0)
 ticket_update(s,i,'Stability checks passed; incident resolved, ticket ready for closure.')
 audit(s,'Recovery verified; incident resolved',i['id'])


def act(s,i,command,actor='Engineer',**kwargs):
 sid=i['site'];site=s['sites'][sid]
 if command=='assess':
  p=plan(s,i);i['state']='Awaiting approval' if p['safe'] else 'Needs intervention';audit(s,p['reason'],i['id']);ticket_update(s,i,p['reason'])
 elif command=='approve':
  if i['state']!='Awaiting approval':return False
  p=plan(s,i)
  if paused(s,i) or not p['safe']:return False
  i['approval']=actor;i['state']='Acting';audit(s,'Action approved; awaiting simulated execution step',i['id'],actor)
 elif command=='reject':
  if i['state']!='Awaiting approval':return False
  i['state']='Needs intervention';audit(s,'Proposal rejected',i['id'],actor)
 elif command=='override':
  if i['state']=='Acting':i['state']='Awaiting approval'
  i['controller']=actor;audit(s,'Manual override taken',i['id'],actor)
 elif command=='handover':
  if paused(s,i) or not site['fresh']:return False
  i['controller']='Automation';audit(s,'Health check passed; control returned to automation',i['id'],actor)
 elif command=='rollback':
  if not i['before']: return False
  s['links'][sid]=deepcopy(i['before']['link']);s['equipment'][sid+'-RTR']=deepcopy(i['before']['router'])
  if i['reserved_on']:
   nl=s['links'][i['reserved_on']];nl['traffic']=max(0,nl['traffic']-i['allocation'])
  site.update(status=i['before']['status'],affected=i['affected'])
  i.update(state='Needs intervention',route=False,allocation=0,reserved_on=None,before=None,resolved=None,quality_fail=False)
  audit(s,'Change rolled back; human intervention required',i['id'],actor)
 elif command=='repair':
  if i['state']=='Resolved':return False
  site.update(mains=True,charge=86.,fresh=True)
  for d in s['equipment'].values():
   if d['site']==sid:d.update(online=True,status='Healthy',fresh=True)
  s['equipment'][sid+'-BAT']['value']=86;s['equipment'][sid+'-PWR']['value']=53.5;s['equipment'][sid+'-RTR']['value']=38
  s['equipment'][sid+'-BBU']['value']=48
  for rk in ['RU1','RU2','RU3']:s['equipment'][sid+'-'+rk]['value']=44
  s['links'][sid].update(up=True,loss=.2,latency=28,error=.03,fresh=True)
  if not i['route']:s['links'][sid]['traffic']=500
  i.update(repair=True,stable=0,state='Verifying');site.update(status='Degraded',stable=0)
  audit(s,'Physical repair recorded; three stability checks required',i['id'],actor);ticket_update(s,i,'Repair complete; stability checks started.')
 elif command=='close':
  if i['state']!='Resolved' or not i['repair'] or i['stable']<3:return False
  s['tickets'][i['id']].update(status='Closed',closed=True);audit(s,'Ticket closed after stable repair',i['id'],actor)
 snapshot(s)
 return True


def advance(s):
 s['minute']+=5
 for i in list(s['incidents'].values()):
  sid=i['site'];site=s['sites'][sid]
  if i['state']=='Resolved':continue
  # Power depletion is physical and continues while automation is paused.
  if i['scenario']=='Power failure' and not i['repair']:
   site['charge']=max(0,site['charge']-8);s['equipment'][sid+'-BAT']['value']=site['charge']
   if site['charge']==0:
    site['status']='Unavailable'
    for d in s['equipment'].values():
     if d['site']==sid:d.update(online=False,status='Offline',value=None)
    s['links'][sid].update(up=False,traffic=0,latency=None,loss=None,error=None)
  if paused(s,i):continue
  if i['state']=='Assessing' and not i.get('guided'):act(s,i,'assess')
  if s['auto'] and not i.get('guided') and i['risk']=='Low' and i['controller']=='Automation' and i['state']=='Awaiting approval':
   act(s,i,'approve','Automation (allowlisted low risk)')
  if i['state']=='Acting':
   p=plan(s,i)
   if not p['safe']:i['state']='Needs intervention';audit(s,'Execution blocked: '+p['reason'],i['id']);continue
   i['before']=dict(link=deepcopy(s['links'][sid]),router=deepcopy(s['equipment'][sid+'-RTR']),status=site['status'])
   if i['scenario']=='High router CPU':s['equipment'][sid+'-RTR'].update(value=38,status='Healthy')
   else:
    s['links'][p['neighbor']]['traffic']+=p['need'];s['links'][sid].update(traffic=max(0,s['links'][sid]['traffic']-p['need']),latency=32,loss=.4,error=.04,up=True)
    i.update(route=True,allocation=p['need'],reserved_on=p['neighbor'])
   site.update(affected=0,status='Degraded');i['state']='Verifying';i['stable']=0
   audit(s,'Simulated action executed; verification started',i['id']);ticket_update(s,i,'Recovery action executed.')
  elif i['state']=='Verifying':
   if i.get('issue_analysis'):
    from issues import checks
    if not all(ok for _,ok in checks(s,i)):
     if i['before']:act(s,i,'rollback','Verification guard')
     else:i['state']='Needs intervention';audit(s,'Verification failed: measured targets unmet',i['id'])
     i['issue_analysis']['result']='Failed';continue
   if i['quality_fail'] and i['before']:
    act(s,i,'rollback','Verification guard');continue
   i['stable']+=1;site['stable']=i['stable'];audit(s,f'Stability check {i["stable"]}/3 passed',i['id'])
   if i['stable']>=3:
    if i['route'] and i['scenario']=='Congestion':
     audit(s,'Balanced routing retained; service targets verified',i['id']);resolve(s,i)
    elif i['route'] and not i['repair']:
     i['state']='Mitigated';site['status']='Degraded';audit(s,'Service restored on alternate path; original fault remains',i['id'])
    else:
     if i['route']:
      s['links'][i['reserved_on']]['traffic']-=i['allocation'];s['links'][sid]['traffic']+=i['allocation'];i.update(route=False,allocation=0,reserved_on=None)
      audit(s,'Stable primary path restored; temporary allocation released',i['id'])
     resolve(s,i)
 snapshot(s)


def site_list(s,province='All provinces'):
 return [x for x in s['sites'].values() if province=='All provinces' or x['province']==province]


def series(s,sid,metric,device=False):
 # Historical baseline is synthetic. Discrete simulation checkpoints follow it.
 value=s['equipment'][sid]['value'] if device else s['links'][sid][metric]
 baseline=({'BBU':48,'RU1':44,'RU2':46,'RU3':45,'RTR':35,'PWR':53.5,'BAT':86}[s['equipment'][sid]['kind']] if device else {'latency':28,'loss':.2,'traffic':500,'error':.03}[metric])
 points=[(-30+j*5,round(baseline*(1+.05*math.sin(j)),2)) for j in range(6)]
 for h in s['history']:
  v=h['values'].get(sid) if device else h['links'][sid][metric]
  points.append((h['minute'],v))
 return points
