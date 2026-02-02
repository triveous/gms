import { Button } from '@/components/ui/button';
import { Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import TopBar from '@/components/TopBar';
import ErrorLogo from '../assets/404-logo.svg';

export default function NotFound() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen flex flex-col bg-[#F8FAFC] font-sans">
            <TopBar showGrantSwitcher />
            
            <div className="flex-1 flex flex-col items-center justify-center px-4 -mt-20">
                <div className="text-center max-w-2xl">
                    <div className="relative mb-8 select-none flex justify-center items-center h-[220px]">
                        <img src={ErrorLogo} alt="404" className="h-[241px] object-contain" />
                    </div>
                    <h1 
                        className="mb-3"
                        style={{
                            color: 'var(--general-foreground, #020617)',
                            textAlign: 'center',
                            fontFamily: 'var(--font-definitions-font-family-headings, Inter)',
                            fontSize: '20px',
                            fontStyle: 'normal',
                            fontWeight: 600,
                            lineHeight: '125%',
                            letterSpacing: '-0.4px'
                        }}
                    >
                        Page not found
                    </h1>
                    <p className="text-[#64748b] text-[18px] mb-10 font-medium">
                        The page you are looking for has missing.
                    </p>
                    <Button 
                        onClick={() => navigate('/')}
                        className="bg-[#0f172a] hover:bg-[#1e293b] text-white px-10 py-5 rounded-lg gap-3 text-[14px] font-semibold shadow-xl hover:shadow-2xl transition-all duration-300 active:scale-95 flex items-center mx-auto"
                    >
                        <Home className="w-5 h-5" />
                        Go to home
                    </Button>
                </div>
            </div>
        </div>
    );
}
