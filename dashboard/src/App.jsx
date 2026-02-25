import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import BenchmarkData from './views/BenchmarkData'
import TraceLogs from './views/TraceLogs'
import Experiments from './views/Experiments'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<BenchmarkData />} />
          <Route path="traces" element={<TraceLogs />} />
          <Route path="experiments" element={<Experiments />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
