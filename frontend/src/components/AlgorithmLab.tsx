import {useCallback,useEffect,useMemo,useRef,useState} from 'react'
import {ArrowRight,ChevronLeft,ChevronRight,Clock,Layers,Minus,Pause,Play,Plus,RotateCcw,Shuffle} from 'lucide-react'

export type AlgorithmMode='bubble'|'quick'|'merge'|'stack'|'queue'|'linkedlist'|'tree'|'heap'|'graph'
type Complexity={name:string;description:string;time:{best:string;average:string;worst:string};space:string;code:string}
type SortState='default'|'compare'|'active'|'sorted'|'pivot'
type SortNode={value:number;state:SortState}
type SortStep={nodes:SortNode[];line:number;message:string;stack:string[]}

export const algorithmModes:{id:AlgorithmMode;label:string;group:string}[]=[
  {id:'bubble',label:'Bubble Sort',group:'Sorting'},
  {id:'quick',label:'Quick Sort',group:'Sorting'},
  {id:'merge',label:'Merge Sort',group:'Sorting'},
  {id:'stack',label:'Stack',group:'Linear'},
  {id:'queue',label:'Queue',group:'Linear'},
  {id:'linkedlist',label:'Linked List',group:'Linear'},
  {id:'tree',label:'Binary Tree',group:'Non-linear'},
  {id:'heap',label:'Heap',group:'Non-linear'},
  {id:'graph',label:'Graph',group:'Non-linear'},
]

const info:Record<AlgorithmMode,Complexity>={
  bubble:{name:'Bubble Sort',description:'Repeatedly compare adjacent values and swap every inversion.',time:{best:'O(n)',average:'O(n²)',worst:'O(n²)'},space:'O(1)',code:`function bubbleSort(arr) {         // 1\n  for (let i = 0; i < n - 1; i++) { // 2\n    for (let j = 0; j < n-i-1; j++) // 3\n      if (arr[j] > arr[j + 1])      // 4\n        swap(arr[j], arr[j + 1]);   // 5\n  }                                  // 6\n  return arr;                        // 7\n}`},
  quick:{name:'Quick Sort',description:'Partition around a pivot, then recursively sort both sides.',time:{best:'O(n log n)',average:'O(n log n)',worst:'O(n²)'},space:'O(log n)',code:`function quickSort(arr, low, high) { // 1\n  const pivot = arr[high];             // 2\n  for (let j = low; j < high; j++)     // 3\n    if (arr[j] < pivot) swap(i++, j);  // 4\n  swap(arr[i + 1], arr[high]);         // 5\n  quickSort(arr, low, pi - 1);         // 6\n  quickSort(arr, pi + 1, high);        // 7\n}`},
  merge:{name:'Merge Sort',description:'Split into smaller ranges, then merge them in sorted order.',time:{best:'O(n log n)',average:'O(n log n)',worst:'O(n log n)'},space:'O(n)',code:`function mergeSort(arr, l, r) {      // 1\n  const mid = Math.floor((l + r) / 2); // 2\n  mergeSort(arr, l, mid);              // 3\n  mergeSort(arr, mid + 1, r);          // 4\n  merge(arr, l, mid, r);               // 5\n  return arr;                           // 6\n}`},
  stack:{name:'Stack',description:'Last in, first out: push and pop operate at the top.',time:{best:'O(1)',average:'O(1)',worst:'O(1)'},space:'O(n)',code:`class Stack {\n  push(value) { this.items.push(value); }\n  pop() { return this.items.pop(); }\n  peek() { return this.items.at(-1); }\n  isEmpty() { return this.items.length === 0; }\n}`},
  queue:{name:'Queue',description:'First in, first out: enqueue at the rear and dequeue at the front.',time:{best:'O(1)',average:'O(1)',worst:'O(1)'},space:'O(n)',code:`class Queue {\n  enqueue(value) { this.items.push(value); }\n  dequeue() { return this.items.shift(); }\n  front() { return this.items[0]; }\n  isEmpty() { return this.items.length === 0; }\n}`},
  linkedlist:{name:'Linked List',description:'Nodes store values and explicit links to the next node.',time:{best:'O(1)',average:'O(n)',worst:'O(n)'},space:'O(n)',code:`class Node {\n  constructor(value) {\n    this.value = value;\n    this.next = null;\n  }\n}\nfunction insertAtHead(value) {\n  const node = new Node(value);\n  node.next = head;\n  head = node;\n}`},
  tree:{name:'Binary Search Tree',description:'Every left descendant is smaller; every right descendant is larger.',time:{best:'O(log n)',average:'O(log n)',worst:'O(n)'},space:'O(n)',code:`function insert(root, value) {\n  if (!root) return new Node(value);\n  if (value < root.value)\n    root.left = insert(root.left, value);\n  else\n    root.right = insert(root.right, value);\n  return root;\n}`},
  heap:{name:'Binary Heap',description:'A complete tree that keeps its largest or smallest value at the root.',time:{best:'O(1)',average:'O(log n)',worst:'O(log n)'},space:'O(n)',code:`function heapifyUp(heap, index) {\n  while (index > 0) {\n    const parent = Math.floor((index - 1) / 2);\n    if (heap[index] <= heap[parent]) break;\n    swap(heap, index, parent);\n    index = parent;\n  }\n}`},
  graph:{name:'Graph Traversal',description:'Explore connected vertices breadth-first with a queue or depth-first recursively.',time:{best:'O(V+E)',average:'O(V+E)',worst:'O(V+E)'},space:'O(V)',code:`function bfs(graph, start) {\n  const queue = [start];\n  const visited = new Set();\n  while (queue.length) {\n    const node = queue.shift();\n    if (visited.has(node)) continue;\n    visited.add(node);\n    queue.push(...graph[node]);\n  }\n}`},
}

