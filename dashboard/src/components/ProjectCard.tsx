import { Button } from '@/components/ui/button';
import { ChevronRight, LayoutList, X, CircleCheckBig, BadgeInfo } from 'lucide-react';
import { MetricItem } from './MetricItem';
import { useNavigate } from 'react-router-dom';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogClose,
} from '@/components/ui/dialog';

interface ProjectMetric {
    value: number;
    change: string;
    isPositive: boolean;
}

interface ComparisonMetric {
    current: number;
    previous: number;
    growth: number;
    growth_percent: number;
}

interface ComparisonResult {
    quarter: string;
    compare_with: string;
    metrics: {
        'Technology Readiness Level': ComparisonMetric;
        'Market Readiness Level': ComparisonMetric;
        'Commercial Readiness Level': ComparisonMetric;
        'Social Impact Readiness Level': ComparisonMetric;
    }
}

interface ProjectCardProps {
    title: string;
    id: string;
    grantId:string;
    projectLead: string;
    selectedPeriod: string;
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
    highlights?: string[] | string;
    lowlights?: string[] | string;
    comparisonData?: {
        project: string;
        result: ComparisonResult;
    };
}

export function ProjectCard({
    title,
    id,
    grantId,
    projectLead,
    activeSince,
    lastUpdated,
    selectedPeriod,
    metrics,
    budgetSpent,
    progress,
    highlights = [],
    lowlights = [],
    comparisonData,
}: ProjectCardProps) {
    const highlightsList = Array.isArray(highlights) 
        ? highlights 
        : typeof highlights === 'string' 
            ? highlights.split('\n').map(s => s.trim().replace(/^[•-]\s*/, '')).filter(Boolean)
            : [];
            
    const lowlightsList = Array.isArray(lowlights) 
        ? lowlights 
        : typeof lowlights === 'string' 
            ? lowlights.split('\n').map(s => s.trim().replace(/^[•-]\s*/, '')).filter(Boolean)
            : [];

    console.log(comparisonData);
    const navigate = useNavigate();
    
    const handleProjectClick = (projectId: string) => {
        navigate(`/${grantId}/${projectId}`);
    };

    const getMetricDisplay = (key: 'tbl' | 'mrl' | 'crl' | 'sirl', name: keyof ComparisonResult['metrics']) => {
        const defaultMetric = metrics[key];
        
        if (comparisonData?.result?.metrics?.[name]) {
            const compMetric = comparisonData.result.metrics[name];
            
            // Check if there is no growth (growth is 0)
            if (compMetric.growth === 0) {
                 return {
                    value: defaultMetric.value,
                    change: 'No Change',
                    isPositive: true // Neutral essentially, handled by component
                };
            }

            return {
                value: defaultMetric.value,
                change: `${compMetric.growth > 0 ? '+' : ''}${compMetric.growth_percent}%`,
                isPositive: compMetric.growth >= 0
            };
        }
        
        // If no comparison data, return empty change so badge is hidden
        return {
             ...defaultMetric,
             change: '' 
        };
    };

    const tblDisplay = getMetricDisplay('tbl', 'Technology Readiness Level');
    const mrlDisplay = getMetricDisplay('mrl', 'Market Readiness Level');
    const crlDisplay = getMetricDisplay('crl', 'Commercial Readiness Level');
    const sirlDisplay = getMetricDisplay('sirl', 'Social Impact Readiness Level');
    // console.log(tblDisplay, mrlDisplay, crlDisplay, sirlDisplay);
    return (
        <div className="p-6 bg-card border border-border rounded-[4px] flex flex-col gap-4">
            {/* Project Header */}
            <div className="flex gap-4">
                <div className="flex flex-col gap-6 flex-1">
                    <h3 className="text-[#020617] font-sans text-[20px] font-semibold leading-[120%] tracking-[-0.4px]">
                        {title}
                    </h3>
                    <div className="flex flex-wrap items-center gap-4 text-[#334155] font-sans text-base font-normal leading-[150%]">
                        <span>Project Lead: {projectLead}</span>
                        <span className="bg-[#E2E8F0] w-[1px] h-[24px]"></span>
                        <span>Active Since: {activeSince}</span>
                        <span className="bg-[#E2E8F0] w-[1px] h-[24px]"></span>
                        <span>Last Updated: {lastUpdated}</span>
                    </div>
                </div>
                <div className="flex gap-3">
                    <Dialog>
                        <DialogTrigger asChild>
                            <Button variant="outline" size="icon" className="h-[45px] w-[45px] border-[#E2E8F0] shadow-none">
                                <LayoutList className="size-5 text-[#0F172A]" />
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-[700px] p-6 gap-6 border-none rounded-lg overflow-hidden" showCloseButton={false}>
                            <DialogHeader className="pb-0 flex flex-row items-center justify-between">
                                <DialogTitle className="text-[#020617] font-sans text-[20px] font-semibold leading-[120%] tracking-[-0.4px]">
                                    Key Highlights & Lowlights
                                </DialogTitle>
                                <DialogClose asChild>
                                    <Button variant="ghost" size="sm" className="h-9  gap-2 bg-[#F1F5F9] text-[#0F172A] hover:bg-[#E2E8F0] border-none font-medium">
                                        <X className="w-4 h-4" /> Close
                                    </Button>
                                </DialogClose>
                            </DialogHeader>
                            <div className=" flex flex-col space-y-4">
                                <h3 className="text-[#020617] font-sans text-[16px] font-semibold leading-[140%]">
                                    {title}
                                </h3>

                                <div className="relative">
                                    <div className="space-y-6 max-h-[300px] overflow-y-auto scroll-smooth remove-scrollbar">
                                        <div className="space-y-3">
                                            <h4 className="text-[#64748B] font-sans text-[16px] font-medium">Highlights</h4>
                                            <div className="space-y-4 text-[#334155]">
                                                {highlightsList.length > 0 ? (
                                                    highlightsList.map((item, index) => (
                                                        <div key={index} className="flex gap-3 items-start">
                                                            <CircleCheckBig className="w-5 h-5 text-[#22C55E] shrink-0 mt-0.5" />
                                                            <p className="text-[#334155] text-[16px] leading-[150%]">{item}</p>
                                                        </div>
                                                    ))
                                                ) : (
                                                    <p className="text-sm italic text-[#94A3B8]">No highlights recorded for this period.</p>
                                                )}
                                            </div>
                                        </div>

                                        <div className="h-px bg-[#CBD5E1] w-full" />

                                        <div className="space-y-3">
                                            <h4 className="text-[#64748B] font-sans text-[16px] font-medium">Lowlights</h4>
                                            <div className="space-y-4 text-[#334155]">
                                                {lowlightsList.length > 0 ? (
                                                    lowlightsList.map((item, index) => (
                                                        <div key={index} className="flex gap-3 items-start">
                                                            <BadgeInfo className="w-5 h-5 text-[#F97316] shrink-0 mt-0.5" />
                                                            <p className="text-[#334155] text-[16px] leading-[150%]">{item}</p>
                                                        </div>
                                                    ))
                                                ) : (
                                                    <p className="text-sm italic text-[#94A3B8]">No lowlights recorded for this period.</p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-background to-transparent pointer-events-none z-10" />
                                </div>
                            </div>
                        </DialogContent>
                    </Dialog>
                    <Button variant="outline" className="w-[155.5px] h-[45px] px-6 gap-2  shadow-none" onClick={() => handleProjectClick(id)}>
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
            </div>

            {/* Project Metrics */}
            <div className="flex flex-wrap gap-4 items-stretch">
                <MetricItem
                    label="TRL"
                    value={tblDisplay.value}
                    change={tblDisplay.change}
                    isPositive={tblDisplay.isPositive}
                />
                <div className="w-px self-stretch bg-border" />
                <MetricItem
                    label="MRL"
                    value={mrlDisplay.value}
                    change={mrlDisplay.change}
                    isPositive={mrlDisplay.isPositive}
                />
                <div className="w-px self-stretch bg-border" />
                <MetricItem
                    label="CRL"
                    value={crlDisplay.value}
                    change={crlDisplay.change}
                    isPositive={crlDisplay.isPositive}
                />
                <div className="w-px self-stretch bg-border" />
                <MetricItem
                    label="SIRL"
                    value={sirlDisplay.value}
                    change={sirlDisplay.change}
                    isPositive={sirlDisplay.isPositive}
                />

                <div className="flex-1 block min-w-[80px]" />
                
                {/* Q2 Budget Spent */}
                <div className="flex flex-col gap-4 px-[16px] py-[12px] items-end">
                    <div className="text-neutral-500 text-right font-inter text-base font-medium leading-6">{selectedPeriod.slice(0,2)} Budget Spent</div>
                    <div className="text-[#020617] text-right font-inter text-2xl font-semibold leading-[120%] ">
                        {budgetSpent}
                    </div>
                </div>


                {/* Q2 Progress */}
                <div className="flex flex-col gap-4 px-[16px] py-[12px] items-end">
                    <div className="text-neutral-500 text-right font-inter text-base font-medium leading-6">{selectedPeriod.slice(0,2)} Progress</div>
                    <div className="text-[#020617] text-right font-inter text-2xl font-semibold leading-[120%] ">
                        {progress}
                    </div>
                </div>
            </div>
        </div>
    );
}
