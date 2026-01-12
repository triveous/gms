'use client';

import {
  ChainOfThought,
  ChainOfThoughtContent,
  ChainOfThoughtHeader,
  ChainOfThoughtStep,
} from '@/components/ai-elements/chain-of-thought';

interface Thought {
  title: string;
  thought: string;
}

interface ChainOfThoughtData {
  thoughts: Thought[];
  thoughts_duration?: string;
}


const ChainOfThoughtComponent = ({ 
  open, 
  data, 
  status 
}: { 
  open: boolean; 
  data?: ChainOfThoughtData; 
  status?: string;
}) => {
  const isComplete = status === 'ready';
  const headerText = isComplete ? 'Thoughts' : 'Thinking';
  const isOpen = isComplete ? false : open;

  return (
    <ChainOfThought defaultOpen={isOpen}>
      <ChainOfThoughtHeader>
        {headerText}
      </ChainOfThoughtHeader>
      <ChainOfThoughtContent>
        {data?.thoughts && (
          data.thoughts.map((thought, index) => (
            <ChainOfThoughtStep
              key={index}
              icon={<div className="rounded-xl bg-[#CBD5E1] h-[8px] w-[8px] mt-0.5"></div>}
              className="text-[12px] text-[#475569] font-[400]"
              label={thought.title}
              // description={thought.thought}
              status="complete"
            />
          ))
        )}
      </ChainOfThoughtContent>
    </ChainOfThought>
  );
};

export default ChainOfThoughtComponent;
