import Editor from '@monaco-editor/react'
import {useEffect,useState} from 'react'
import {BookOpen,BrainCircuit,Code2,Eye,GitBranch,Info,Lightbulb,Play,Send,ShieldCheck,Sparkles,TrendingUp} from 'lucide-react'
import {useParams} from 'react-router-dom'
import api from '../api'
import {Attempt,Concept,Problem,Student,SubmissionInsights} from '../types'
import AlgorithmLab,{modeFromConcept} from '../components/AlgorithmLab'

const tabs=[['understand',BookOpen],['visualise',Eye],['trace',GitBranch],['code',Code2]] as const
const loadingCopy=[
  'Reading your current learning context…',
  'Choosing the right scaffold level…',
  'Asking your local Qwen model…',
  'Shaping a hint without revealing the solution…',
]

export default function Learn({student}:{student:Student}){
  const {conceptId}=useParams()
  const [concept,setConcept]=useState<Concept>()
  const [problem,setProblem]=useState<Problem>()
  const [mode,setMode]=useState('understand')
  const [code,setCode]=useState('')
  const [attempt,setAttempt]=useState<Attempt>()
  const [insights,setInsights]=useState<SubmissionInsights>()
  const [hint,setHint]=useState('')
  const [hintError,setHintError]=useState('')
  const [hintLoading,setHintLoading]=useState(false)
  const [hintElapsed,setHintElapsed]=useState(0)
  const [busy,setBusy]=useState(false)

  useEffect(()=>{
    Promise.all([
      api.get(`/concepts/${conceptId}/lesson?student_id=${student.id}`),
      api.get(`/problems?concept_id=${conceptId}`),
    ]).then(([c,p])=>{
      setConcept(c.data)
      setProblem(p.data[0])
      setCode(p.data[0]?.starter_code||'')
    })
  },[conceptId,student.id])

  useEffect(()=>{
    if(!hintLoading){setHintElapsed(0);return}
    const timer=window.setInterval(()=>setHintElapsed(value=>value+1),1000)
    return()=>window.clearInterval(timer)
  },[hintLoading])

  async function submit(){
    if(!problem)return
    setBusy(true)
    setInsights(undefined)
    const {data}=await api.post('/submissions',{student_id:student.id,problem_id:problem.id,source_code:code,assisted:!!hint})
    setAttempt(data)
    const poll=window.setInterval(async()=>{
      const response=await api.get(`/submissions/${data.id}`)
      setAttempt(response.data)
      if(['COMPLETED','FAILED'].includes(response.data.status)){
        window.clearInterval(poll)
        setBusy(false)
        if(response.data.status==='COMPLETED'){
          try{const insightResponse=await api.get(`/submissions/${data.id}/insights`);setInsights(insightResponse.data)}catch{}
        }
      }
    },900)
  }

  async function getHint(){
    setHintLoading(true)
    setHintError('')
    setHint('')
    try{
      const {data}=await api.post('/tutor/hints',{
        student_id:student.id,
        concept_id:Number(conceptId),
        problem_id:problem?.id,
      },{timeout:130000})
      setHint(data.response)
    }catch(error:any){
      setHintError(error.response?.data?.detail||'The local tutor could not respond. Check that Ollama is running and try again.')
    }finally{
      setHintLoading(false)
    }
  }

  if(!concept)return <div className="loading">Loading workspace…</div>

  return <div className="learn">
    <div className="learn-head">
      <div><p className="kicker">CONCEPT {String(concept.position).padStart(2,'0')}</p><h1>{concept.title}</h1><p>{concept.summary}</p></div>
      <div className="estimate"><span>MASTERY ESTIMATE</span><b>Learning</b></div>
    </div>
    <div className="mode-tabs">
      {tabs.map(([name,Icon])=><button key={name} className={mode===name?'active':''} onClick={()=>setMode(name)}><Icon/>{name}</button>)}
    </div>
    <section className="workspace">
      {mode==='understand'&&<div className="lesson">
        <p className="kicker">CORE IDEA</p><h2>Build the mental model first.</h2><p className="lead">{concept.explanation}</p>
        <h3>Complexity</h3><div className="complexities">{Object.entries(concept.complexity||{}).map(([key,value])=><div key={key}><span>{key.replaceAll('_',' ')}</span><b>{value}</b></div>)}</div>
        <h3>Patterns to notice</h3><ul>{concept.examples?.map(item=><li key={item}>{item}</li>)}</ul>
      </div>}
      {mode==='visualise'&&<><div className="workspace-title"><div><p className="kicker">DETERMINISTIC VISUAL</p><h2>Watch state change, one operation at a time.</h2></div></div><AlgorithmLab initialMode={modeFromConcept(concept.visualizer)} embedded/></>}
      {mode==='trace'&&<div className="trace"><p className="kicker">GUIDED TRACE</p><h2>Predict before revealing.</h2><p>For <code>[7, 3, 8, 2, 5]</code>, which pair does bubble sort compare first—and does it swap?</p><details><summary>Reveal the next state</summary><div><code>[3, 7, 8, 2, 5]</code><p>7 &gt; 3, so the adjacent inversion is swapped.</p></div></details></div>}
      {mode==='code'&&problem&&<div className="code-lab">
        <div className="problem">
          <p className="kicker">{problem.difficulty.toUpperCase()} PRACTICE</p><h2>{problem.title}</h2><p>{problem.statement}</p>
          <h3>Visible example</h3><pre>Input{`\n`}{problem.visible_cases[0]?.input}{`\n`}Output{`\n`}{problem.visible_cases[0]?.expected}</pre>
          <div className="hint-control">
            <button className="hint-button" onClick={getHint} disabled={hintLoading}><Lightbulb/>{hintLoading?'Local tutor is thinking…':'Ask for a scaffolded hint'}<Info className="hint-info"/></button>
            <div className="hint-popover" role="tooltip">
              <div className="popover-title"><Sparkles/>How this hint is made</div>
              <p>PALS combines your mastery estimate, recent attempts, diagnosis, and current scaffold level before asking your local Qwen model.</p>
              <div><ShieldCheck/><span>It never judges correctness, changes mastery, or reveals hidden tests.</span></div>
            </div>
          </div>
          {hintLoading&&<div className="hint-loading" aria-live="polite">
            <div className="tutor-orbit"><Sparkles/><i/><i/><i/></div>
            <div className="hint-loading-copy"><b>Local tutor is composing your next nudge</b><span>{loadingCopy[Math.min(Math.floor(hintElapsed/4),loadingCopy.length-1)]}</span></div>
            <time>{hintElapsed}s</time>
            <div className="hint-progress"><i/></div>
            <small>Cold starts can take up to 90 seconds. Everything stays on this computer.</small>
          </div>}
          {hint&&<div className="hint"><div className="tutor-label"><Sparkles/><b>PALS local tutor</b><span>Qwen · scaffolded</span></div><p>{hint}</p></div>}
          {hintError&&<div className="hint-error"><b>Local tutor unavailable</b><span>{hintError}</span><button onClick={getHint}>Try again</button></div>}
        </div>
        <div className="editor">
          <Editor height="460px" language="java" theme="vs-dark" value={code} onChange={value=>setCode(value||'')} options={{fontSize:14,minimap:{enabled:false},padding:{top:18}}}/>
          <div className="editor-actions"><span>{attempt?`Status: ${attempt.status}`:'Judge0 evaluates visible + hidden cases'}</span><button className="secondary" onClick={submit} disabled={busy}><Play/>Run</button><button className="primary inline" onClick={submit} disabled={busy}><Send/>{busy?'Evaluating…':'Submit'}</button></div>
          {attempt&&['COMPLETED','FAILED'].includes(attempt.status)&&<div className={`result ${attempt.correct?'pass':'fail'}`}><b>{attempt.correct?'All cases passed':'Needs another look'}</b><span>{attempt.compiler_output||`${attempt.results.filter(result=>result.passed).length}/${attempt.results.length} cases passed · ${Math.round(attempt.runtime_ms||0)}ms`}</span></div>}
          {insights&&<div className="intelligence-card" aria-live="polite">
            <div className="intelligence-head"><span><BrainCircuit/>PALS intelligence</span><b>{Math.round(insights.mastery.probability*100)}% mastery</b></div>
            {insights.diagnosis?<><div className="diagnosis-title"><span className={`severity ${insights.diagnosis.severity}`}>{insights.diagnosis.severity}</span><h3>{insights.diagnosis.title}</h3><small>{Math.round(insights.diagnosis.confidence*100)}% confidence</small></div><p>{insights.diagnosis.explanation}</p><div className="next-action"><Lightbulb/><span><b>Next action</b>{insights.diagnosis.suggested_action}</span></div></>:<div className="diagnosis-clear"><ShieldCheck/><span><b>No misconception detected</b>This attempt strengthened the tracked skill.</span></div>}
            {insights.intervention&&<div className="intervention-row"><div><small>SELECTED SUPPORT · LEVEL {insights.intervention.scaffold_level}</small><b>{insights.intervention.kind}</b><span>{insights.intervention.rationale}</span></div>{insights.intervention.recommended_mode==='visualise'&&<button onClick={()=>setMode('visualise')}><Eye/>Open visual</button>}</div>}
            <div className="skill-row"><TrendingUp/><span>{insights.skills.length} skill signal{insights.skills.length===1?'':'s'} tracked persistently</span></div>
          </div>}
        </div>
      </div>}
    </section>
  </div>
}