function clone(values:number[],states:Record<number,SortState>={}):SortNode[]{return values.map((value,index)=>({value,state:states[index]||'default'}))}

function bubbleSteps(input:number[]):SortStep[]{
  const values=[...input],steps:SortStep[]=[]
  const add=(line:number,message:string,states:Record<number,SortState>={},stack:string[]=['bubbleSort(arr)'])=>steps.push({nodes:clone(values,states),line,message,stack})
  add(1,'Start bubble sort.')
  for(let end=values.length-1;end>0;end--){
    for(let i=0;i<end;i++){
      add(3,`Compare ${values[i]} with ${values[i+1]}.`,{[i]:'compare',[i+1]:'compare'},['bubbleSort(arr)',`pass ${values.length-end}`,`compare j=${i}`])
      if(values[i]>values[i+1]){[values[i],values[i+1]]=[values[i+1],values[i]];add(5,'Swap the inverted pair.',{[i]:'active',[i+1]:'active'})}
    }
    add(6,`${values[end]} is now fixed.`,{[end]:'sorted'})
  }
  steps.push({nodes:clone(values,Object.fromEntries(values.map((_,i)=>[i,'sorted']))),line:7,message:'Sorting complete.',stack:[]})
  return steps
}

function quickSteps(input:number[],pivotChoice:string):SortStep[]{
  const values=[...input],steps:SortStep[]=[]
  const add=(line:number,message:string,states:Record<number,SortState>={},stack:string[]=[])=>steps.push({nodes:clone(values,states),line,message,stack})
  function sort(low:number,high:number,depth:number){
    if(low>high)return
    const frame=`quickSort(${low}, ${high})`
    if(low===high){add(7,`${values[low]} is a one-value partition.`,{[low]:'sorted'},[frame]);return}
    let pivotIndex=pivotChoice==='first'?low:pivotChoice==='middle'?Math.floor((low+high)/2):pivotChoice==='random'?low+Math.floor(Math.random()*(high-low+1)):high
    ;[values[pivotIndex],values[high]]=[values[high],values[pivotIndex]]
    const pivot=values[high];add(2,`Choose ${pivot} as the ${pivotChoice} pivot.`,{[high]:'pivot'},[...Array(depth).fill('quickSort(…)'),frame])
    let boundary=low
    for(let scan=low;scan<high;scan++){
      add(3,`Compare ${values[scan]} with pivot ${pivot}.`,{[scan]:'compare',[high]:'pivot'},[frame,`partition(${low}, ${high})`])
      if(values[scan]<pivot){[values[scan],values[boundary]]=[values[boundary],values[scan]];add(4,`Move ${values[boundary]} into the lower partition.`,{[boundary]:'active',[high]:'pivot'},[frame]);boundary++}
    }
    ;[values[boundary],values[high]]=[values[high],values[boundary]];add(5,`Place pivot ${pivot} at index ${boundary}.`,{[boundary]:'sorted'},[frame])
    sort(low,boundary-1,depth+1);sort(boundary+1,high,depth+1)
  }
  add(1,'Start quick sort.',{},[`quickSort(0, ${values.length-1})`]);sort(0,values.length-1,0)
  steps.push({nodes:clone(values,Object.fromEntries(values.map((_,i)=>[i,'sorted']))),line:7,message:'Sorting complete.',stack:[]})
  return steps
}

