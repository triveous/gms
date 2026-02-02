import { FrappeProvider } from 'frappe-react-sdk'
import { AppProvider } from './contexts/AppContext'
import { AuthProvider } from './contexts/AuthContext'
import { BrowserRouter, Outlet, Route, Routes, Navigate } from 'react-router-dom'
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
	return (
		<ProtectedRoute>
			<>
				<Outlet />
				<ChatPanel />
			</>
		</ProtectedRoute>
	)
}

function App() {
	const pathname = window.location.pathname;
	const isDashboardRoot = pathname.startsWith('/dashboard');

	return (
		<FrappeProvider>
			<AppProvider>
				<AuthProvider>
					<ChatProvider>
						<DesktopOnly />
						{isDashboardRoot ? (
							<BrowserRouter basename="/dashboard">
								<Routes>
									<Route element={<DashboardLayout />}>
										<Route index element={<Grants />} />
										<Route path=":grantId">
											<Route index element={<Grant />} />
											<Route path="partners" element={<PartnersList scope="grant" />} />
											<Route path="contributors" element={<ContributorsList scope="grant" />} />
											<Route path=":projectId">
												<Route index element={<Project />} />
												<Route path="partners" element={<PartnersList scope="project" />} />
												<Route path="contributors" element={<ContributorsList scope="project" />} />
											</Route>
										</Route>
									</Route>
									<Route path="*" element={<NotFound />} />
								</Routes>
							</BrowserRouter>
						) : (
							<BrowserRouter>
								<Routes>
									<Route path="/" element={<Navigate to="/dashboard" replace />} />
									<Route path="*" element={<NotFound />} />
								</Routes>
							</BrowserRouter>
						)}
					</ChatProvider>
				</AuthProvider>
			</AppProvider>
		</FrappeProvider>
	);
}

export default App