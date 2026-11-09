import {useEffect,useState} from 'react'
import {ArrowRight,Check,Lock} from 'lucide-react'
import {Link} from 'react-router-dom'
import api from '../api'
import {Concept,Course} from '../types'
export default function Catalogue(){const [course,setCourse]=useState<Course>();const [concepts,setConcepts]=useState<Concept[]>([]);useEffect(()=>{api.get('/courses').then(async r=>{setCourse(r.data[0]);const c=await api.get(`/courses/${r.data[0].id}/concepts`);setConcepts(c.data)})},[]);return <div className="page"><header><div><p className="kicker">STRUCTURED PATH</p><h1>{course?.title||'Curriculum'}</h1><p>{course?.description}</p></div></header><div className="concept-grid">{concepts.map((c,i)=><Link to={`/learn/${c.id}`} className="concept-card" key={c.id}><div className="concept-number">{String(i+1).padStart(2,'0')}</div><span className="status-dot">{i===0?<Check/>:<Lock/>}</span><h2>{c.title}</h2><p>{c.summary}</p><div>{c.prerequisites.length?`After ${c.prerequisites.join(', ')}`:'Start here'}<ArrowRight/></div></Link>)}</div></div>}