function mergeSteps(input:number[]):SortStep[]{
  const values=[...input],steps:SortStep[]=[]
  const add=(line:number,message:string,states:Record<number,SortState>={},stack:string[]=[])=>steps.push({nodes:clone(values,states),line,message,stack})
  function sort(left:number,right:number,depth:number){
    if(left>=right)return
    const mid=Math.floor((left+right)/2),frame=`mergeSort(${left}, ${right})`
    add(2,`Split [${left}..${right}] at ${mid}.`,{},[...Array(depth).fill('mergeSort(…)'),frame]);sort(left,mid,depth+1);sort(mid+1,right,depth+1)
    const a=values.slice(left,mid+1),b=values.slice(mid+1,right+1);let i=0,j=0,k=left
    while(i<a.length&&j<b.length){add(5,`Compare ${a[i]} and ${b[j]}.`,{[k]:'compare'},[frame,`merge(${left}, ${mid}, ${right})`]);values[k++]=a[i]<=b[j]?a[i++]:b[j++]}
    while(i<a.length)values[k++]=a[i++];while(j<b.length)values[k++]=b[j++]
    const states:Record<number,SortState>={};for(let x=left;x<=right;x++)states[x]='active'
    add(6,`Merged range [${left}..${right}].`,states,[frame])
  }
  add(1,'Start merge sort.',{},[`mergeSort(0, ${values.length-1})`]);sort(0,values.length-1,0)
  steps.push({nodes:clone(values,Object.fromEntries(values.map((_,i)=>[i,'sorted']))),line:6,message:'Sorting complete.',stack:[]})
  return steps
}

function SortVisualizer({mode,onStep}:{mode:'bubble'|'quick'|'merge';onStep:(step:SortStep)=>void}){
  const [caseType,setCaseType]=useState('random'),[pivot,setPivot]=useState('last'),[speed,setSpeed]=useState(450)
  const [values,setValues]=useState<number[]>([]),[steps,setSteps]=useState<SortStep[]>([]),[at,setAt]=useState(0),[playing,setPlaying]=useState(false)
  const reset=useCallback((kind=caseType)=>{const next=kind==='best'?[12,20,28,36,44,52,60,68,76,84]:kind==='worst'?[84,76,68,60,52,44,36,28,20,12]:Array.from({length:10},()=>Math.floor(Math.random()*75)+12);setValues(next);setSteps([]);setAt(0);setPlaying(false);onStep({nodes:clone(next),line:0,message:'Choose Play or step forward to begin.',stack:[]})},[caseType,onStep])
  useEffect(()=>reset(caseType),[mode,caseType,reset])
  useEffect(()=>{if(!playing||!steps.length)return;const timer=window.setInterval(()=>setAt(index=>{if(index>=steps.length-1){setPlaying(false);return index}return index+1}),speed);return()=>window.clearInterval(timer)},[playing,speed,steps.length])
  useEffect(()=>{if(steps[at])onStep(steps[at])},[at,steps,onStep])
  function ensure(){if(steps.length)return steps;const generated=mode==='bubble'?bubbleSteps(values):mode==='quick'?quickSteps(values,pivot):mergeSteps(values);setSteps(generated);return generated}
  const current=steps[at]?.nodes||clone(values),comparisons=steps.slice(0,at+1).filter(step=>step.message.startsWith('Compare')).length,swaps=steps.slice(0,at+1).filter(step=>/Swap|Move|Place/.test(step.message)).length
  return <div className="sort-module">
    <div className="lab-toolbar split"><div className="segmented" aria-label="Input order">{['random','best','worst'].map(kind=><button key={kind} className={caseType===kind?'active':''} onClick={()=>setCaseType(kind)}>{kind}</button>)}</div>{mode==='quick'&&<label>Pivot<select value={pivot} onChange={event=>{setPivot(event.target.value);setSteps([]);setAt(0)}}><option value="last">Last</option><option value="first">First</option><option value="middle">Middle</option><option value="random">Random</option></select></label>}</div>
    <div className="sort-stage" aria-label={`${info[mode].name} visualization`}>{current.map((node,index)=><div className={`sort-bar ${node.state}`} key={index} style={{height:`${45+node.value*2.15}px`}}><span>{node.value}</span></div>)}</div>
    <div className="step-message"><b>Step {steps.length?at+1:0}{steps.length?` / ${steps.length}`:''}</b><span>{steps[at]?.message||'Choose Play or step forward to begin.'}</span></div>
    <div className="lab-controls"><button aria-label="New array" onClick={()=>reset('random')}><Shuffle/></button><button aria-label="Previous" onClick={()=>setAt(index=>Math.max(0,index-1))} disabled={!steps.length}><ChevronLeft/></button><button className="lab-play" onClick={()=>{const generated=ensure();if(generated.length)setPlaying(value=>!value)}}>{playing?<Pause/>:<Play/>}<span>{playing?'Pause':'Play'}</span></button><button aria-label="Next" onClick={()=>{const generated=ensure();if(generated.length)setAt(index=>Math.min(generated.length-1,index+1))}}><ChevronRight/></button><button aria-label="Reset" onClick={()=>reset()}><RotateCcw/></button><label className="speed">Speed<input type="range" min="120" max="900" step="30" value={1020-speed} onChange={event=>setSpeed(1020-Number(event.target.value))}/></label></div>
    <div className="metrics"><span><small>Comparisons</small><b>{comparisons}</b></span><span><small>Moves</small><b>{swaps}</b></span><span><small>Input</small><b>{caseType}</b></span></div>
  </div>
}

