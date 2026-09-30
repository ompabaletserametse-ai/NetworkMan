"""Inspectable, deterministic issue analysis. Proposed ML methods are labels, not models."""
from copy import deepcopy
from model import SCENARIOS, trigger, audit, act, advance, plan, paused, now

ISSUES = {
 'High latency': dict(metric='latency',unit='ms',threshold=80,scope='Network links',scenario='High latency',method='Multivariate anomaly detection',inputs='Delay history, traffic load, packet loss and interface errors',purpose='Learn normal delay patterns and flag unusual combinations.',response='Inspect the delayed path and assess an alternate route.',impact='Slow applications, delayed voice and poor interactive service.'),
 'Packet loss': dict(metric='loss',unit='%',threshold=1,scope='Network links',scenario='Packet loss',method='Diagnostic classification',inputs='Loss, link utilisation, interface errors and reachability',purpose='Distinguish congestion from physical or interface problems.',response='Rebalance traffic for congestion; investigate equipment when errors are elevated.',impact='Retransmissions, broken calls and unreliable connections.'),
 'Congestion': dict(metric='utilisation',unit='%',threshold=80,scope='Network links',scenario='Congestion',method='Demand forecasting + anomaly detection',inputs='Traffic/capacity, latency, loss and interface error rate',purpose='Predict saturation and identify demand-related service degradation.',response='Move a checked traffic allocation to an alternate connected path.',impact='Queueing raises delay and loss for customers sharing the link.'),
 'Interface errors': dict(metric='error',unit='%',threshold=.5,scope='Network interfaces',scenario='Interface errors',method='Error-pattern classification',inputs='Errored-frame percentage, loss, load and interface state',purpose='Recognise persistent patterns consistent with interface degradation.',response='Create a repair ticket and inspect the affected interface.',impact='Corrupted frames can cause retransmissions and service degradation.'),
 'High CPU': dict(metric='cpu',unit='%',threshold=80,scope='Routers',scenario='High router CPU',method='Multivariate anomaly detection',inputs='Device CPU, memory, uptime and link state',purpose='Identify unusual processing load relative to the device baseline.',response='Inspect workload; use the allowlisted demo diagnostic-process restart.',impact='Processing delays may affect management and routing responsiveness.'),
 'Device offline': dict(metric='online',unit='',threshold=0,scope='Equipment',scenario='Device offline',method='Dependency-aware alarm correlation',inputs='Equipment reachability, mains, batteries and backhaul state',purpose='Group dependent alarms and distinguish device faults from site-wide outages.',response='Assess fault dependencies and dispatch repair when remote recovery is unsafe.',impact='Loss of equipment service; impact depends on the failed component.')}


def measure(s,kind,sid,eid=None):
 spec=ISSUES[kind];l=s['links'][sid]
 if kind=='Device offline':
  if eid:
   d=s['equipment'][eid];return None if not d['fresh'] else (1 if d['online'] else 0)
  devices=[d for d in s['equipment'].values() if d['site']==sid]
  if any(d['fresh'] and not d['online'] for d in devices):return 0
  return 1 if all(d['fresh'] for d in devices) else None
 if kind=='High CPU':
  d=s['equipment'][sid+'-RTR'];return d['value'] if d['fresh'] and d['online'] else None
 if not l['fresh'] or not l['up']:return None
 return 100*l['traffic']/l['capacity'] if spec['metric']=='utilisation' else l[spec['metric']]


def affected(s,kind,province='All provinces'):
 rows=[]
 for sid,site in s['sites'].items():
  if province!='All provinces' and province!=site['province']:continue
  eids=[d['id'] for d in s['equipment'].values() if d['site']==sid] if kind=='Device offline' else [None]
  for eid in eids:
   val=measure(s,kind,sid,eid)
   if val is not None and (val==0 if kind=='Device offline' else val>ISSUES[kind]['threshold']):
    linked=next((i for i in reversed(list(s['incidents'].values())) if i['site']==sid and i['state']!='Resolved'),None)
    rows.append(dict(site=sid,asset=eid or (sid+'-RTR' if kind=='High CPU' else s['links'][sid]['id']),value=val,incident=linked['id'] if linked else None,status=linked['state'] if linked else 'Needs investigation',severity=linked['severity'] if linked else 'Major'))
 return rows


def capture(s,i):
 sid=i['site'];l=s['links'][sid];d=s['equipment'][sid+'-RTR'];site=s['sites'][sid]
 return dict(latency=l['latency'],loss=l['loss'],utilisation=100*l['traffic']/l['capacity'],error=l['error'],cpu=d['value'],online=d['online'],fresh=l['fresh'] and d['fresh'],mains=site['mains'],charge=site['charge'],customers=site['affected'],offline_count=sum(not d['online'] for d in s['equipment'].values() if d['site']==sid))


def ensure_demo(s,kind):
 scenario=ISSUES[kind]['scenario'];sid=SCENARIOS[scenario][0]
 i=next((i for i in reversed(list(s['incidents'].values())) if i['site']==sid and i['state']!='Resolved'),None)
 if i is None:
  trigger(s,scenario);i=list(s['incidents'].values())[-1]
 i['guided']=True
 return i


