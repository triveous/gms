import { TrendingUp, TrendingDown } from 'lucide-react';

interface TrendingBadgeProps {
    change: string;
    isPositive: boolean;
}

export function TrendingBadge({ change, isPositive }: TrendingBadgeProps) {
    if (change === 'No Change') {
        return (
            <span className="flex items-center gap-[10px] px-[8px] py-[2px] rounded-[10px] bg-[#F1F5F9]">
               <span className="text-[#020617] font-mono text-sm font-normal leading-[150%]">-- No Change</span>
            </span>
        );
    }

    return (
        <span
            className={`flex items-center gap-[10px] px-[8px] py-[2px]  rounded-[10px] ${
                isPositive ? 'bg-[#B9FBD2]' : 'bg-[#FFD9D9]'
            }`}
        >
            {isPositive ? (
                <TrendingUp className="h-4 text-[#19D163]" />
            ) : (
                <TrendingDown className="h-4 text-[#FF4F79]" />
            )}
            <span className="text-[#020617] font-mono text-sm font-normal leading-[150%]">{change}</span>
        </span>
    );
}
