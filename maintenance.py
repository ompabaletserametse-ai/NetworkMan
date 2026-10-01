"""Evidence-led corrective and preventive maintenance demonstrations. No model inference."""
from copy import deepcopy
from statistics import mean
from model import audit, now

DATA_SOURCES = [
 ('Optical measurements','RX/TX power, laser bias, temperature and vendor limits','Device DOM telemetry'),
 ('Network symptoms','Loss of signal, link flaps, interface errors, loss and latency','Interface counters / alarms'),
 ('Asset context','Port, optic model, cable route, splice records and repair history','Inventory / GIS / work orders'),
 ('Fault location','Distance to optical event and trace from a known test end','OTDR test or instrument integration'),
 ('External context','Site power, environmental alarm and verified local reports','Site sensors / operator reports'),
 ('Ground truth','Confirmed cause, photos/test references, repair and post-test readings','Technician findings')]


def init_case(s,i):
 if 'maintenance' in i:return i['maintenance']
 fibre=i['scenario']=='Fibre damage'
 m=dict(asset='FIB-GT06-07' if fibre else i['site'],fault='Possible fibre-path damage' if fibre else i['cause'],confirmed_cause='',technician='',action='',evidence_ref='',tests=False,tests_at=None,test_values=None,otdr_km=None,repair_recorded_at=None,service_restored_at=None,pre_fault_traffic=600 if fibre else 500,failure_snapshot=deepcopy(s['links'][i['site']]),captured_at=now(s))
 i['maintenance']=m
 return m


def ensure(s):
 for i in s['incidents'].values():
  if i['ticket']:init_case(s,i)
 if 'watch' not in s:
  s['watch']={
   'WATCH-01':dict(id='WATCH-01',site='GT-04',asset='GT-04-RTR / optic',kind='Optical power',unit='dBm',values=[-8,-8.2,-9,-10,-11.3,-12.4,-13.7,-15],limit=-16,rule='Receive power dropped by ≥3 dB across the sample window, or is within 2 dB of the demo warning limit.',action='Inspect/clean connectors, compare both-end DOM and commission an OTDR test if loss persists.',tools='Optical power meter, inspection kit; OTDR if indicated',method='Time-series anomaly detection / trend forecasting (proposed)'),
   'WATCH-02':dict(id='WATCH-02',site='MP-05',asset='MP-05-RU2',kind='Radio temperature',unit='°C',values=[43,44,46,49,53,59,64,72],limit=75,rule='Temperature increased by ≥15°C and latest reading is within 5°C of the demo warning limit.',action='Inspect cooling, airflow, seals and environmental exposure; compare temperature with load.',tools='Temperature probe, approved cooling-service tools',method='Multivariate anomaly detection (proposed)'),
   'WATCH-03':dict(id='WATCH-03',site='EC-04',asset='EC-04-BAT',kind='Battery capacity health',unit='%',values=[94,92,88,84,79,74,69,65],limit=70,rule='Measured usable capacity is below 70% of nominal in the demo history.',action='Schedule a controlled capacity test and review replacement if degradation is confirmed.',tools='Battery analyser and compatible replacement after confirmation',method='Degradation modelling (proposed)')}
 s.setdefault('preventive_orders',{})


def corrective_brief(s,i):
 m=init_case(s,i);sid=i['site'];fibre=i['scenario']=='Fibre damage';l=m.get('failure_snapshot',s['links'][sid])
 if fibre:
  suspect='Fibre-path interruption; fire is suspected from an unverified report.'
  if m['confirmed_cause']:suspect=m['confirmed_cause']+' (technician recorded)'
  evidence=[('Primary physical fibre','Up' if l.get('physical_up',True) else 'Loss of signal','Interface alarm'),('Received optical power',str(l.get('rx_dbm','Unavailable'))+' dBm','Simulated DOM'),('Transmit optical power',str(l.get('tx_dbm','Unavailable'))+' dBm','Simulated DOM'),('Both-end equipment','Powered; local mains available','Site telemetry'),('Route report','Reported smoke near cable corridor; unconfirmed','Simulated operator report'),('OTDR event',f"{m['otdr_km']:.1f} km from GT-06 test end" if m['otdr_km'] is not None else 'Not available — request a test','Simulated trace import' if m['otdr_km'] is not None else 'Missing instrument data')]
  steps=['Confirm both-end power, ports and optic readings; exclude optic or patch-lead faults.','Localise the optical event using a qualified OTDR test and cable-route records.','Inspect the indicated route section and confirm the physical cause.','Repair/splice or replace the confirmed damaged section under the approved field procedure.','Record loss/OTDR results, restore the primary route and verify service stability.']
  kit='Fibre-trained crew; OTDR, optical loss-test kit, inspection/cleaning kit, compatible cable/splice materials.'
  unknown='Loss of light alone cannot identify fire, a cut, a disconnection, or a remote optic fault. OTDR distance is along cable, not a GPS coordinate.'
 else:
  suspect=m['confirmed_cause'] or i['cause'];evidence=[('Recorded symptom',i['evidence'],'Incident measurements'),('Mains','Available' if s['sites'][sid]['mains'] else 'Failed','Site telemetry'),('Battery',str(s['sites'][sid]['charge'])+'%','Battery controller'),('Physical finding',m['confirmed_cause'] or 'Not yet confirmed','Technician')]
  steps=['Review alarms, asset history and both-end dependencies.','Confirm the failed component on site before choosing a replacement.','Record corrective work and supporting test evidence.','Verify equipment, link quality and stable service before closure.']
  kit='Appropriately qualified technician; vendor-approved test instruments and compatible spares after diagnosis.'
  unknown='Remote evidence narrows the investigation; technician findings establish the physical cause.'
 return dict(cause=suspect,evidence=evidence,steps=steps,kit=kit,unknown=unknown,method='Alarm correlation + diagnostic classification + approved procedure retrieval (proposed)')


