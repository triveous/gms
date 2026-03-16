import { Sparkles } from 'lucide-react';
import DefaultImage from '../assets/defalut-coe.png';
import { useChatContext } from '@/contexts/ChatContext';
import { Button } from './ui/button';


export default function EmptyState() {
    const { openChat, setPendingMessage } = useChatContext();

    const handleUploadDPR = () => {
        setPendingMessage('I want to upload a DPR document');
        openChat();
    };

    return (
        <div className="flex flex-col items-center justify-center py-16 px-4 bg-white mt-6 rounded-lg">
            {/* Illustration */}
            <div className="mb-8">
                <img src={DefaultImage} alt="" className='w-[400px]'/>
            </div>

            {/* Text */}
            <h2 className="text-foreground font-semibold text-xl mb-8">
                Please setup your platform:
            </h2>

            {/* Upload Button */}
            <Button
                onClick={handleUploadDPR}
                variant="outline"
                className="flex items-center gap-2 px-6 py-2 h-[45px] text-[#475569] border-[#E2E8F0] shadow-none font-medium"
            >
                <Sparkles className="w-5 h-5" />
                Upload your DPR
            </Button>
        </div>
    );
}