function LinearVisualizer({type}:{type:'stack'|'queue'}){
  const [values,setValues]=useState([42,17,83,56]),[input,setInput]=useState(''),[active,setActive]=useState<number|null>(null)
  function add(){const value=input?Number(input):Math.floor(Math.random()*90)+10;if(!Number.isFinite(value))return;setValues(items=>[...items,value]);setActive(values.length);setInput('');window.setTimeout(()=>setActive(null),350)}
  function remove(){if(!values.length)return;const index=type==='stack'?values.length-1:0;setActive(index);window.setTimeout(()=>{setValues(items=>type==='stack'?items.slice(0,-1):items.slice(1));setActive(null)},250)}
  return <div className="structure-module"><div className={`linear-stage ${type}`}>{type==='queue'&&<span>FRONT</span>}<div>{values.map((value,index)=><b className={active===index?'active':''} key={`${value}-${index}`}>{value}</b>)}{!values.length&&<em>Empty {type}</em>}</div>{type==='queue'&&<span>REAR</span>}</div><div className="lab-toolbar"><input aria-label="Value" type="number" placeholder="Value" value={input} onChange={event=>setInput(event.target.value)}/><button className="solid" onClick={add}><Plus/>{type==='stack'?'Push':'Enqueue'}</button><button onClick={remove}><Minus/>{type==='stack'?'Pop':'Dequeue'}</button><button aria-label="Reset" onClick={()=>setValues([42,17,83,56])}><RotateCcw/></button></div><div className="concept-note"><b>{type==='stack'?'LIFO':'FIFO'}</b><span>{type==='stack'?'The newest value leaves first from the top.':'The oldest value leaves first from the front.'}</span></div></div>
}

function LinkedListVisualizer(){
  const [values,setValues]=useState([10,20,30,40]),[input,setInput]=useState(''),[position,setPosition]=useState(''),[active,setActive]=useState<number|null>(null)
  const value=()=>input?Number(input):Math.floor(Math.random()*90)+10
  function insert(where:'head'|'tail'|'position'){const next=value(),index=where==='head'?0:where==='tail'?values.length:Number(position);if(!Number.isFinite(next)||!Number.isInteger(index)||index<0||index>values.length)return;setValues(items=>{const result=[...items];result.splice(index,0,next);return result});setActive(index);setInput('');setPosition('');window.setTimeout(()=>setActive(null),400)}
  function remove(where:'head'|'tail'){if(!values.length)return;const index=where==='head'?0:values.length-1;setActive(index);window.setTimeout(()=>{setValues(items=>where==='head'?items.slice(1):items.slice(0,-1));setActive(null)},250)}
  return <div className="structure-module"><div className="list-stage"><span>HEAD</span>{values.map((item,index)=><div className={active===index?'active':''} key={`${item}-${index}`}><b>{item}</b><i><ArrowRight/></i></div>)}<span>NULL</span>{!values.length&&<em>Empty list</em>}</div><div className="lab-toolbar wrap"><input type="number" placeholder="Value" value={input} onChange={event=>setInput(event.target.value)}/><input type="number" placeholder="Position" value={position} onChange={event=>setPosition(event.target.value)}/><button className="solid" onClick={()=>insert('head')}><Plus/>Head</button><button className="solid" onClick={()=>insert('tail')}><Plus/>Tail</button><button onClick={()=>insert('position')}><Plus/>At position</button><button onClick={()=>remove('head')}><Minus/>Head</button><button onClick={()=>remove('tail')}><Minus/>Tail</button><button aria-label="Reset" onClick={()=>setValues([10,20,30,40])}><RotateCcw/></button></div><div className="concept-note"><b>Length {values.length}</b><span>Insertion rewires links; it does not shift stored values.</span></div></div>
}

