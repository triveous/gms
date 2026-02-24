import {
    Dialog,
    DialogContent,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { X, Check, XCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
    TooltipProvider,
} from '@/components/ui/tooltip';

interface MetricValue {
    value: string;
    isPresent: boolean;
    isCorrectFormat: boolean;
    errorMessage: string;
}

interface ProjectData {
    id: string;
    title: string;
    trl: MetricValue;
    mrl: MetricValue;
    crl: MetricValue;
    sirl: MetricValue;
    progress: MetricValue;
    spend: MetricValue;
    highlights: MetricValue & { values: string[] };
    lowlights: MetricValue & { values: string[] };
    artifacts: { name: MetricValue; link: string }[];
    quarters: any[];
}

interface ReviewDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    type?: 'progress' | 'plan';
    data?: any;
    onSubmit?: () => Promise<void>;
    onCancel?: () => Promise<void>;
    isSubmitting?: boolean;
}

export function ReviewDialog({ open, onOpenChange, type = 'progress', data, onSubmit, onCancel, isSubmitting }: ReviewDialogProps) {
    const timeline = data?.timeline;
    const milestones = data?.milestones || [];
    const mappedProjects = milestones.map((m: any, idx: number) => {
        const getMetric = (code: string) => m.metrics_values?.find((v: any) => v.code === code);

        const formatMetric = (metric: any, value: string) => {
            const isPresent = metric ? (metric.isPresent ?? true) : false;
            const isCorrectFormat = metric ? (metric.isCorrectFormat ?? true) : true;
            return {
                value: value || '',
                isPresent,
                isCorrectFormat,
                errorMessage: metric?.errorMessage || (!isPresent ? 'This value is missing from the document.' :
                    !isCorrectFormat ? 'The format of this value is invalid.' : '')
            };
        };

        const trlMetric = getMetric('trl');
        const mrlMetric = getMetric('mrl');
        const crlMetric = getMetric('crl');
        const sirlMetric = getMetric('sirl');
        const progressMetric = getMetric('progress');
        const spendMetric = getMetric('budget-spent');
        const hlMetric = getMetric('hl');
        const llMetric = getMetric('ll');

        return {
            id: String(idx + 1),
            title: m.project || m.title || `Project ${idx + 1}`,
            trl: formatMetric(trlMetric, trlMetric?.data_int != null ? String(trlMetric.data_int) : ''),
            mrl: formatMetric(mrlMetric, mrlMetric?.data_int != null ? String(mrlMetric.data_int) : ''),
            crl: formatMetric(crlMetric, crlMetric?.data_int != null ? String(crlMetric.data_int) : ''),
            sirl: formatMetric(sirlMetric, sirlMetric?.data_int != null ? String(sirlMetric.data_int) : ''),
            progress: formatMetric(progressMetric, progressMetric?.data_float != null ? `${progressMetric.data_float}%` : ''),
            spend: formatMetric(spendMetric, spendMetric?.data_string || ''),
            highlights: {
                ...formatMetric(hlMetric, ''),
                values: hlMetric?.data_string ? [hlMetric.data_string] : []
            },
            lowlights: {
                ...formatMetric(llMetric, ''),
                values: llMetric?.data_string ? [llMetric.data_string] : []
            },
            artifacts: m.artifacts?.map((art: any) => ({
                name: {
                    value: art.title || '',
                    isPresent: !!art.title,
                    isCorrectFormat: true,
                    errorMessage: !art.title ? 'The artifact name is missing.' : ''
                },
                link: art.link
            })) || [],
            quarters: (m.quarters && m.quarters.length > 0)
                ? m.quarters.map((q: any) => ({
                    q: q.quarter || q.q || 'Missing !',
                    goals: (q.goals && q.goals.length > 0) ? q.goals : ['Missing !'],
                    budget: q.budget || 'Missing !',
                    badge: q.badge || ''
                }))
                : [{
                    q: timeline?.quarter || 'Missing !',
                    goals: (getMetric('goal')?.data_string)
                        ? getMetric('goal')?.data_string.split('\n').map((g: string) => g.trim()).filter(Boolean)
                        : ['Missing !'],
                    budget: m.forecasted_amount
                        ? new Intl.NumberFormat('en-IN', {
                            style: 'currency',
                            currency: 'INR',
                            maximumFractionDigits: 0
                        }).format(Number(m.forecasted_amount))
                        : 'Missing !',
                    badge: ''
                }]
        };
    });

    const projectsToRender = mappedProjects;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-[95vw] sm:max-w-[906px] w-full p-0 gap-0 rounded-xl overflow-hidden" showCloseButton={false}>
                <TooltipProvider delayDuration={0}>
                    <div className="flex flex-col h-[85vh] max-h-[800px]">
                        {/* Header */}
                        <div className="flex items-center justify-between p-6 border-b">
                            <div>
                                <DialogTitle className="text-[22px] font-semibold text-slate-900 mb-3">
                                    {type === 'plan' ? 'Review Plan' : 'Review Progress'}
                                </DialogTitle>
                                <div className="flex gap-2">
                                    <Badge variant="secondary" className="bg-[#F1F5F9] text-[#475569] hover:bg-slate-200 font-normal border-[#E2E8F0] border text-sm py-1 px-3">
                                        Year Timeline: {timeline?.program_year ? (
                                            timeline.program_year
                                        ) : (
                                            <span className="text-[#EF4444] font-medium">Missing !</span>
                                        )}
                                    </Badge>
                                    <Badge variant="secondary" className="bg-[#F1F5F9] text-[#475569] hover:bg-slate-200 font-normal border-[#E2E8F0] border text-sm py-1 px-3">
                                        Quarter: {timeline?.quarter ? (
                                            `${timeline.quarter} ${timeline.reporting_period || ''}`
                                        ) : (
                                            <span className="text-[#EF4444] font-medium">Missing !</span>
                                        )}
                                    </Badge>
                                </div>
                            </div>
                            <Button variant="secondary" className="bg-[#F8FAFC] flex items-center gap-1 hover:bg-slate-200 text-slate-700 font-medium" onClick={() => onOpenChange(false)}>
                                <X className="w-4 h-4" />
                                Close
                            </Button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-y-auto p-6 bg-white">
                            {projectsToRender.length > 0 ? (
                                <Accordion type="single" collapsible defaultValue={projectsToRender[0]?.id} className="w-full space-y-4">
                                    {projectsToRender.map((project: ProjectData) => (
                                        <AccordionItem key={project.id} value={project.id} className="border-0 border-b border-slate-200 mb-0 shadow-none data-[state=open]:border-slate-200">
                                            <AccordionTrigger className="px-0 py-4 hover:bg-transparent hover:no-underline text-[16px] font-medium text-slate-900 [&[data-state=open]]:bg-white">
                                                {project.title}
                                            </AccordionTrigger>
                                            <AccordionContent className="p-0 border border-slate-200 rounded-md overflow-hidden mt-2 mb-6">
                                                <div className="bg-white flex flex-col">
                                                    {type === 'progress' ? (
                                                        <>
                                                            <div className="grid grid-cols-6 border-b border-slate-200 bg-[#E2E8F0]/50">
                                                                {['TRL', 'MRL', 'CRL', 'SIRL', 'Progress', 'Actual Spend'].map((heading, i) => (
                                                                    <div key={heading} className={cn(
                                                                        "py-3 px-4 text-center text-[14px] font-medium text-[#1E293B]",
                                                                        i < 5 && "border-r border-slate-200"
                                                                    )}>
                                                                        {heading}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                            <div className="grid grid-cols-6 border-b border-slate-200 min-h-[60px]">
                                                                {[project.trl, project.mrl, project.crl, project.sirl, project.progress, project.spend].map((metric, i) => (
                                                                    <div key={i} className={cn(
                                                                        "py-2 px-2 text-center flex items-center justify-center",
                                                                        i < 5 && "border-r border-slate-200"
                                                                    )}>
                                                                        {!metric.isPresent || !metric.isCorrectFormat ? (
                                                                            <Tooltip>
                                                                                <TooltipTrigger className="flex items-center text-[#EF4444] text-[14px] font-medium cursor-default">
                                                                                    {!metric.isPresent ? 'Missing !' : 'Invalid Format !'}
                                                                                </TooltipTrigger>
                                                                                <TooltipContent side="bottom" className="bg-black text-white p-2 text-xs">
                                                                                    {metric.errorMessage}
                                                                                </TooltipContent>
                                                                            </Tooltip>
                                                                        ) : (
                                                                            <span className="text-[#0F172A] text-[14px] font-medium">{metric.value}</span>
                                                                        )}
                                                                    </div>
                                                                ))}
                                                            </div>

                                                            {/* Highlights */}
                                                            <div className="bg-[#E2E8F0]/50 py-3 px-4 border-b border-slate-200 font-medium text-[#1E293B] text-[14px]">
                                                                Highlights
                                                            </div>
                                                            <div className="flex flex-col">
                                                                {!project.highlights.isPresent || !project.highlights.isCorrectFormat ? (
                                                                    <div className="py-4 px-4">
                                                                        <Tooltip>
                                                                            <TooltipTrigger className="flex items-center text-[#EF4444] text-[14px] font-medium cursor-default">
                                                                                {!project.highlights.isPresent ? 'Missing !' : 'Invalid Format !'}
                                                                            </TooltipTrigger>
                                                                            <TooltipContent side="bottom" className="bg-black text-white p-2 text-xs">
                                                                                {project.highlights.errorMessage}
                                                                            </TooltipContent>
                                                                        </Tooltip>
                                                                    </div>
                                                                ) : project.highlights.values.length > 0 ? project.highlights.values.map((hlt: string, i: number) => (
                                                                    <div key={i} className={cn(
                                                                        "py-4 px-4 text-[14px] text-[#0F172A]",
                                                                        i < project.highlights.values.length - 1 && "border-b border-slate-100"
                                                                    )}>
                                                                        {hlt}
                                                                    </div>
                                                                )) : (
                                                                    <div className="py-4 px-4 text-[14px] text-slate-500">No highlights</div>
                                                                )}
                                                            </div>

                                                            {/* Lowlights */}
                                                            <div className="bg-[#E2E8F0]/50 py-3 px-4 border-y border-slate-200 font-medium text-[#1E293B] text-[14px] mt-0">
                                                                Lowlights
                                                            </div>
                                                            <div className="py-4 px-4">
                                                                {!project.lowlights.isPresent || !project.lowlights.isCorrectFormat ? (
                                                                    <Tooltip>
                                                                        <TooltipTrigger className="flex items-center text-[#EF4444] text-[14px] font-medium cursor-default">
                                                                            {!project.lowlights.isPresent ? 'Missing !' : 'Invalid Format !'}
                                                                        </TooltipTrigger>
                                                                        <TooltipContent side="bottom" className="bg-black text-white p-2 text-xs">
                                                                            {project.lowlights.errorMessage}
                                                                        </TooltipContent>
                                                                    </Tooltip>
                                                                ) : project.lowlights.values.length > 0 ? project.lowlights.values.map((hlt: string, i: number) => (
                                                                    <div key={i} className="text-[14px] text-[#0F172A]">
                                                                        {hlt}
                                                                    </div>
                                                                )) : (
                                                                    <div className="text-[14px] text-slate-500">No lowlights</div>
                                                                )}
                                                            </div>

                                                            {/* Artifacts */}
                                                            <div className="bg-[#E2E8F0]/50 py-3 px-4 border-y border-slate-200 font-medium text-[#1E293B] text-[14px]">
                                                                Artifacts
                                                            </div>
                                                            {project.artifacts.length > 0 ? (
                                                                <div className="w-full">
                                                                    <div className="grid grid-cols-2 border-b border-slate-200">
                                                                        <div className="py-4 px-4 text-[14px] text-[#0F172A] border-r border-slate-200 bg-white font-normal">Name</div>
                                                                        <div className="py-4 px-4 text-[14px] text-[#0F172A] bg-white font-normal">Link</div>
                                                                    </div>
                                                                    {project.artifacts.map((art: { name: MetricValue; link: string }, i: number) => (
                                                                        <div key={i} className={cn(
                                                                            "grid grid-cols-2",
                                                                            i < project.artifacts.length - 1 && "border-b border-slate-200"
                                                                        )}>
                                                                            <div className="py-4 px-4 text-[14px] text-[#0F172A] border-r border-slate-200 flex items-center bg-white">
                                                                                {!art.name.isPresent || !art.name.isCorrectFormat ? (
                                                                                    <Tooltip>
                                                                                        <TooltipTrigger className="flex items-center text-[#EF4444] text-[14px] font-medium cursor-default">
                                                                                            {!art.name.isPresent ? 'Missing !' : 'Invalid Format !'}
                                                                                        </TooltipTrigger>
                                                                                        <TooltipContent side="bottom" className="bg-black text-white p-2 text-xs">
                                                                                            {art.name.errorMessage}
                                                                                        </TooltipContent>
                                                                                    </Tooltip>
                                                                                ) : (
                                                                                    art.name.value
                                                                                )}
                                                                            </div>
                                                                            <div className="py-4 px-4 text-[14px] text-[#0F172A] flex items-center bg-white break-all">
                                                                                <a href={art.link} target="_blank" rel="noopener noreferrer" className="text-[#0F172A] hover:underline hover:text-blue-600 transition-colors">
                                                                                    {art.link}
                                                                                </a>
                                                                            </div>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            ) : (
                                                                <div className="py-4 px-4 text-[14px] text-slate-500 bg-white">No artifacts available</div>
                                                            )}
                                                        </>
                                                    ) : (
                                                        <div className="flex flex-col w-full">
                                                            {project.quarters?.map((quarter: any, qIndex: number) => (
                                                                <div key={qIndex} className="flex flex-col w-full">
                                                                    <div className="grid grid-cols-[1fr_150px] border-b border-slate-200 bg-[#E2E8F0]/50">
                                                                        <div className="py-3 px-4 text-[14px] font-medium text-[#1E293B] border-r border-slate-200">
                                                                            {quarter.q} | Goals / Deliverables
                                                                        </div>
                                                                        <div className="py-3 px-4 text-[14px] font-medium text-[#1E293B]">
                                                                            Budget
                                                                        </div>
                                                                    </div>
                                                                    <div className={cn("grid grid-cols-[1fr_150px]", qIndex < project.quarters!.length - 1 && "border-b border-slate-200")}>
                                                                        <div className="py-5 px-4 text-[14px] text-[#0F172A] border-r border-slate-200 bg-white">
                                                                            {quarter.goals[0] === 'Missing !' ? (
                                                                                <div className="text-[#EF4444] font-medium h-full flex items-center">Missing !</div>
                                                                            ) : (
                                                                                <div className="flex flex-col gap-5">
                                                                                    {quarter.goals.map((goal: string, gIndex: number) => (
                                                                                        <div key={gIndex} className="text-[#0F172A] leading-relaxed">{goal}</div>
                                                                                    ))}
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                        <div className="py-5 px-4 text-[14px] flex flex-col items-center justify-center gap-2 bg-[#F8FAFC]">
                                                                            {quarter.budget === 'Invalid Format !' ? (
                                                                                <div className="text-[#EF4444] font-medium text-center leading-snug">
                                                                                    Invalid<br />Format !
                                                                                </div>
                                                                            ) : quarter.budget === 'Missing !' ? (
                                                                                <div className="text-[#EF4444] font-medium text-center leading-snug">
                                                                                    Missing !
                                                                                </div>
                                                                            ) : (
                                                                                <>
                                                                                    <div className="font-semibold text-[#0F172A]">{quarter.budget}</div>
                                                                                    {quarter.badge && (
                                                                                        <Badge variant="secondary" className="bg-[#E2E8F0] text-[#475569] hover:bg-[#E2E8F0] font-medium border-0 text-[11px] py-0.5 px-2.5 rounded-full shadow-sm">
                                                                                            {quarter.badge}
                                                                                        </Badge>
                                                                                    )}
                                                                                </>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            </AccordionContent>
                                        </AccordionItem>
                                    ))}
                                </Accordion>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full py-20 text-center">
                                    <span className="text-[#EF4444] text-[32px] font-bold mb-2">Missing !</span>
                                    <p className="text-[#64748B] text-[16px]">No data was found in the document.</p>
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t flex items-center justify-end gap-3 bg-white">
                            <Button variant="secondary" className="bg-[#F8FAFC] border border-[#E2E8F0] hover:bg-slate-100 text-[#0F172A] font-medium h-10 px-4 flex items-center gap-2"
                                onClick={onCancel}
                                disabled={isSubmitting}
                            >
                                <XCircle className="w-[18px] h-[18px]" />
                                Cancel
                            </Button>
                            <Button
                                className="bg-[#059669] hover:bg-emerald-700 text-white font-medium h-10 px-4 flex items-center gap-2"
                                onClick={onSubmit}
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? (
                                    <Loader2 className="w-[18px] h-[18px] animate-spin" />
                                ) : (
                                    <Check className="w-[18px] h-[18px]" />
                                )}
                                {isSubmitting ? 'Submitting...' : 'Approve and Submit'}
                            </Button>
                        </div>
                    </div>
                </TooltipProvider>
            </DialogContent>
        </Dialog>
    );
}
