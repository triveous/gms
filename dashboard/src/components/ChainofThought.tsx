'use client';

import React from 'react';
import {
  ChainOfThought,
  ChainOfThoughtContent,
  ChainOfThoughtHeader,
  ChainOfThoughtStep,
} from '@/components/ai-elements/chain-of-thought';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { Search, FileText, File } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

export interface KBQuery {
  query: string;
  limit: number;
}

export interface KBSource {
  name: string;
}

export interface KBStep {
  id: string;
  type: 'KB_SEARCH' | 'BROWSE_KB_RESULT';
  kb_search?: {
    goal_id: string;
    queries: KBQuery[];
  };
  browse_kb_result?: {
    goal_id: string;
    sources: KBSource[];
  };
}

export interface Goal {
  id: string;
  description: string;
  final: boolean;
}

export interface DataBlock {
  type: 'data-block';
  id: 'plan' | 'step';
  data: {
    usage: 'plan' | 'step';
    plan_content?: {
      goals: Goal[];
    };
    step_content?: {
      steps: KBStep[];
      progress: string;
      final: boolean;
    };
  };
}

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
    const goalsMap: Record<string, { goal: Goal; steps: KBStep[] }> = {};
    const goalOrder: string[] = [];

    if (!blocks || blocks.length === 0) return [];

    // First pass: collect goals from 'plan' blocks
    blocks.forEach(block => {
      if (block.type === 'data-block' && block.id === 'plan' && block.data.plan_content) {
        block.data.plan_content.goals.forEach(g => {
          const gid = String(g.id);
          if (!goalsMap[gid]) {
            goalsMap[gid] = { goal: g, steps: [] };
            goalOrder.push(gid);
          } else {
            goalsMap[gid].goal = g;
          }
        });
      }
    });

    // Second pass: collect steps from 'step' blocks and associate them with goals
    blocks.forEach(block => {
      if (block.type === 'data-block' && block.id === 'step' && block.data.step_content) {
        block.data.step_content.steps.forEach(s => {
          const goalIdRaw = s.kb_search?.goal_id || s.browse_kb_result?.goal_id;
          if (goalIdRaw !== undefined && goalIdRaw !== null) {
            const gid = String(goalIdRaw);
            // If goal doesn't exist in map yet, create a placeholder to ensure it's rendered
            if (!goalsMap[gid]) {
              goalsMap[gid] = { 
                goal: { id: gid, description: 'Thinking...', final: false },
                steps: [] 
              };
              goalOrder.push(gid);
            }
            // Add step if not already present
            if (!goalsMap[gid].steps.find(existing => existing.id === s.id)) {
              goalsMap[gid].steps.push(s);
            }
          }
        });
      }
    });

    return goalOrder.map(id => goalsMap[id]);
  }, [blocks]);

  const mainStepsCount = organizedGoals.length;
  const headerText = isComplete ? `${mainStepsCount} steps completed` : 'Thinking';

  return (
    <ChainOfThought key={isComplete ? 'complete' : 'active'} defaultOpen={isComplete ? false : open}>
      <ChainOfThoughtHeader>
        {headerText === 'Thinking' ? <Shimmer>{headerText}</Shimmer> : headerText}
      </ChainOfThoughtHeader>
      <ChainOfThoughtContent>
        <div className="relative">
          {/* Vertical line connecting all dots */}
          <div className="absolute left-[3px] top-2 bottom-2 w-[1px] bg-[#CBD5E1]"></div>
          
          {organizedGoals.map((gObj) => (
            <React.Fragment key={gObj.goal.id}>
              {/* Goal Step */}
              <div className="relative mb-4">
                <ChainOfThoughtStep
                  icon={<div className="rounded-xl bg-[#CBD5E1] h-[8px] w-[8px] mt-0.5 relative z-10"></div>}
                  className="text-[12px] text-[#334155] font-[400] [&>div:first-child>div:last-child]:hidden"
                  label={gObj.goal.description}
                  status="complete"
                />
              </div>

              {/* Substeps for this goal */}
              {gObj.steps.map((step) => {
                if (step.type === 'KB_SEARCH' && step.kb_search) {
                  return (
                    <div key={step.id} className="mb-3 relative pl-6">
                      <div className="text-[12px] text-[#94A3B8] font-[400] mb-2">
                        Searching relevant information
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {step.kb_search.queries.map((query, idx) => (
                          <Tooltip key={idx}>
                            <TooltipTrigger asChild>
                              <div
                                className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-[#CBD5E1] text-[13px] text-[#475569] max-w-[200px] cursor-default"
                              >
                                <Search className="h-3.5 w-3.5 text-[#64748B] shrink-0" />
                                <span className="truncate">{query.query}</span>
                              </div>
                            </TooltipTrigger>
                            <TooltipContent 
                              side="bottom" 
                              sideOffset={4}
                              showArrow={false}
                              className="bg-[#F8FAFC] text-[#475569] border border-[#CBD5E1] shadow-sm font-medium py-1.5 px-3 text-[13px] rounded-[4px]"
                            >
                              {query.query}
                            </TooltipContent>
                          </Tooltip>
                        ))}
                      </div>
                    </div>
                  );
                } else if (step.type === 'BROWSE_KB_RESULT' && step.browse_kb_result) {
                  return (
                    <div key={step.id} className="mb-3 relative pl-6">
                      <div className="text-[12px] text-[#94A3B8] font-[400] mb-2">
                        Reading files
                      </div>
                      <div className="border border-[#CBD5E1] rounded-md bg-white p-3 space-y-1">
                        {step.browse_kb_result.sources.map((source, idx) => (
                          <Tooltip key={idx}>
                            <TooltipTrigger asChild>
                              <div
                                className="flex items-center gap-2 py-1.5 text-[13px] text-[#475569] cursor-default overflow-hidden"
                              >
                                <File className="h-3.5 w-3.5 text-[#64748B] shrink-0" />
                                <span className="truncate">{source.name}</span>
                              </div>
                            </TooltipTrigger>
                            <TooltipContent 
                              side="bottom" 
                              sideOffset={4}
                              showArrow={false}
                              className="bg-[#F8FAFC] text-[#475569] border border-[#CBD5E1] shadow-sm font-medium py-1.5 px-3 text-[13px] rounded-[4px]"
                            >
                              {source.name}
                            </TooltipContent>
                          </Tooltip>
                        ))}
                      </div>
                    </div>
                  );
                }
                return null;
              })}
            </React.Fragment>
          ))}
          
          {/* If it's complete, optionally show a Finished step if required, 
              but the new structure doesn't explicitly have a "finished" type anymore */}
          {isComplete && organizedGoals.length > 0 && (
             <div className="relative mb-4">
                <ChainOfThoughtStep
                  icon={<div className="rounded-xl bg-[#CBD5E1] h-[8px] w-[8px] mt-0.5 relative z-10"></div>}
                  className="text-[12px] text-[#334155] font-[400] [&>div:first-child>div:last-child]:hidden"
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