type TreeNode={value:number;left:TreeNode|null;right:TreeNode|null}
function buildTree(values:number[]):TreeNode|null{let root:TreeNode|null=null;for(const value of values){const insert=(node:TreeNode|null):TreeNode=>!node?{value,left:null,right:null}:value<node.value?{...node,left:insert(node.left)}:{...node,right:insert(node.right)};root=insert(root)}return root}
function treePositions(root:TreeNode|null){const result:{value:number;x:number;y:number;parent?:{x:number;y:number}}[]=[];function walk(node:TreeNode|null,x:number,y:number,gap:number,parent?:{x:number;y:number}){if(!node)return;result.push({value:node.value,x,y,parent});walk(node.left,x-gap,y+70,Math.max(24,gap*.55),{x,y});walk(node.right,x+gap,y+70,Math.max(24,gap*.55),{x,y})}walk(root,210,34,105);return result}
function TreeVisualizer(){
  const initial=[50,30,70,20,40,60,80], [values,setValues]=useState(initial),[input,setInput]=useState(''),[visited,setVisited]=useState<number[]>([]),[current,setCurrent]=useState<number|null>(null),[running,setRunning]=useState(false)
  const root=useMemo(()=>buildTree(values),[values]),positions=useMemo(()=>treePositions(root),[root])
  async function traverse(kind:'inorder'|'preorder'){if(running)return;const order:number[]=[];function collect(node:TreeNode|null){if(!node)return;if(kind==='preorder')order.push(node.value);collect(node.left);if(kind==='inorder')order.push(node.value);collect(node.right)}collect(root);setRunning(true);setVisited([]);for(const item of order){setCurrent(item);setVisited(done=>[...done,item]);await new Promise(resolve=>window.setTimeout(resolve,420))}setCurrent(null);setRunning(false)}
  return <div className="structure-module"><div className="tree-stage"><svg viewBox="0 0 420 270" role="img" aria-label="Binary search tree">{positions.map((node,index)=>node.parent&&<line key={`edge-${index}`} x1={node.parent.x} y1={node.parent.y} x2={node.x} y2={node.y}/>)}{positions.map((node,index)=><g key={`${node.value}-${index}`} className={current===node.value?'current':visited.includes(node.value)?'visited':''}><circle cx={node.x} cy={node.y} r="20"/><text x={node.x} y={node.y}>{node.value}</text></g>)}</svg></div><div className="lab-toolbar wrap"><input type="number" placeholder="Value" value={input} onChange={event=>setInput(event.target.value)}/><button className="solid" disabled={running} onClick={()=>{const value=input?Number(input):Math.floor(Math.random()*90)+10;if(Number.isFinite(value)){setValues(items=>[...items,value]);setInput('')}}}><Plus/>Insert</button><button disabled={running} onClick={()=>traverse('inorder')}><Play/>Inorder</button><button disabled={running} onClick={()=>traverse('preorder')}><Play/>Preorder</button><button aria-label="Reset" onClick={()=>{setValues(initial);setVisited([])}}><RotateCcw/></button></div>{visited.length>0&&<div className="traversal"><span>Traversal</span>{visited.map((value,index)=><b key={`${value}-${index}`}>{value}</b>)}</div>}</div>
}

