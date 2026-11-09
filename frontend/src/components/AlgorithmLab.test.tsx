import {fireEvent,render,screen} from '@testing-library/react'
import {describe,expect,it} from 'vitest'
import AlgorithmLab from './AlgorithmLab'

describe('AlgorithmLab',()=>{
  it('switches between all imported visual modules',()=>{
    render(<AlgorithmLab/>)
    expect(screen.getAllByText('Bubble Sort').length).toBeGreaterThan(0)
    fireEvent.click(screen.getByRole('button',{name:/Quick Sort/i}))
    expect(screen.getByRole('heading',{name:'Quick Sort',level:2})).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button',{name:/Heap/i}))
    expect(screen.getByRole('img',{name:'Max heap'})).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button',{name:/Graph/i}))
    expect(screen.getByRole('button',{name:'Run BFS'})).toBeInTheDocument()
  })
})
