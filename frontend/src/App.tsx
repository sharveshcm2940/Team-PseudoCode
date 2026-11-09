import {useEffect,useState} from 'react'
import {Navigate,Route,Routes} from 'react-router-dom'
import api from './api'
import {Student} from './types'
import Shell from './components/Shell'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Catalogue from './pages/Catalogue'
import Learn from './pages/Learn'
import VisualLab from './pages/VisualLab'
import Intelligence from './pages/Intelligence'

export default function App(){
 const [student,setStudent]=useState<Student|null>(()=>{try{return JSON.parse(localStorage.getItem('pals_student')||'null')}catch{return null}})
 useEffect(()=>{if(student)localStorage.setItem('pals_student',JSON.stringify(student))},[student])
 if(!student)return <Onboarding onReady={setStudent}/>
 return <Routes><Route element={<Shell student={student} onLogout={()=>{localStorage.removeItem('pals_student');setStudent(null)}}/>}><Route index element={<Dashboard student={student}/>}/><Route path="courses" element={<Catalogue/>}/><Route path="visual-lab" element={<VisualLab/>}/><Route path="intelligence" element={<Intelligence student={student}/>}/><Route path="learn/:conceptId" element={<Learn student={student}/>}/></Route><Route path="*" element={<Navigate to="/"/>}/></Routes>
}