function HeapVisualizer(){
  const initial=[90,80,70,50,60,40,30],[heap,setHeap]=useState(initial),[max,setMax]=useState(true),[input,setInput]=useState(''),[active,setActive]=useState<number[]>([])
  async function animate(next:number[],index:number,direction:'up'|'down'){let current=index;while(true){const candidates=direction==='up'&&current>0?[current,Math.floor((current-1)/2)]:direction==='down'?[current,2*current+1,2*current+2].filter(item=>item<next.length):[];if(candidates.length<2)break;setActive(candidates);await new Promise(resolve=>window.setTimeout(resolve,280));let target=candidates[0];for(const candidate of candidates.slice(1))if(max?next[candidate]>next[target]:next[candidate]<next[target])target=candidate;if(target===current)break;[next[current],next[target]]=[next[target],next[current]];setHeap([...next]);current=target}setActive([])}
  async function insert(){const value=input?Number(input):Math.floor(Math.random()*90)+10;if(!Number.isFinite(value))return;const next=[...heap,value];setHeap(next);setInput('');await animate(next,next.length-1,'up')}
  async function extract(){if(!heap.length)return;const next=[...heap];next[0]=next.at(-1)!;next.pop();setHeap(next);if(next.length)await animate(next,0,'down')}
  function rebuild(nextMax:boolean){const source=[...heap].sort((a,b)=>nextMax?b-a:a-b);setMax(nextMax);setHeap(source);setActive([])}
  const positions=heap.map((value,index)=>{const level=Math.floor(Math.log2(index+1)),start=2**level-1,at=index-start,count=2**level;return{value,index,x:420*(at+1)/(count+1),y:42+level*68,parent:index?Math.floor((index-1)/2):null}})
  return <div className="structure-module"><div className="heap-switch"><button className={max?'active':''} onClick={()=>rebuild(true)}>Max heap</button><button className={!max?'active':''} onClick={()=>rebuild(false)}>Min heap</button></div><div className="tree-stage"><svg viewBox="0 0 420 270" role="img" aria-label={max?'Max heap':'Min heap'}>{positions.map(node=>node.parent!==null&&<line key={`edge-${node.index}`} x1={positions[node.parent].x} y1={positions[node.parent].y} x2={node.x} y2={node.y}/>)}{positions.map(node=><g key={node.index} className={active.includes(node.index)?'current':''}><circle cx={node.x} cy={node.y} r="20"/><text x={node.x} y={node.y}>{node.value}</text></g>)}</svg></div><div className="heap-array">{heap.map((value,index)=><span className={active.includes(index)?'active':''} key={index}><small>{index}</small><b>{value}</b></span>)}</div><div className="lab-toolbar"><input type="number" placeholder="Value" value={input} onChange={event=>setInput(event.target.value)}/><button className="solid" onClick={insert}><Plus/>Insert</button><button onClick={extract}><Minus/>Extract root</button><button aria-label="Reset" onClick={()=>{setHeap(initial);setMax(true)}}><RotateCcw/></button></div></div>
}

const graphNodes=[{id:'A',x:210,y:35},{id:'B',x:105,y:125},{id:'C',x:315,y:125},{id:'D',x:50,y:230},{id:'E',x:155,y:230},{id:'F',x:265,y:230},{id:'G',x:370,y:230}],graphEdges=[['A','B'],['A','C'],['B','D'],['B','E'],['C','F'],['C','G'],['E','F']]
function GraphVisualizer(){
  const [visited,setVisited]=useState<string[]>([]),[current,setCurrent]=useState<string|null>(null),[running,setRunning]=useState(false)
  const neighbors=(id:string)=>graphEdges.filter(edge=>edge.includes(id)).map(edge=>edge[0]===id?edge[1]:edge[0])
  async function traverse(kind:'bfs'|'dfs'){if(running)return;const order:string[]=[];if(kind==='bfs'){const queue=['A'],seen=new Set<string>();while(queue.length){const node=queue.shift()!;if(seen.has(node))continue;seen.add(node);order.push(node);queue.push(...neighbors(node).filter(item=>!seen.has(item)))}}else{const seen=new Set<string>();const walk=(node:string)=>{if(seen.has(node))return;seen.add(node);order.push(node);neighbors(node).forEach(walk)};walk('A')}setRunning(true);setVisited([]);for(const node of order){setCurrent(node);setVisited(done=>[...done,node]);await new Promise(resolve=>window.setTimeout(resolve,480))}setCurrent(null);setRunning(false)}
  const byId=(id:string)=>graphNodes.find(node=>node.id===id)!
  return <div className="structure-module"><div className="tree-stage graph-stage"><svg viewBox="0 0 420 270" role="img" aria-label="Graph traversal">{graphEdges.map(([from,to])=><line className={visited.includes(from)&&visited.includes(to)?'visited':''} key={`${from}-${to}`} x1={byId(from).x} y1={byId(from).y} x2={byId(to).x} y2={byId(to).y}/>)}{graphNodes.map(node=><g key={node.id} className={current===node.id?'current':visited.includes(node.id)?'visited':''}><circle cx={node.x} cy={node.y} r="21"/><text x={node.x} y={node.y}>{node.id}</text></g>)}</svg></div><div className="lab-toolbar"><button className="solid" disabled={running} onClick={()=>traverse('bfs')}><Play/>Run BFS</button><button disabled={running} onClick={()=>traverse('dfs')}><Play/>Run DFS</button><button onClick={()=>{setVisited([]);setCurrent(null)}}><RotateCcw/>Reset</button></div>{visited.length>0&&<div className="traversal"><span>Traversal order</span>{visited.map(node=><b key={node}>{node}</b>)}</div>}<div className="graph-notes"><p><b>BFS</b>explores level by level using a queue.</p><p><b>DFS</b>explores deeply before backtracking.</p></div></div>
}

