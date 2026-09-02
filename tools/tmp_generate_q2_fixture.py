from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

OUT = Path('tests/fixtures/v1.6-event-family-hybrid-qualification.synthetic.v1.json')
EFA='lin_tianji_event_family_attribution_v1-exp'
C2='lin_tianji_hierarchical_claim_authority_v1-exp'
HCC='lin_tianji_hybrid_claim_composer_v1-exp'
HOC='lin_tianji_hybrid_output_contract_v1-exp'


def digest(value):
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def sha(label):
    return digest({'label':label})


def child_id(domain,family): return f'child:yearly:{domain}:{family}'
def parent_id(domain): return f'claim:yearly:{domain}'


def child(domain,family,opened=False,systems=(),deps=(),maturity=(),qualification=(),ceiling=None,bazi=(),ziwei=(),modifiers=(),timing=(),verify=False):
    return {
        'child_claim_id':child_id(domain,family),'parent_claim_id':parent_id(domain),'primary_domain':domain,
        'event_family':family,'target_scope':'yearly','candidate_source':'phase3','child_opened':opened,
        'bazi_target_feature_ids':list(bazi),'ziwei_target_feature_ids':list(ziwei),
        'modifier_feature_ids':list(modifiers),'timing_trigger_feature_ids':list(timing),
        'direct_target_dependency_families':list(deps),'direct_target_systems':list(systems),
        'maturity_summary':list(maturity),'qualification_summary':list(qualification),
        'required_verification_caveat':verify,'family_specificity_ceiling':ceiling,
        'source_ranking_digest':'','source_structural_interpretation_digest':''}


def efa(case,children):
    ranking=sha(case+':ranking'); structural=sha(case+':structural'); rows=[]
    for row in children:
        row=copy.deepcopy(row); row['source_ranking_digest']=ranking; row['source_structural_interpretation_digest']=structural; rows.append(row)
    out={'profile_version':EFA,'target_scope':'yearly','base_ranking_digest':ranking,'structural_interpretation_digest':structural,'children':rows}
    out['event_family_attribution_digest']=digest(out); return out


def decision(row,decision,authorized=None,parent_decision='render',parent_specificity='event_family',reasons=()):
    return {'child_claim_id':row['child_claim_id'],'parent_claim_id':row['parent_claim_id'],'primary_domain':row['primary_domain'],
            'event_family':row['event_family'],'decision':decision,'parent_decision':parent_decision,
            'parent_authorized_specificity':parent_specificity,'family_specificity_ceiling':row['family_specificity_ceiling'],
            'authorized_specificity':authorized,'source_systems':list(row['direct_target_systems']),'reason_codes':list(reasons)}


def c2(case,efa_bundle,decisions):
    out={'profile_version':C2,'target_scope':'yearly','claim_evidence_digest':sha(case+':claim_evidence'),
         'claim_consumption_digest':sha(case+':claim_consumption'),'event_family_attribution_digest':efa_bundle['event_family_attribution_digest'],
         'decisions':decisions}
    out['hierarchical_claim_authority_digest']=digest(out); return out


def hchild(row,dec,relation,visibility):
    caveats=[] if dec['decision']=='abstain_child' else list(dec['reason_codes'])
    if dec['decision']!='abstain_child' and relation=='divergence' and 'explicit_divergence' not in caveats: caveats.append('explicit_divergence')
    return {'child_claim_id':row['child_claim_id'],'parent_claim_id':row['parent_claim_id'],'primary_domain':row['primary_domain'],
            'event_family':row['event_family'],'authority_decision':dec['decision'],'authorized_specificity':dec['authorized_specificity'],
            'source_systems':list(row['direct_target_systems']),'cross_system_relation':relation,
            'visibility':'audit_only' if dec['decision']=='abstain_child' else visibility,'required_caveats':caveats}


