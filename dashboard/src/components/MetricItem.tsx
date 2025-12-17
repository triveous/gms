import { TrendingBadge } from './TrendingBadge';

interface MetricItemProps {
    label: string;
    value: number;
    change: string;
    isPositive: boolean;
}

export function MetricItem({ label, value, change, isPositive }: MetricItemProps) {
    return (
        <div className="flex flex-col w-[117px] h-[89px] px-[16px] py-[12px] gap-[12px]">
            <div className="text-neutral-500 font-inter text-base font-medium leading-6">{label}</div>
            <div className="flex items-center gap-4">
                <span className="text-[#020617] font-inter text-2xl font-semibold leading-[120%] ">
                    {value}
                </span>
                <TrendingBadge change={change} isPositive={isPositive} />
            </div>
        </div>
    );
}
