'use client';

import React from 'react';
import {
  ChainOfThought,
  ChainOfThoughtContent,
  ChainOfThoughtHeader,
  ChainOfThoughtStep,
} from '@/components/ai-elements/chain-of-thought';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { Search, File } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface KBQuery {
  query: string;
  limit: number;
}

interface KBSource {
  id: string;
  title: string
  page: number
}

interface ChainStep {
  id: string;
  type: 'search_kb' | 'browse_kb';
  content: {
    queries?: KBQuery[];
    sources?: KBSource[];
  };
}

interface Goal {
  id: string;
  description: string;
  final: boolean;
}

interface DataBlock {
  type: 'data-goal' | 'data-step';
  id: string;
  data: any;
  transient?: boolean;
}

interface DataGoal extends DataBlock {
  type: 'data-goal';
  data: {
    id: string;
    text: string;
    status: string;
  };
}

interface DataStep extends DataBlock {
  type: 'data-step';
  data: {
    id: string;
    type: string;
    goal_id: string;
    content: {
      query?: string[];
      sources?: string[] | { name: string }[];
    };
    progress: string;
  };
}

const TruncatedSourceItem = ({ title }: { title: string }) => {
  const [isTruncated, setIsTruncated] = React.useState(false);
  const textRef = React.useRef<HTMLSpanElement>(null);

  React.useLayoutEffect(() => {
    const element = textRef.current;
    if (element) {
        setIsTruncated(element.scrollWidth > element.clientWidth);
    }
  }, [title]);

  const content = (
      <div className="flex items-center gap-2 py-1.5 text-[13px] text-[#475569] cursor-default overflow-hidden max-w-full">
        <File className="h-3.5 w-3.5 text-[#64748B] shrink-0" />
        <span ref={textRef} className="truncate">{title}</span>
      </div>
  );

  if (!isTruncated) return content;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        {content}
      </TooltipTrigger>
      <TooltipContent
        side="bottom"
        sideOffset={4}
        showArrow={false}
        className="bg-[#F8FAFC] text-[#475569] border border-[#CBD5E1] shadow-sm font-medium py-1.5 px-3 text-[13px] rounded-[4px]"
      >
        {title}
      </TooltipContent>
    </Tooltip>
  );
};

const ChainOfThoughtComponent = ({
  open,
  data,
  status
}: {
  open: boolean;
  data?: DataBlock | DataBlock[];
  status?: string;
}) => {
  const isComplete = status === 'ready';

  const blocks = React.useMemo(() => {
    if (!data) return [];
    return Array.isArray(data) ? data : [data];
  }, [data]);

  const organizedGoals = React.useMemo(() => {
    const goalsMap: Record<string, { goal: Goal; steps: ChainStep[] }> = {};
    const goalOrder: string[] = [];

    if (!blocks || blocks.length === 0) return [];

    // Collect goals from 'data-goal'
    blocks.forEach(block => {
      if (block.type === 'data-goal') {
        const g = (block as DataGoal).data;
        const gid = String(g.id);
        const goalObj: Goal = {
          id: gid,
          description: g.text,
          final: g.status === 'completed'
        };

        if (!goalsMap[gid]) {
          goalsMap[gid] = { goal: goalObj, steps: [] };
          goalOrder.push(gid);
        } else {
          goalsMap[gid].goal = goalObj;
        }
      }
    });

    // Collect steps from 'data-step'
    blocks.forEach(block => {
      if (block.type === 'data-step') {
        const s = (block as DataStep).data;
        const gid = String(s.goal_id);

        if (gid) {
          if (!goalsMap[gid]) {
            goalsMap[gid] = {
              goal: { id: gid, description: 'Thinking...', final: false },
              steps: []
            };
            goalOrder.push(gid);
          }

          let newStep: ChainStep | null = null;

          if (s.type === 'search_kb') {
            newStep = {
              id: s.id,
              type: 'search_kb',
              content: {
                queries: (s.content.query || []).map((q) => ({ query: q, limit: 5 }))
              }
            };
          } else if (s.type === 'browse_kb' || s.type === 'read_kb') {
            const sources = s.content.sources || [];
            const mappedSources = sources.map((src) =>
              typeof src === 'string' ? { name: src } : src
            );

            newStep = {
              id: s.id,
              type: 'browse_kb',
              content: {
                sources: mappedSources
              }
            };
          }

          if (newStep && !goalsMap[gid].steps.find(existing => existing.id === newStep!.id)) {
            goalsMap[gid].steps.push(newStep);
          }
        }
      }
    });

    return goalOrder.map(id => goalsMap[id]);
  }, [blocks]);

  const mainStepsCount = organizedGoals.length;
  const headerText = isComplete ? `${mainStepsCount} steps completed` : 'Thinking';

  return (
    <ChainOfThought key={isComplete ? 'complete' : 'active'} defaultOpen={isComplete ? false : open}>
      <ChainOfThoughtHeader hideChevron={!isComplete}>
        {headerText === 'Thinking' ? <Shimmer>{headerText}</Shimmer> : headerText}
      </ChainOfThoughtHeader>
      <ChainOfThoughtContent>
        <div className="relative">
          <div className="absolute left-[3px] top-2 bottom-2 w-[1px] bg-[#CBD5E1]"></div>

          {organizedGoals.map((gObj) => (
            <React.Fragment key={gObj.goal.id}>
              <div className="relative mb-4">
                <ChainOfThoughtStep
                  icon={<div className="rounded-xl bg-[#CBD5E1] h-[8px] w-[8px] mt-0.5 relative z-10"></div>}
                  className="text-[14px] text-[#334155] font-[400] [&>div:first-child>div:last-child]:hidden"
                  label={gObj.goal.description}
                  status="complete"
                />
              </div>

              {gObj.steps.map((step) => {
                if (step.type === 'search_kb' && step.content.queries) {
                  return (
                    <div key={step.id} className="mb-3 relative pl-6">
                      <div className="text-[12px] text-[#94A3B8] font-[400] mb-2">
                        Searching relevant information
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {step.content.queries.map((query, idx) => (
                          <div key={idx} className="flex gap-2 px-3 py-1.5 rounded-md border border-[#CBD5E1] text-[13px] text-[#475569]  cursor-default">
                            <Search className={`h-3.5 w-3.5 text-[#64748B] ${query.query.length>40 ? 'mt-1' : 'mt-0.5'} shrink-0`} />
                            <span className="">{query.query}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                } else if (step.type === 'browse_kb' && step.content.sources) {
                  return (
                    <div key={step.id} className="mb-3 relative pl-6">
                      <div className="text-[12px] text-[#94A3B8] font-[400] mb-2">
                        Reading files
                      </div>
                      <div className="border border-[#CBD5E1] rounded-md bg-white p-3 space-y-1">
                        {step.content.sources.map((source, idx) => (
                          <TruncatedSourceItem key={idx} title={source.title} />
                        ))}
                      </div>
                    </div>
                  );
                }
                return null;
              })}
            </React.Fragment>
          ))}

          {isComplete && organizedGoals.length > 0 && (
            <div className="relative mb-4">
              <ChainOfThoughtStep
                icon={<div className="rounded-xl bg-[#CBD5E1] h-[8px] w-[8px] mt-0.5 relative z-10"></div>}
                className="text-[14px] text-[#334155] font-[400] [&>div:first-child>div:last-child]:hidden"
                label="Finished"
                status="complete"
              />
            </div>
          )}
        </div>
      </ChainOfThoughtContent>
    </ChainOfThought>
  );
};

export default ChainOfThoughtComponent;