def hcc(case,efa_bundle,c2_bundle,children,groups=()):
    out={'profile_version':HCC,'target_scope':'yearly','hierarchical_claim_authority_digest':c2_bundle['hierarchical_claim_authority_digest'],
         'event_family_attribution_digest':efa_bundle['event_family_attribution_digest'],'source_interpretation_contract_digest':sha(case+':interpretation'),
         'source_claim_evidence_digest':c2_bundle['claim_evidence_digest'],'children':children,'composition_groups':list(groups)}
    out['hybrid_claim_composer_digest']=digest(out); return out


def unit(hcc_bundle,domain,composition,members):
    ids=[m['child_claim_id'] for m in members]
    identity={'target_scope':'yearly','primary_domain':domain,'composition_type':composition,'member_child_claim_ids':ids}
    caveats=[]; relations=[]
    for m in members:
        for x in m['required_caveats']:
            if x not in caveats: caveats.append(x)
        if m['cross_system_relation'] not in relations: relations.append(m['cross_system_relation'])
    specificity='event_family' if any(m['authorized_specificity']=='event_family' for m in members) else 'concrete_event'
    return {'render_unit_id':'render-unit:'+digest(identity),'member_child_claim_ids':ids,'primary_domain':domain,'target_scope':'yearly',
            'composition_type':composition,'cross_system_relations':relations,'visibility':members[0]['visibility'],
            'authorized_specificity':specificity,'required_caveats':caveats,'causality_allowed':False,
            'source_efa_digest':hcc_bundle['event_family_attribution_digest'],'source_c2_digest':hcc_bundle['hierarchical_claim_authority_digest'],
            'source_hcc_digest':hcc_bundle['hybrid_claim_composer_digest']}


def hoc(hcc_bundle,units):
    ordinary=[copy.deepcopy(x) for x in hcc_bundle['children'] if x['authority_decision'] in {'render','render_with_caveat'}]
    audit=[copy.deepcopy(x) for x in hcc_bundle['children'] if x['authority_decision']=='abstain_child']
    out={'profile_version':HOC,'target_scope':'yearly','source_hybrid_claim_composer_digest':hcc_bundle['hybrid_claim_composer_digest'],
         'render_units':units,'children':ordinary,'audit_only_children':audit}
    out['hybrid_output_contract_digest']=digest(out); return out


def expectation(row,opened,systems,deps,authorization,minspec,maxspec,caveat,relation,visibility,manifest):
    return {'child_claim_id':row['child_claim_id'],'expected_opened':opened,'expected_direct_target_systems':list(systems),
            'expected_direct_target_dependency_families':list(deps),'expected_authorization':authorization,
            'minimum_acceptable_specificity':minspec,'maximum_specificity':maxspec,'caveat_required':caveat,
            'expected_cross_system_relation':relation,'expected_visibility':visibility,'expected_in_render_manifest':manifest}


def case(case_id,efa_bundle,c2_bundle,hcc_bundle,hoc_bundle,expectations,groups=(),absence=()):
    receipt={'source_identity_digest':sha(case_id+':source'),'first_efa_digest':efa_bundle['event_family_attribution_digest'],
             'second_efa_digest':efa_bundle['event_family_attribution_digest'],'first_c2_digest':c2_bundle['hierarchical_claim_authority_digest'],
             'second_c2_digest':c2_bundle['hierarchical_claim_authority_digest'],'first_hcc_digest':hcc_bundle['hybrid_claim_composer_digest'],
             'second_hcc_digest':hcc_bundle['hybrid_claim_composer_digest'],'first_hoc_digest':hoc_bundle['hybrid_output_contract_digest'],
             'second_hoc_digest':hoc_bundle['hybrid_output_contract_digest']}
    out={'case_id':case_id,'efa_bundle':efa_bundle,'c2_bundle':c2_bundle,'hcc_bundle':hcc_bundle,'hoc_bundle':hoc_bundle,
         'child_expectations':expectations,'composition_expectations':list(groups),'absence_policy_cases':list(absence),
         'determinism_receipt':receipt,'cutoff_contamination':False}
    out['input_digest']=digest(out); return out