def record_findings(s,i,cause,technician,action,reference):
 if not all(str(x).strip() for x in [cause,technician,action,reference]):return False
 m=init_case(s,i)
 if s['tickets'][i['id']]['closed']:return False
 m.update(confirmed_cause=cause.strip(),technician=technician.strip(),action=action.strip(),evidence_ref=reference.strip(),tests=False,tests_at=None)
 audit(s,'Technician findings recorded: '+cause.strip(),i['id'],technician.strip())
 return True


def postrepair_ok(s,i):
 l=s['links'][i['site']]
 ok=l['up'] and l['fresh'] and l.get('physical_up',True) and l['loss'] is not None and l['loss']<=1 and l['error'] is not None and l['error']<=.5
 ok=ok and all(d['online'] and d['fresh'] for d in s['equipment'].values() if d['site']==i['site'])
 if i['scenario']=='Fibre damage':ok=ok and l.get('rx_dbm',-99)>=-16
 return bool(ok)


def field_tests(s,i):
 if not i['repair']:return False
 m=init_case(s,i);l=s['links'][i['site']];ok=postrepair_ok(s,i)
 m['tests']=bool(ok);m['tests_at']=now(s)
 m['test_values']=deepcopy({k:l.get(k) for k in ['physical_up','rx_dbm','latency','loss','error']})
 audit(s,'Post-repair measurements '+('passed' if ok else 'failed')+' (simulation)',i['id'],m['technician'] or 'Engineer')
 return bool(ok)


def ready_to_close(s,i):
 m=init_case(s,i);l=s['links'][i['site']]
 return bool(m['confirmed_cause'] and m['technician'] and m['action'] and m['evidence_ref'] and m['tests'] and i['repair'] and i['stable']>=3 and i['state']=='Resolved' and not i['route'] and postrepair_ok(s,i))


def watch_result(w):
 vals=w['values'];change=vals[-1]-vals[0]
 if w['kind']=='Optical power':flag=change<=-3 or vals[-1]<=w['limit']+2
 elif w['kind']=='Radio temperature':flag=change>=15 and vals[-1]>=w['limit']-5
 else:flag=vals[-1]<w['limit']
 return dict(priority='High' if flag else 'Monitor',change=change,latest=vals[-1],slope=change/(len(vals)-1),recommendation='Review within 24 hours' if flag else 'Continue monitoring')


def create_order(s,w,actor):
 key=w['id']
 if key in s['preventive_orders']:return s['preventive_orders'][key]
 r=watch_result(w)
 o=dict(id='PM-'+str(len(s['preventive_orders'])+301),watch=key,site=w['site'],asset=w['asset'],owner='Unassigned',window=r['recommendation'],status='Planned',notes='',created=now(s))
 s['preventive_orders'][key]=o;audit(s,'Preventive order '+o['id']+' created for '+w['asset'],actor=actor)
 return o


def briefing(s,i):
 b=corrective_brief(s,i);m=init_case(s,i);t=s['tickets'][i['id']]
 return '\n'.join([f"TECHNICIAN BRIEF · {t['id']} / {i['id']}",f"Site: {i['site']} | Asset: {m['asset']}",f"Service: {i['state']} | Physical repair: {'recorded' if i['repair'] else 'outstanding'}",f"Owner: {t['owner']} | ETA: {t['eta']}",f"Suspected / recorded cause: {b['cause']}",'EVIDENCE']+[f'{a}: {v} [{source}]' for a,v,source in b['evidence']]+['CORRECTIVE PLAN']+b['steps']+['CREW & EQUIPMENT',b['kit'],'UNCERTAINTY',b['unknown'],f"Technician finding: {m['confirmed_cause'] or 'Not recorded'}",f"Action: {m['action'] or 'Not recorded'}",f"Evidence reference: {m['evidence_ref'] or 'Not recorded'}",'DEMONSTRATION: all observations and recommendations are simulated.'])
