import './App.css'
import { FrappeProvider } from 'frappe-react-sdk'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Grants from './pages/Grants'
import Grant from './pages/Grant'
import Project from './pages/Project'
import Login from './pages/Login'
import { ChatProvider } from './contexts/ChatContext'
import { AuthProvider } from './contexts/AuthContext'
import ChatPanel from './components/ChatPanel'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
	return (
		<FrappeProvider>
			
				<ChatProvider>
					<Router>
						<AuthProvider>
						<Routes>
							<Route path="/login" element={<Login />} />
							<Route 
								path="/dashboard" 
								element={
									<ProtectedRoute>
										<Grants />
									</ProtectedRoute>
								} 
							/>
							<Route 
								path="/grant/:id" 
								element={
									<ProtectedRoute>
										<Grant />
									</ProtectedRoute>
								} 
							/>
							<Route 
								path="/project/:id" 
								element={
									<ProtectedRoute>
										<Project />
									</ProtectedRoute>
								} 
							/>
						</Routes>
						<ChatPanel />
						</AuthProvider>
					</Router>
				</ChatProvider>
		</FrappeProvider>
	)
}

export default App
