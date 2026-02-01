import React from 'react';
import { Button } from '@/components/ui/button';
import { type QuickQuestion } from '@/types/chat';

interface QuickQuestionsProps {
    questions: QuickQuestion[];
    onQuestionClick: (text: string) => void;
    disabled: boolean;
}

const QuickQuestions: React.FC<QuickQuestionsProps> = ({ questions, onQuestionClick, disabled }) => {
    return (
        <div className="flex flex-col items-end text-right mb-2">
            <h3 className="text-sm font-semibold text-foreground mb-2">Quick suggestion to ask.</h3>
            <p className="text-xs text-muted-foreground mb-4">You can pick can from below or ask anything in chat.</p>

            <div className="w-full space-y-2">
                {questions.map((q: QuickQuestion) => (
                    <Button
                        key={q.name}
                        variant="outline"
                        className="w-auto justify-start text-sm h-auto py-2.5 px-3 text-left font-normal shadow-none"
                        onClick={() => onQuestionClick(q.question)}
                        disabled={disabled}
                    >
                        {q.question}
                    </Button>
                ))}
            </div>
        </div>
    );
};

export default QuickQuestions;
