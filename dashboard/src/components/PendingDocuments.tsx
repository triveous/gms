import { Button } from '@/components/ui/button';
import { Sparkles } from 'lucide-react';
import defaultCoeImage from '@/assets/defalut-coe.png';
import { useChatContext } from '@/contexts/ChatContext';

export function PendingDocuments() {
    const { openChat, setPendingMessage } = useChatContext();

    const handleButtonClick = (message: string) => {
        openChat();
        setPendingMessage(message);
    };

    return (
        <div className="flex flex-col items-center justify-center py-12 gap-6 w-full bg-white">
            <img
                src={defaultCoeImage}
                alt="Pending Documents"
                className="w-auto h-auto max-w-[400px] mb-2"
            />

            <h3 className="text-[#020617] font-sans text-[20px] font-semibold leading-[120%] tracking-[-0.4px]">
                Pending Documents to upload
            </h3>

            <div className="flex flex-col gap-4 items-center">
                <Button
                    variant="outline"
                    className="flex items-center gap-2 px-6 py-2 h-[45px] text-[#475569] border-[#E2E8F0] shadow-none font-medium"
                    onClick={() => handleButtonClick("want to upload yealy plan document")}
                >
                    <Sparkles className="w-4 h-4 text-[black]" />
                    Submit Yearly Plan
                </Button>

                <Button
                    variant="outline"
                    className="flex items-center gap-2 px-6 py-2 h-[45px] text-[#475569] border-[#E2E8F0] shadow-none font-medium"
                    onClick={() => handleButtonClick("want to upload 1 quarter progress report document")}
                >
                    <Sparkles className="w-4 h-4 text-[black]" />
                    Submit 1 quarter progress Report
                </Button>
            </div>
        </div>
    );
}