def mixed_primary():
    cid='Q2-A-mixed-primary'
    rows=[
      child('career','role_change',True,('bazi','ziwei'),('dep:b-role','dep:z-role'),('stable',),('qualified',),'concrete_event',('b-role',),('z-role',)),
      child('career','partnership_change',True,('ziwei',),('dep:z-partner',),('stable',),('qualified',),'event_family',ziwei=('z-partner',)),
      child('career','leadership_change',True,('bazi',),('dep:b-lead',),('stable',),('qualified',),'event_family',bazi=('b-lead',)),
      child('career','verification_needed',True,('bazi',),('dep:b-verify',),('stable',),('needs_verification',),'event_family',bazi=('b-verify',),verify=True),
      child('career','experimental_signal',True,('ziwei',),('dep:z-exp',),('experimental',),('qualified',),'event_family',ziwei=('z-exp',)),
      child('career','modifier_only',False,modifiers=('z-mod',)),child('career','timing_only',False,timing=('z-time',)),child('career','unqualified_signal')]
    eb=efa(cid,rows); rows=eb['children']
    ds=[decision(rows[0],'render','concrete_event',parent_specificity='concrete_event'),
        decision(rows[1],'render_with_caveat','event_family',reasons=('single_system_support',)),
        decision(rows[2],'render_with_caveat','event_family',reasons=('single_system_support',)),
        decision(rows[3],'render_with_caveat','event_family',reasons=('single_system_support','needs_verification')),
        decision(rows[4],'render_with_caveat','event_family',reasons=('single_system_support','experimental_only'))]
    ds += [decision(rows[i],'abstain_child',None,reasons=('no_direct_target_support',)) for i in (5,6,7)]
    cb=c2(cid,eb,ds); rel=['direct_convergence','single_system_qualified','single_system_qualified','single_system_qualified','single_system_qualified','no_direct_target_support','no_direct_target_support','no_direct_target_support']
    hc=[hchild(r,d,x,'primary') for r,d,x in zip(rows,ds,rel)]
    members=[rows[i]['child_claim_id'] for i in (1,2,3,4)]
    group={'composition_type':'parallel_sibling','primary_domain':'career','member_child_claim_ids':members}
    hb=hcc(cid,eb,cb,hc,(group,)); ob=hoc(hb,(unit(hb,'career','parallel_sibling_group',[hc[i] for i in (1,2,3,4)]),unit(hb,'career','direct_convergence_child',[hc[0]])))
    ex=[expectation(rows[0],True,('bazi','ziwei'),('dep:b-role','dep:z-role'),'render','concrete_event','concrete_event',False,'direct_convergence','primary',True),
        expectation(rows[1],True,('ziwei',),('dep:z-partner',),'render_with_caveat','event_family','event_family',True,'single_system_qualified','primary',True),
        expectation(rows[2],True,('bazi',),('dep:b-lead',),'render_with_caveat','event_family','event_family',True,'single_system_qualified','primary',True),
        expectation(rows[3],True,('bazi',),('dep:b-verify',),'render_with_caveat','event_family','event_family',True,'single_system_qualified','primary',True),
        expectation(rows[4],True,('ziwei',),('dep:z-exp',),'render_with_caveat','event_family','event_family',True,'single_system_qualified','primary',True)]
    ex += [expectation(rows[i],False,(),(),'abstain_child',None,None,False,None,'audit_only',False) for i in (5,6,7)]
    return case(cid,eb,cb,hb,ob,ex,({'composition_type':'parallel_sibling','member_child_claim_ids':members,'expected_manifest_presence':True},))


