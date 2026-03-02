import { Card } from '@/components/ui/card';
import { formatDate, calculateActiveSince } from '@/utils/formatters';

interface SimpleProjectCardProps {
    title: string;
    projectLead: string;
    startDate: string;
    lastUpdated: string;
}

export function SimpleProjectCard({
    title,
    projectLead,
    startDate,
    lastUpdated,
}: SimpleProjectCardProps) {
    return (
        <Card className="p-6 bg-card border border-border rounded-[4px] flex flex-col gap-4 shadow-none">
            <div className="flex flex-col gap-6">
                <h3 className="text-[#020617] font-sans text-[20px] font-semibold leading-[120%] tracking-[-0.4px]">
                    {title}
                </h3>
                <div className="flex flex-wrap items-center gap-4 text-[#334155] font-sans text-base font-normal leading-[150%]">
                    <span>Project Lead: {projectLead}</span>
                    <span className="bg-[#E2E8F0] w-[1px] h-[24px]"></span>
                    <span>Active Since: {calculateActiveSince(startDate)}</span>
                    <span className="bg-[#E2E8F0] w-[1px] h-[24px]"></span>
                    <span>Last Updated: {formatDate(lastUpdated)}</span>
                </div>
            </div>
        </Card>
    );
}
