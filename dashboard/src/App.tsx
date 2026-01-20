import { FrappeProvider } from 'frappe-react-sdk'
import { AppProvider } from './contexts/AppContext'
import { AuthProvider } from './contexts/AuthContext'
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
import PartnersList from './pages/PartnersList'
import ContributorsList from './pages/ContributorsList'

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
		<AppProvider>
			<AuthProvider>
				<DesktopOnly />
				<BrowserRouter basename='dashboard'>
					<Routes>
						{/* Dashboard layout */}
						<Route element={<DashboardLayout />}>
							<Route index element={<Grants />} />
							<Route path=":grantId" element={<Grant />} />
							<Route path=":grantId/partners" element={<PartnersList scope="grant" />} />
							<Route path=":grantId/contributors" element={<ContributorsList scope="grant" />} />
							<Route path=":grantId/:projectId" element={<Project />} />
							<Route path=":grantId/:projectId/partners" element={<PartnersList scope="project" />} />
							<Route path=":grantId/:projectId/contributors" element={<ContributorsList scope="project" />} />
						</Route>
						<Route path="*" element={<NotFound />} />
					</Routes>
				</BrowserRouter>
			</AuthProvider>
		</AppProvider>
	</FrappeProvider>
}

export default App