function CodePanel({code,line,stack}:{code:string;line:number;stack:string[]}){return <div className="code-panel"><div className="code-panel-head"><i/><i/><i/><span>algorithm.ts</span>{line>0&&<b>Line {line}</b>}</div><pre>{code.split('\n').map((row,index)=><span className={line===index+1?'active':''} key={index}><em>{index+1}</em><code>{row||' '}</code></span>)}</pre>{stack.length>0&&<div className="call-stack"><span>CALL STACK</span>{[...stack].reverse().map((frame,index)=><b key={`${frame}-${index}`}>{frame}</b>)}</div>}</div>}
function ComplexityCard({data}:{data:Complexity}){return <div className="complexity-card"><h3>{data.name}</h3><div className="complexity-title"><Clock/>Time complexity</div><div className="complexity-grid"><span><small>Best</small><b>{data.time.best}</b></span><span><small>Average</small><b>{data.time.average}</b></span><span><small>Worst</small><b>{data.time.worst}</b></span></div><div className="space-row"><span><Layers/>Space</span><b>{data.space}</b></div></div>}

export function modeFromConcept(kind?:string):AlgorithmMode{if(kind==='sort')return'bubble';if(kind==='linked-list')return'linkedlist';if(kind==='tree'||kind==='graph'||kind==='stack'||kind==='queue')return kind;return'bubble'}

export default function AlgorithmLab({initialMode='bubble',embedded=false}:{initialMode?:AlgorithmMode;embedded?:boolean}){
  const [mode,setMode]=useState<AlgorithmMode>(initialMode),[sortStep,setSortStep]=useState<SortStep>({nodes:[],line:0,message:'',stack:[]}),[menuOpen,setMenuOpen]=useState(false)
  const sorting=mode==='bubble'||mode==='quick'||mode==='merge',data=info[mode]
  useEffect(()=>setMode(initialMode),[initialMode])
  return <section className={`algorithm-lab ${embedded?'embedded':''}`}>
    <div className="algorithm-picker-head"><div><span>ALGORITHM LAB</span><b>{data.name}</b></div><button onClick={()=>setMenuOpen(value=>!value)}>{menuOpen?'Close modules':'Browse 9 modules'}</button></div>
    <div className={`algorithm-picker ${menuOpen?'open':''}`}>{algorithmModes.map(item=><button key={item.id} className={mode===item.id?'active':''} onClick={()=>{setMode(item.id);setMenuOpen(false)}}><small>{item.group}</small>{item.label}</button>)}</div>
    <div className="lab-intro"><div><h2>{data.name}</h2><p>{data.description}</p></div><span>Interactive · deterministic · step-by-step</span></div>
    <div className="algorithm-grid"><div className="visual-card">{sorting?<SortVisualizer mode={mode} onStep={setSortStep}/>:mode==='stack'||mode==='queue'?<LinearVisualizer type={mode}/>:mode==='linkedlist'?<LinkedListVisualizer/>:mode==='tree'?<TreeVisualizer/>:mode==='heap'?<HeapVisualizer/>:<GraphVisualizer/>}</div><div className="algorithm-side"><CodePanel code={data.code} line={sorting?sortStep.line:0} stack={sorting?sortStep.stack:[]}/><ComplexityCard data={data}/></div></div>
  </section>
}
