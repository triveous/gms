import './App.css'
import { FrappeProvider } from 'frappe-react-sdk'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Grants from './pages/Grants'
import Grant from './pages/Grant'
import Project from './pages/Project'

function App() {
	return (
		<FrappeProvider>
			<Router>
				<Routes>
					<Route path="/" element={<Grants />} />
					<Route path="/grants" element={<Grants />} />
					<Route path="/grant/:id" element={<Grant />} />
					<Route path="/project/:id" element={<Project />} />
				</Routes>
			</Router>
		</FrappeProvider>
	)
}

export default App
