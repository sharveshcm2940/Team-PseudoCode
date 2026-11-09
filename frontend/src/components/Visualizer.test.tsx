import {render,screen,fireEvent} from '@testing-library/react'
import {describe,it,expect} from 'vitest'
import Visualizer from './Visualizer'
describe('Visualizer',()=>{it('moves deterministically through steps',()=>{render(<Visualizer/>);expect(screen.getByText(/Step 1 of/)).toBeInTheDocument();fireEvent.click(screen.getAllByRole('button')[3]);expect(screen.getByText(/Step 2 of/)).toBeInTheDocument()})})