def analyse(s,i,kind,actor):
 if i['state'] not in ['Assessing','Awaiting approval','Needs intervention']:return False
 v=capture(s,i)
 reading=measure(s,kind,i['site'])
 if reading is None or (reading!=0 if kind=='Device offline' else reading<=ISSUES[kind]['threshold']):return False
 if not v['fresh']:
  audit(s,'Analysis blocked: refresh stale telemetry before diagnosis',i['id'],actor);return False
 cause='Further investigation needed';alternative='Upstream issue or incomplete telemetry';rule='No supported pattern detected.'
 if kind=='High CPU':
  cause='Elevated device processing load';alternative='Routing-update burst or software issue'
  rule=f"CPU {v['cpu']}% is above the 80% demo limit; memory stays at {s['equipment'][i['site']+'-RTR']['memory']}%."
 elif kind=='Device offline':
  cause='Local device fault suspected' if v['mains'] else 'Site power failure suspected'
  alternative='Local power feed failure or equipment fault';rule='Reachability is checked alongside mains, battery and backhaul state.'
 elif v['error'] is not None and v['error']>.5:
  cause='Interface degradation suspected';alternative='Optical/connector fault or counter anomaly'
  rule=f"Interface errors {v['error']:.2f}% exceed 0.5%; this supports interface investigation."
 elif v['utilisation']>80 and (v['loss'] or 0)>1 and (v['latency'] or 0)>80:
  cause='Transport congestion likely';alternative='Upstream policing or a simultaneous path fault'
  rule='Utilisation >80%, latency >80 ms and packet loss >1% coincide while interface errors remain low.'
 elif kind=='High latency':
  cause='Delay on the transport path';alternative='Upstream queueing or a longer route'
  rule='Latency exceeds 80 ms without matching high load or interface errors; cause remains uncertain.'
 elif kind=='Packet loss':
  cause='Packet delivery impairment';alternative='Congestion, policing or interface degradation'
  rule='Loss exceeds 1%; inspect load and errors before choosing a response.'
 result=dict(kind=kind,before=deepcopy(v),cause=cause,alternative=alternative,rule=rule,time=now(s),minute=s['minute'],reviewed=False,method=ISSUES[kind]['method'],result=None)
 i['issue_analysis']=result;i['guided']=True
 i['cause']=cause;i['evidence']=rule;i['alternatives']=alternative
 act(s,i,'assess',actor)
 audit(s,f'Issue analysis ({kind}): {cause}. Explicit demo rule; no ML inference.',i['id'],actor)
 return True


def review(s,i,actor):
 a=i.get('issue_analysis')
 if not a:return False
 if capture(s,i)!=a['before']:
  audit(s,'Recommendation expired: measurements changed; analyse again',i['id'],actor);return False
 a['reviewed']=True;a['plan']=deepcopy(plan(s,i));audit(s,'Recommendation reviewed with capacity and operating limits',i['id'],actor);return True


def approve(s,i,actor):
 a=i.get('issue_analysis')
 if not a or not a['reviewed'] or capture(s,i)!=a['before']:return False
 return act(s,i,'approve',actor)


def checks(s,i):
 a=i.get('issue_analysis');kind=a['kind'] if a else 'Congestion';v=capture(s,i)
 if kind=='High CPU':return [('Router reachable',v['online']),('CPU ≤80%',v['cpu'] is not None and v['cpu']<=80)]
 if kind=='Device offline':return [('All site equipment reachable',v['offline_count']==0),('Backhaul up',s['links'][i['site']]['up'])]
 if kind=='Interface errors':return [('Interface errors ≤0.5%',v['error'] is not None and v['error']<=.5),('Packet loss ≤1%',v['loss'] is not None and v['loss']<=1)]
 tests=[('Latency ≤80 ms',v['latency'] is not None and v['latency']<=80),('Packet loss ≤1%',v['loss'] is not None and v['loss']<=1)]
 if kind=='Congestion':
  n=s['links'][s['links'][i['site']]['endpoint']]
  tests += [('Primary utilisation ≤80%',v['utilisation']<=80),('Alternate utilisation ≤80%',n['traffic']/n['capacity']<=.8)]
 return tests


def execute(s,i):
 if i['state']!='Acting' or paused(s,i):return False
 advance(s);return True


def verify(s,i,actor):
 if i['state']!='Verifying' or paused(s,i):return False
 if not all(ok for _,ok in checks(s,i)):
  if i['before']:act(s,i,'rollback','Verification guard')
  else:i['state']='Needs intervention';audit(s,'Verification failed: measured targets unmet',i['id'],actor)
  i['issue_analysis']['result']='Failed';return False
 advance(s)
 if i['state']=='Needs intervention':i['issue_analysis']['result']='Failed'
 elif i['state'] in ['Resolved','Mitigated']:i['issue_analysis']['result']='Passed'
 audit(s,f"Measured verification: {i['stable']}/3 stable samples",i['id'],actor)
 return True
