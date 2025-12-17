import './App.css'
import { FrappeProvider } from 'frappe-react-sdk'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Grants from './pages/Grants'
import Grant from './pages/Grant'
import Project from './pages/Project'
import { ChatProvider } from './contexts/ChatContext'
import ChatPanel from './components/ChatPanel'

function App() {
	return (
		<FrappeProvider url=''>
			<ChatProvider>
				<Router>
					<Routes>
						<Route path="/" element={<Grants />} />
						<Route path="/grant/:id" element={<Grant />} />
						<Route path="/project/:id" element={<Project />} />
					</Routes>
				</Router>
				<ChatPanel />
			</ChatProvider>
		</FrappeProvider>
	)
}

export default App
