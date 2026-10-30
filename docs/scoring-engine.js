/* Shared browser/Node evaluator. No network, model calls, or external dependencies. */
const DOMAINS = {
  argument: ['research-question','motivation-gap','contribution-calibration','literature-positioning'],
  evidence: ['method-specification','design-validity','comparison-fairness','analysis-uncertainty','robustness-failures','claim-evidence-entailment'],
  consistency: ['concept-definitions','notation-units','numbers-denominators','cross-section-alignment'],
  communication: ['title-abstract','introduction-logic','paragraph-sentence-logic','jargon-acronyms','reader-teachback','figures-tables'],
  transparency: ['reproducibility-artifacts','limitations-transfer','ethics-disclosures','venue-compliance']
};
const CORE = new Set(['research-question','design-validity','claim-evidence-entailment','concept-definitions','numbers-denominators','cross-section-alignment']);
const EMPIRICAL = [5,5,5,5,7,7,6,6,4,5,5,5,5,5,3,3,2,2,3,2,3,3,2,2];
const COMPUTED = new Set(['rubric_sha256','rubric_title','profile_title','score_out_of_100','earned_subtotal','nominal_weight','applicable_weight','assessed_weight','excluded_weight','assessed_weight_percent','assessment_coverage_percent','missing_assessment_bounds','status','readiness','domain_scores','active_blockers','core_deficits','low_confidence_core_checks','revision_priorities','limitations','interpretation','comparison','strictness','scoring_policy_id','scoring_policy_sha256','effective_score_out_of_100','score_cap_out_of_100','score_caps','strict_gate_failures']);
const LIMITATIONS = [
  'Editorial assessment of the inspected revision and evidence; not scientific certification, an acceptance probability, or submission approval.',
  'Evidence records identify observations and locations; their presence does not verify that an observation is true or sufficient.',
  'Confidence is reported separately and never multiplies a rating. Missing-assessment bounds are possible score bounds, not statistical confidence intervals.',
  'A numeric score does not resolve a critical blocker. Reviewed is not submission approval; it means the assessment requirements were met.'
];
const clone = value => JSON.parse(JSON.stringify(value));
const require = (ok, message) => { if (!ok) throw new Error(message); };
const text = (v, label) => require(typeof v === 'string' && v.trim().length > 0, `${label} must be a nonempty string`);
const id = (v, label) => { text(v,label); require(!/\s/u.test(v), `${label} must not contain whitespace`); };
function object(v,label,required,optional=[]) {
  require(v && typeof v === 'object' && !Array.isArray(v), `${label} must be an object`);
  require(required.every(k => Object.hasOwn(v,k)) && Object.keys(v).every(k => required.includes(k)||optional.includes(k)), `${label}: missing or unexpected fields`);
}
const sameKeys = (a,b) => a.length === b.length && a.every(k => b.includes(k));
function jsonValues(v) {
  if (typeof v === 'number') require(Number.isFinite(v),'Numbers must be finite');
  else if (v && typeof v === 'object') Object.values(v).forEach(jsonValues);
  else require(v === null || ['string','boolean'].includes(typeof v),'Only JSON-compatible values are allowed');
}
const canonical = v => v && typeof v === 'object' ? Array.isArray(v) ? `[${v.map(canonical).join(',')}]` : `{${Object.keys(v).sort().map(k=>`${JSON.stringify(k)}:${canonical(v[k])}`).join(',')}}` : JSON.stringify(v);
/* Synchronous SHA-256 keeps the exported evaluator usable in Node parity tests. */
export function fingerprint(value) {
  const bytes = new TextEncoder().encode(canonical(value));
  const length = Math.ceil((bytes.length+9)/64)*64;
  const data = new Uint8Array(length); data.set(bytes); data[bytes.length]=128;
  const dv = new DataView(data.buffer); dv.setUint32(length-8,Math.floor(bytes.length/536870912)); dv.setUint32(length-4,bytes.length*8);
  const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  const H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19], W=new Uint32Array(64);
  const rotr=(x,n)=>(x>>>n)|(x<<(32-n));
  for(let offset=0;offset<length;offset+=64) {
    for(let i=0;i<16;i++) W[i]=dv.getUint32(offset+i*4);
    for(let i=16;i<64;i++){let a=W[i-15],b=W[i-2];W[i]=(W[i-16]+(rotr(a,7)^rotr(a,18)^(a>>>3))+W[i-7]+(rotr(b,17)^rotr(b,19)^(b>>>10)))>>>0;}
    let [a,b,c,d,e,f,g,h]=H;
    for(let i=0;i<64;i++){let t1=(h+(rotr(e,6)^rotr(e,11)^rotr(e,25))+((e&f)^(~e&g))+K[i]+W[i])>>>0,t2=((rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c)))>>>0;h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;}
    [a,b,c,d,e,f,g,h].forEach((v,i)=>H[i]=(H[i]+v)>>>0);
  }
  return H.map(v=>v.toString(16).padStart(8,'0')).join('');
}
function validateRubric(r) {
  jsonValues(r);
  object(r,'rubric',['version','rubric_id','max_rating','default_profile','core_threshold','domains','criteria','profiles']);
  require(r.version===2 && r.max_rating===4 && r.core_threshold===2,'Unsupported rubric version or rating scale');
  id(r.rubric_id,'rubric_id'); id(r.default_profile,'default_profile');
  require(Array.isArray(r.domains)&&r.domains.length>0,'Rubric needs domains');
  const domains=new Set();
  for(const d of r.domains){object(d,'domain',['id','title']);id(d.id,'domain.id');text(d.title,'domain.title');require(!domains.has(d.id),'Duplicate domain');domains.add(d.id);}
  require(Array.isArray(r.criteria)&&r.criteria.length>0,'Rubric needs criteria');
  const catalog={};
  for(const c of r.criteria){
    object(c,'rubric criterion',['id','title','domain','description','core','allow_not_applicable','anchors','checks','role_ids']);
    id(c.id,'criterion.id'); require(!catalog[c.id],'Duplicate criterion'); text(c.title,'criterion.title');text(c.description,'criterion.description');
    require(domains.has(c.domain),'Unknown domain'); require(typeof c.core==='boolean'&&typeof c.allow_not_applicable==='boolean','Invalid core/applicability flag');require(!(c.core&&c.allow_not_applicable),'Core criteria cannot be N/A');
    object(c.anchors,'anchors',['0','1','2','3','4']);Object.values(c.anchors).forEach(x=>text(x,'anchor'));require(new Set(Object.values(c.anchors).map(x=>x.trim())).size===5,'Rating anchors must be distinct');
    require(Array.isArray(c.checks)&&c.checks.length>0&&Array.isArray(c.role_ids),'Invalid checks or roles');[...c.checks,...c.role_ids].forEach(x=>text(x,'check/role'));catalog[c.id]=c;
  }
  require([...domains].every(d=>r.criteria.some(c=>c.domain===d)),'Every domain needs criteria');
  require(r.profiles&&typeof r.profiles==='object'&&!Array.isArray(r.profiles)&&Object.hasOwn(r.profiles,r.default_profile),'Invalid rubric profiles');
  for(const [name,p] of Object.entries(r.profiles)){
    id(name,'profile');object(p,'profile',['title','weights','guidance']);text(p.title,'profile.title');require(sameKeys(Object.keys(p.weights),Object.keys(catalog)),'Profile weights must use exact criterion IDs');
    require(Object.values(p.weights).every(w=>typeof w==='number'&&Number.isFinite(w)&&w>=0)&&Math.abs(Object.values(p.weights).reduce((a,b)=>a+b,0)-100)<1e-8,'Profile weights must sum to 100');
    require(p.guidance&&typeof p.guidance==='object'&&!Array.isArray(p.guidance)&&Object.keys(p.guidance).length>0&&Object.keys(p.guidance).every(k=>Object.hasOwn(catalog,k)),'Invalid profile guidance');Object.values(p.guidance).forEach(v=>text(v,'guidance'));
  }
  if(r.rubric_id==='paper-writing-v2'){
    require(sameKeys(Object.keys(catalog),Object.values(DOMAINS).flat())&&sameKeys([...domains],Object.keys(DOMAINS)),'Canonical 24-criterion catalog required');
    for(const c of r.criteria)require(DOMAINS[c.domain].includes(c.id)&&(!CORE.has(c.id)||c.core)&&c.allow_not_applicable===(c.id==='figures-tables'),'Canonical criterion domain, core, or N/A rule changed');
    require(['empirical-ml','theory','clinical','systematic-review'].every(k=>r.profiles[k]),'All four profiles required');
    Object.values(DOMAINS).flat().forEach((cid,i)=>require(r.profiles['empirical-ml'].weights[cid]===EMPIRICAL[i],'Canonical empirical weights required'));
  }
  return catalog;
}
function evidence(records,label,required,sourceIds=true){
  require(Array.isArray(records)&&(!required||records.length>0),`${label} needs evidence`);
  for(const e of records){object(e,label,['locator','observation'],sourceIds?['source_id']:[]);text(e.locator,`${label}.locator`);text(e.observation,`${label}.observation`);if(e.source_id!==undefined)id(e.source_id,`${label}.source_id`);}
}
function validateAssessment(data,r,catalog,hash){
  jsonValues(data);object(data,'assessment',['version','rubric_id','profile','subject','reviewer','evaluated_at','criteria','critical_blockers'],[...COMPUTED]);
  require(data.version===2&&data.rubric_id===r.rubric_id,'Assessment version or rubric does not match');
  if(data.rubric_sha256!==undefined)require(data.rubric_sha256===hash,'Assessment rubric fingerprint does not match');
  require(Object.hasOwn(r.profiles,data.profile),'Unknown profile');object(data.subject,'subject',['id','revision'],['artifact_sha256']);id(data.subject.id,'subject.id');text(data.subject.revision,'subject.revision');
  if(data.subject.artifact_sha256!==undefined)require(/^[0-9a-f]{64}$/.test(data.subject.artifact_sha256),'Invalid artifact fingerprint');
  object(data.reviewer,'reviewer',['id','type']);id(data.reviewer.id,'reviewer.id');require(['human','agent'].includes(data.reviewer.type),'Invalid reviewer type');
  require(typeof data.evaluated_at==='string'&&/^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?$/.test(data.evaluated_at)&&!Number.isNaN(Date.parse(data.evaluated_at)),'evaluated_at must be an ISO date or datetime');
  const datePart=data.evaluated_at.slice(0,10),[y,m,d]=datePart.split('-').map(Number);require(y>=1&&m>=1&&m<=12&&d>=1&&d<=new Date(Date.UTC(y,m,0)).getUTCDate(),'Invalid evaluation calendar date');
  if(data.evaluated_at.includes('T')){const time=data.evaluated_at.slice(11,19).split(':').map(Number);require(time[0]<=23&&time[1]<=59&&time[2]<=59,'Invalid evaluation time');}
  require(Array.isArray(data.criteria)&&data.criteria.length>0,'Assessment needs criteria');const rows={};
  for(const row of data.criteria){
    object(row,'rating criterion',['id','status','rating','confidence','evidence','rationale'],['action','applicability_reason']);
    id(row.id,'criterion.id');require(Object.hasOwn(catalog,row.id)&&!Object.hasOwn(rows,row.id),'Unknown or duplicate criterion');text(row.rationale,`${row.id}.rationale`);if(row.action!==undefined)text(row.action,'action');
    require(['assessed','unassessed','not_applicable'].includes(row.status),'Invalid criterion status');
    if(row.status==='assessed')require(Number.isInteger(row.rating)&&row.rating>=0&&row.rating<=4&&['low','medium','high'].includes(row.confidence),'Assessed rows need a 0–4 integer rating and confidence');
    else require(row.rating===null&&row.confidence===null,'Unassessed and N/A rows need null rating and confidence');
    if(row.status==='not_applicable'){require(!catalog[row.id].core&&catalog[row.id].allow_not_applicable,'Criterion does not permit N/A');text(row.applicability_reason,'applicability_reason');}
    else require(row.applicability_reason===undefined,'Applicability reason is only valid for N/A');
    evidence(row.evidence,row.id,row.status!=='unassessed');rows[row.id]=row;
  }
  require(sameKeys(Object.keys(rows),Object.keys(catalog)),'Assessment must include every criterion exactly once');require(data.criteria.some(r=>r.status!=='not_applicable'),'All criteria cannot be N/A');
  require(Array.isArray(data.critical_blockers),'critical_blockers must be an array');const seen=new Set();
  for(const b of data.critical_blockers){object(b,'critical blocker',['id','criterion_id','description','status','evidence'],['resolution']);id(b.id,'blocker.id');require(!seen.has(b.id),'Duplicate blocker');seen.add(b.id);require(Object.hasOwn(catalog,b.criterion_id),'Unknown blocker criterion');text(b.description,'blocker.description');require(['open','resolved'].includes(b.status),'Invalid blocker status');evidence(b.evidence,'blocker',true,false);if(b.status==='resolved'||b.resolution!==undefined)text(b.resolution,'blocker.resolution');}
  return rows;
}
/* Python's round uses ties-to-even; bundled integer profile weights can produce exact .005 ties. */
const round = v => {const scaled=v*100,lower=Math.floor(scaled);return (scaled-lower===0.5?(lower%2===0?lower:lower+1):Math.round(scaled))/100;};
function metrics(ids,rows,weights){
  const sum=f=>ids.reduce((s,cid)=>s+f(cid),0);
  const nominal=sum(c=>weights[c]), excluded=sum(c=>rows[c].status==='not_applicable'?weights[c]:0), applicable=sum(c=>rows[c].status!=='not_applicable'?weights[c]:0), assessed=sum(c=>rows[c].status==='assessed'?weights[c]:0), earned=sum(c=>rows[c].status==='assessed'?weights[c]*rows[c].rating/4:0), complete=ids.every(c=>rows[c].status!=='unassessed');
  return {nominal_weight:nominal,applicable_weight:applicable,assessed_weight:assessed,excluded_weight:excluded,earned_subtotal:earned,score_out_of_100:complete&&applicable>0?round(100*earned/applicable):null,assessment_coverage_percent:applicable>0?round(100*assessed/applicable):null,status:complete?'complete':'provisional',missing_assessment_bounds:{lower:applicable>0?round(100*earned/applicable):null,upper:applicable>0?round(100*(earned+applicable-assessed)/applicable):null}};
}
export function scoreAssessment(data,rubric,policies,mode=null){
  mode=mode??data?.strictness??'standard';
  require(['standard','aggressive'].includes(mode),'Strictness must be standard or aggressive');
  const catalog=validateRubric(rubric), hash=fingerprint(rubric), rows=validateAssessment(data,rubric,catalog,hash);
  require(policies?.version===1&&policies.policies?.[mode],'Scoring policies version 1 required');const policy=policies.policies[mode],policyHash=fingerprint({version:policies.version,policy});
  if(data.scoring_policy_sha256!==undefined)require(data.scoring_policy_sha256===policyHash,'Assessment scoring policy fingerprint does not match');
  if(data.scoring_policy_id!==undefined)require(data.scoring_policy_id===policy.id,'Assessment scoring policy ID does not match');
  const weights=rubric.profiles[data.profile].weights, totals=metrics(Object.keys(catalog),rows,weights);require(totals.applicable_weight>0,'Assessment needs positive applicable weight');
  const active=clone(data.critical_blockers.filter(b=>b.status==='open')), deficits=[],low=[];
  for(const [cid,c] of Object.entries(catalog)){const row=rows[cid];if(c.core&&row.status==='assessed'){const finding={criterion_id:cid,rating:row.rating,confidence:row.confidence,evidence:clone(row.evidence),rationale:row.rationale};if(row.rating<rubric.core_threshold)deficits.push(finding);if(row.confidence==='low')low.push(finding);}}
  const priorities=[];
  for(const b of active)priorities.push({kind:'critical_blocker',criterion_id:b.criterion_id,blocker_id:b.id,reason:b.description,action:`Resolve and document the blocker: ${b.description}`,evidence:clone(b.evidence)});
  for(const [cid,row] of Object.entries(rows))if(row.status==='unassessed')priorities.push({kind:'missing_assessment',criterion_id:cid,reason:'Unassessed; quality is unknown, not an established failure.',action:row.action||'Inspect the relevant manuscript and source evidence, then record a rating, confidence, and evidence locations.',evidence:clone(row.evidence)});
  for(const [kind,findings] of [['core_deficit',deficits],['low_confidence_core',low]])for(const f of findings){const row=rows[f.criterion_id];priorities.push({kind,criterion_id:f.criterion_id,rating:row.rating,reason:row.rationale,action:row.action||(kind==='core_deficit'?'Address the recorded core deficit and reassess against its rubric anchors.':'Inspect additional source evidence to resolve low confidence in this core assessment.'),evidence:clone(row.evidence)});}
  for(const [cid,row] of Object.entries(rows).sort((a,b)=>(a[1].rating??5)-(b[1].rating??5)||a[0].localeCompare(b[0])))if(row.status==='assessed'&&row.rating<3&&!deficits.some(f=>f.criterion_id===cid))priorities.push({kind:'rated_weakness',criterion_id:cid,rating:row.rating,reason:row.rationale,action:row.action||'Address the observed weakness and reassess against the next rubric anchor.',evidence:clone(row.evidence)});
  const result=Object.fromEntries(Object.entries(clone(data)).filter(([k])=>!COMPUTED.has(k)));
  Object.assign(result,totals,{rubric_sha256:hash,profile_title:rubric.profiles[data.profile].title,assessed_weight_percent:totals.assessed_weight,readiness:active.length?'blocked':totals.status==='provisional'?'incomplete':deficits.length||low.length?'needs_revision_or_evidence':'reviewed',active_blockers:active,core_deficits:deficits,low_confidence_core_checks:low,domain_scores:rubric.domains.map(d=>({id:d.id,title:d.title,...metrics(Object.keys(catalog).filter(c=>catalog[c].domain===d.id),rows,weights)})),revision_priorities:priorities,limitations:[...LIMITATIONS],interpretation:LIMITATIONS[0],strictness:mode,scoring_policy_id:policy.id,scoring_policy_sha256:policyHash});
  const caps=[],failures=[];const cap=(rule,reason,evidence,identity)=>caps.push({rule,cap:policy.caps[rule],reason,evidence:clone(evidence),...identity});
  for(const [cid,c] of Object.entries(catalog)){
    const row=rows[cid];if(row.status!=='assessed')continue;
    if(c.core&&row.rating<policy.core_min_rating)failures.push({kind:'core_below_target',criterion_id:cid,reason:`Core rating ${row.rating}/4 is below ${policy.core_min_rating}/4.`,evidence:clone(row.evidence)});
    if(c.core&&(row.confidence==='low'||(policy.require_high_confidence_core&&row.confidence!=='high')))failures.push({kind:'core_confidence',criterion_id:cid,reason:`Core confidence is ${row.confidence}; additional evidence is required.`,evidence:clone(row.evidence)});
    if(mode!=='aggressive')continue;
    if(row.rating<=1){cap(c.core?'core_severe':'criterion_severe',`${c.core?'Core':'Applicable'} criterion rated ${row.rating}/4.`,row.evidence,{criterion_id:cid});failures.push({kind:'criterion_severe',criterion_id:cid,reason:'Applicable criterion is rated 0 or 1.',evidence:clone(row.evidence)});}
    else if(c.core&&row.rating===2)cap('core_below_target','Core criterion is partially adequate at 2/4; aggressive target is 3/4.',row.evidence,{criterion_id:cid});
    if(c.core&&row.confidence!=='high')cap(`core_confidence_${row.confidence}`,`Core assessment has ${row.confidence} confidence; confidence does not alter its raw rating.`,row.evidence,{criterion_id:cid});
  }
  for(const domain of result.domain_scores){const displayed=domain.score_out_of_100,value=displayed===null?null:100*domain.earned_subtotal/domain.applicable_weight;if(value===null||value>=policy.min_domain_score)continue;const records=Object.entries(catalog).filter(([,c])=>c.domain===domain.id).flatMap(([cid])=>rows[cid].evidence.map(e=>({criterion_id:cid,...e}))),reason=`Complete domain's unrounded score is below ${policy.min_domain_score}/100; displayed score is ${displayed}/100.`;failures.push({kind:'domain_below_target',domain_id:domain.id,reason,evidence:clone(records)});if(mode==='aggressive')cap(value<60?'domain_severe':'domain_below_target',reason,records,{domain_id:domain.id});}
  if(mode==='aggressive')for(const b of active)cap('open_blocker',b.description,b.evidence,{blocker_id:b.id,criterion_id:b.criterion_id});
  const scoreCap=Math.min(100,...caps.map(c=>c.cap));Object.assign(result,{score_caps:caps,strict_gate_failures:failures,score_cap_out_of_100:scoreCap,effective_score_out_of_100:totals.score_out_of_100===null?null:Math.min(totals.score_out_of_100,scoreCap)});
  if(!['blocked','incomplete'].includes(result.readiness)&&failures.length)result.readiness='needs_revision_or_evidence';
  return result;
}