def layered_secondary():
    cid='Q2-B-layered-secondary-absence'; rows=[
      child('finance','income_change',True,('bazi',),('dep:b-income',),('stable',),('qualified',),'event_family',bazi=('b-income',)),
      child('finance','role_change',True,('bazi',),('dep:b-role',),('stable',),('qualified',),'event_family',bazi=('b-role',),modifiers=('z-mod',))]
    eb=efa(cid,rows); rows=eb['children']; ds=[decision(r,'render_with_caveat','event_family',reasons=('single_system_support',)) for r in rows]; cb=c2(cid,eb,ds)
    hc=[hchild(rows[0],ds[0],'single_system_qualified','secondary'),hchild(rows[1],ds[1],'layered_complement','secondary')]; hb=hcc(cid,eb,cb,hc)
    ob=hoc(hb,(unit(hb,'finance','single_child',[hc[0]]),unit(hb,'finance','layered_complement_child',[hc[1]])))
    ex=[expectation(rows[0],True,('bazi',),('dep:b-income',),'render_with_caveat','event_family','event_family',True,'single_system_qualified','secondary',True),
        expectation(rows[1],True,('bazi',),('dep:b-role',),'render_with_caveat','event_family','event_family',True,'layered_complement','secondary',True)]
    absence=({'child_claim_id':rows[0]['child_claim_id'],'materialized_system':'bazi','missing_system':'ziwei','expected_authorization':'render_with_caveat','expected_relation':'single_system_qualified'},)
    return case(cid,eb,cb,hb,ob,ex,absence=absence)


def capped():
    cid='Q2-C-parent-specificity-cap'; rows=[child('career','role_change',True,('bazi','ziwei'),('dep:b','dep:z'),('stable',),('qualified',),'concrete_event',('b',),('z',))]
    eb=efa(cid,rows); rows=eb['children']; ds=[decision(rows[0],'render_with_caveat','event_family',reasons=('specificity_downgraded',))]; cb=c2(cid,eb,ds)
    hc=[hchild(rows[0],ds[0],'direct_convergence','primary')]; hb=hcc(cid,eb,cb,hc); ob=hoc(hb,(unit(hb,'career','direct_convergence_child',hc),))
    ex=[expectation(rows[0],True,('bazi','ziwei'),('dep:b','dep:z'),'render_with_caveat','event_family','event_family',True,'direct_convergence','primary',True)]
    return case(cid,eb,cb,hb,ob,ex)


def divergence():
    cid='Q2-D-explicit-divergence'; rows=[child('career','role_change',True,('bazi',),('dep:b',),('stable',),('qualified',),'event_family',bazi=('b',)),child('career','leadership_change',True,('ziwei',),('dep:z',),('stable',),('qualified',),'event_family',ziwei=('z',))]
    eb=efa(cid,rows); rows=eb['children']; ds=[decision(r,'render_with_caveat','event_family',reasons=('single_system_support',)) for r in rows]; cb=c2(cid,eb,ds)
    hc=[hchild(r,d,'divergence','primary') for r,d in zip(rows,ds)]; hb=hcc(cid,eb,cb,hc); ob=hoc(hb,tuple(unit(hb,'career','divergence_child',[x]) for x in hc))
    ex=[expectation(r,True,tuple(r['direct_target_systems']),tuple(r['direct_target_dependency_families']),'render_with_caveat','event_family','event_family',True,'divergence','primary',True) for r in rows]
    return case(cid,eb,cb,hb,ob,ex)


def parent_abstain():
    cid='Q2-E-parent-abstain-audit'; rows=[child('career','context_only',False,modifiers=('z-context',))]
    eb=efa(cid,rows); rows=eb['children']; ds=[decision(rows[0],'abstain_child',None,parent_decision='abstain_claim',reasons=('parent_abstained',))]; cb=c2(cid,eb,ds)
    hc=[hchild(rows[0],ds[0],'no_direct_target_support','primary')]; hb=hcc(cid,eb,cb,hc); ob=hoc(hb,())
    ex=[expectation(rows[0],False,(),(),'abstain_child',None,None,False,None,'audit_only',False)]
    return case(cid,eb,cb,hb,ob,ex)


payload={'schema_version':'v1.6-event-family-hybrid-qualification-input.v1','classification':'synthetic_validation','cases':[mixed_primary(),layered_secondary(),capped(),divergence(),parent_abstain()]}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(OUT)
