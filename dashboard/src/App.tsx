import { FrappeProvider } from 'frappe-react-sdk'
import { BrowserRouter, Outlet, Route, Routes } from 'react-router-dom'
import './App.css'
import ChatPanel from './components/ChatPanel'
import DesktopOnly from './components/DesktopOnly'
import ProtectedRoute from './components/ProtectedRoute'
import { ChatProvider } from './contexts/ChatContext'
import Grant from './pages/Grant'
import Grants from './pages/Grants'
import NotFound from './pages/NotFound'
import Project from './pages/Project'

function DashboardLayout() {
	return <ProtectedRoute>
		<ChatProvider>
			<Outlet />
			<ChatPanel />
		</ChatProvider>
	</ProtectedRoute>

}

function App() {
	return <FrappeProvider>
		<DesktopOnly />
		<BrowserRouter>
			<Routes>
				{/* Dashboard layout */}
				<Route path="dashboard" element={<DashboardLayout />}>
					<Route index element={<Grants />} />
					<Route path="dashboard/:grantId" element={<Grant />} />
					<Route path=":dashboard/grantId/:projectId" element={<Project />} />
				</Route>
				<Route path="*" element={<NotFound />} />
			</Routes>
		</BrowserRouter>
	</FrappeProvider>
}

export default App