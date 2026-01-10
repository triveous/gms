import { useState, useEffect, Fragment } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import SmoothWordAnimation from '@/components/SmoothWordAnimation';
import MarkdownRenderer from './MarkdownRenderer';

interface MessagePart {
    type: 'text' | string;
    text?: string;
}

interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | string;
    parts: MessagePart[];
}

interface ChatConversationProps {
  messages: ChatMessage[];
  status: string;
  activeToolUI: { tool: string; state: string; query?: string } | null;
}


const TOOL_CONFIG: Record<string, { label: string }> = {
    'research-tool': { label: 'Researching...' },
};

const getToolLabel = (toolName: string) => {
    return TOOL_CONFIG[toolName]?.label || 'Processing...';
};

const ChatConversation = ({ messages, status, activeToolUI }: ChatConversationProps) => {
  const [isExiting, setIsExiting] = useState(false);
  const [prevStatus, setPrevStatus] = useState(status);
  // Track if this session has seen active streaming (to distinguish new vs history)
  const [hasActiveStream, setHasActiveStream] = useState(false);


  useEffect(() => {
    if (status === 'streaming' || status === 'submitted') {
        setHasActiveStream(true);
    }

    // When status becomes 'ready', we start the smooth transition sequence
    if (status === 'ready' && prevStatus !== 'ready') {
        setIsExiting(true);
        // Delay showing the final message content to allow the progress to "vanish"
        const timer = setTimeout(() => {
            setIsExiting(false);
        }, 800); // 800ms for a smooth vanish effect
        return () => clearTimeout(timer);
    } else if (status !== 'ready') {
        setIsExiting(false);
    }
    setPrevStatus(status);
  }, [status, prevStatus]);

  return (
    <div className="flex flex-col-reverse gap-6">
      {/* Error Message */}
      {status === 'error' && (
        <div className="flex w-full justify-center py-2">
            <span className="text-sm text-red-500">Oops! Something went wrong. Please try again.</span>
        </div>
      )}

      {/* Tool Progress - shown even during exit animation */}
      {(activeToolUI && (status !== 'ready')) && (
        <div className={cn(
            'relative min-h-[40px] w-full mb-2 overflow-hidden transition-all duration-700 ease-in-out mt-[-24px]',
            isExiting ? 'opacity-0 -translate-y-4 blur-sm' : 'opacity-100 translate-y-0'
        )}>
           <div className="flex flex-col gap-1.5 animate-in fade-in slide-in-from-bottom-2 duration-500">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-[#475569]" />
                <span className="text-[14px] font-medium text-slate-700">
                    {getToolLabel(activeToolUI.tool)}
                </span>
              </div>
              <p className="text-[13px] text-slate-500 ml-6 leading-tight">
                {activeToolUI.query}
              </p>
            </div>
        </div>
      )}

      {/* Messages */}
      {[...messages].reverse().map((message, index) => {

        const isLatestAssistant = index === 0 && message.role !== 'user';

        const shouldAnimate = isLatestAssistant && hasActiveStream;
        
        const hasTextContent = message.parts.some(p => p.type === 'text' && p.text && p.text.trim().length > 0);

        if (!hasTextContent) return null;

        const showDivider = message.role === 'user' && index < messages.length - 1;

        return (
            <Fragment key={message.id}>
                <div
                    className={cn(
                        'flex flex-col w-full',
                        message.role === 'user' ? 'items-end animate-in fade-in slide-in-from-bottom-2 duration-700' : 'items-start'
                    )}
                >
                    {message.role === 'user' ? (
                        <div className="bg-white border border-slate-200 rounded-[6px] px-4 py-2 text-sm text-slate-700 max-w-[85%]">
                            {message.parts.map((part, idx) => 
                                part.type === 'text' ? <span key={idx}>{part.text}</span> : null
                            )}
                        </div>
                    ) : (
                        <div className="text-sm text-foreground leading-relaxed w-full">
                        <div className="prose prose-sm max-w-none dark:prose-invert prose-table:border-collapse prose-table:w-full prose-th:border prose-th:border-border prose-th:bg-muted prose-th:p-2 prose-th:text-left prose-td:border prose-td:border-border prose-td:p-2">
                            {message.parts.map((part, idx) => 
                                part.type === 'text' && part.text ? (
                                shouldAnimate ? (
                                    <SmoothWordAnimation key={idx} text={part.text} useMarkdown={true} />
                                ) : (
                                    <MarkdownRenderer key={idx} content={part.text} />
                                )
                                ) : null
                            )}
                        </div>
                        </div>
                    )}
                </div>
                {showDivider && (
                    <div className="w-full h-[1px] bg-slate-200/60" />
                )}
            </Fragment>
        );
      })}
    </div>
  );
};

export default ChatConversation;
