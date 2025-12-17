import { Button } from '@/components/ui/button';
import { ChevronRight } from 'lucide-react';
import { MetricItem } from './MetricItem';
import { useNavigate } from 'react-router-dom';

interface ProjectMetric {
    value: number;
    change: string;
    isPositive: boolean;
}

interface ProjectCardProps {
    title: string;
    projectLead: string;
    activeSince: string;
    lastUpdated: string;
    metrics: {
        tbl: ProjectMetric;
        mrl: ProjectMetric;
        crl: ProjectMetric;
        sirl: ProjectMetric;
    };
    budgetSpent: string;
    progress: string;
}

export function ProjectCard({
    title,
    projectLead,
    activeSince,
    lastUpdated,
    metrics,
    budgetSpent,
    progress,
}: ProjectCardProps) {

    const navigate = useNavigate();
    
    const handleProjectClick = (projectId: number) => {
        navigate(`/project/${projectId}`);
    };
    
    return (
        <div className="p-6 bg-card border border-border rounded-[4px] flex flex-col gap-4">
            {/* Project Header */}
            <div className="flex gap-4">
                <div className="flex flex-col gap-6 flex-1">
                    <h3 className="text-[#020617] font-sans text-[20px] font-semibold leading-[120%] tracking-[-0.4px]">
                        {title}
                    </h3>
                    <div className="flex items-center gap-4 text-[#334155] font-sans text-base font-normal leading-[150%]">
                        <span>Project Lead: {projectLead}</span>
                        <span className="bg-[#E2E8F0] w-[1px] h-[24px]"></span>
                        <span>Active Since: {activeSince}</span>
                        <span className="bg-[#E2E8F0] w-[1px] h-[24px]"></span>
                        <span>Last Updated: {lastUpdated}</span>
                    </div>
                </div>
                <Button variant="outline" className="w-[155.5px] h-[45px] px-6 gap-2" onClick={() => handleProjectClick(1)}>
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="14"
                        height="14"
                        viewBox="0 0 14 14"
                        fill="none"
                    >
                        <path
                            d="M4.75 8.66699C5.5324 8.66699 6.16699 9.30158 6.16699 10.084V12.084C6.16664 12.8661 5.53219 13.5 4.75 13.5H1.41699C0.634806 13.5 0.000351737 12.8661 0 12.084V10.084C0 9.30158 0.634589 8.66699 1.41699 8.66699H4.75ZM12.083 6C12.8654 6 13.5 6.63459 13.5 7.41699V12.083C13.5 12.8654 12.8654 13.5 12.083 13.5H8.75C7.96775 13.4998 7.33301 12.8653 7.33301 12.083V7.41699C7.33301 6.6347 7.96775 6.00018 8.75 6H12.083ZM1.5 12H4.66699V10.167H1.5V12ZM8.83301 12H12V7.5H8.83301V12ZM4.75 0C5.5324 1.28852e-07 6.16699 0.634589 6.16699 1.41699V6.08301C6.16699 6.86541 5.5324 7.5 4.75 7.5H1.41699C0.634589 7.5 0 6.86541 0 6.08301V1.41699C0 0.634589 0.634589 0 1.41699 0H4.75ZM1.5 6H4.66699V1.5H1.5V6ZM12.083 0C12.8654 1.28852e-07 13.5 0.634589 13.5 1.41699V3.41699C13.4998 4.19925 12.8653 4.83301 12.083 4.83301H8.75C7.96785 4.83283 7.33318 4.19914 7.33301 3.41699V1.41699C7.33301 0.634697 7.96775 0.000175814 8.75 0H12.083ZM8.83301 3.33301H12V1.5H8.83301V3.33301Z"
                            fill="#020617"
                        />
                    </svg>
                    View Project <ChevronRight className="w-4 h-4" />
                </Button>
            </div>

            {/* Project Metrics */}
            <div className="flex gap-4 items-end">
                <MetricItem
                    label="TRL"
                    value={metrics.tbl.value}
                    change={metrics.tbl.change}
                    isPositive={metrics.tbl.isPositive}
                />
                <div className="w-px h-22 bg-border" />
                <MetricItem
                    label="MRL"
                    value={metrics.mrl.value}
                    change={metrics.mrl.change}
                    isPositive={metrics.mrl.isPositive}
                />
                <div className="w-px h-22 bg-border" />
                <MetricItem
                    label="CRL"
                    value={metrics.crl.value}
                    change={metrics.crl.change}
                    isPositive={metrics.crl.isPositive}
                />
                <div className="w-px h-22 bg-border" />
                <MetricItem
                    label="SIRL"
                    value={metrics.sirl.value}
                    change={metrics.sirl.change}
                    isPositive={metrics.sirl.isPositive}
                />

                <div className="flex-1" />

                {/* Q2 Budget Spent */}
                <div className="flex flex-col gap-4 px-[16px] py-[12px] items-end">
                    <div className="text-neutral-500 text-right font-inter text-base font-medium leading-6">Q2 Budget Spent</div>
                    <div className="text-[#020617] text-right font-inter text-2xl font-semibold leading-[120%] ">
                        {budgetSpent}
                    </div>
                </div>


                {/* Q2 Progress */}
                <div className="flex flex-col gap-4 px-[16px] py-[12px] items-end">
                    <div className="text-neutral-500 text-right font-inter text-base font-medium leading-6">Q2 Progress</div>
                    <div className="text-[#020617] text-right font-inter text-2xl font-semibold leading-[120%] ">
                        {progress}
                    </div>
                </div>
            </div>
        </div>
    );
}
