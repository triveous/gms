import React from 'react';
import { useChatContext } from '@/contexts/ChatContext';
import { Button } from '@/components/ui/button';
import { X, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

const ChatPanel: React.FC = () => {
    const { isChatOpen, closeChat } = useChatContext();

    return (
        <div
            className={cn(
                "fixed top-0 right-0 h-screen min-w-[447px] bg-background   transition-transform duration-300 ease-in-out z-50",
                isChatOpen ? "translate-x-0" : "translate-x-full"
            )}
        >
            <div className="flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3  h-16">
                    <div className="flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M4.33301 7.66602C4.71154 7.66602 5.05803 7.88034 5.22754 8.21875L5.75 9.26465C5.94351 9.65169 5.98598 9.72731 6.03125 9.78613H6.03223C6.08443 9.85384 6.14505 9.91538 6.21289 9.96777C6.27191 10.0133 6.34698 10.0554 6.73438 10.249L7.78027 10.7715C8.11885 10.9408 8.33276 11.2875 8.33301 11.666C8.33301 12.0447 8.11898 12.3911 7.78027 12.5605L6.73438 13.084C6.34675 13.2777 6.27193 13.3197 6.21289 13.3652C6.14494 13.4177 6.08449 13.4791 6.03223 13.5469H6.03125C5.98594 13.6057 5.94362 13.6801 5.75 14.0674L5.22754 15.1133C5.05815 15.4521 4.71178 15.666 4.33301 15.666C3.95436 15.6659 3.60782 15.452 3.43848 15.1133L2.91602 14.0674C2.7225 13.6804 2.68007 13.6057 2.63477 13.5469H2.63379C2.58157 13.4792 2.52099 13.4176 2.45312 13.3652C2.39414 13.3198 2.31859 13.2774 1.93164 13.084L0.885742 12.5605C0.547259 12.3911 0.333008 12.0446 0.333008 11.666C0.333253 11.2876 0.547237 10.9408 0.885742 10.7715L1.93164 10.249C2.31928 10.0553 2.39409 10.0133 2.45312 9.96777C2.52112 9.91531 2.5815 9.85396 2.63379 9.78613H2.63477C2.68013 9.72726 2.72216 9.65238 2.91602 9.26465L3.43848 8.21875C3.60789 7.88029 3.95451 7.66614 4.33301 7.66602ZM4.21875 11.0068C4.10075 11.16 3.96808 11.3014 3.82324 11.4287L3.67383 11.5518C3.62072 11.5927 3.56492 11.6294 3.50879 11.666C3.56491 11.7026 3.62073 11.7404 3.67383 11.7812L3.82324 11.9043C3.96786 12.0315 4.10089 12.1723 4.21875 12.3252C4.25945 12.378 4.29661 12.4335 4.33301 12.4893C4.36947 12.4334 4.4065 12.3781 4.44727 12.3252C4.60464 12.121 4.78824 11.9385 4.99219 11.7812L5.15625 11.666L4.99219 11.5518C4.78829 11.3945 4.6046 11.211 4.44727 11.0068C4.4066 10.954 4.3694 10.8986 4.33301 10.8428C4.29654 10.8987 4.25952 10.9539 4.21875 11.0068ZM10 0.333008C10.4133 0.333142 10.7839 0.588031 10.9326 0.973633L11.7188 3.0166C11.9248 3.55234 11.9724 3.65663 12.0283 3.73535C12.0931 3.82645 12.173 3.90613 12.2637 3.9707H12.2646C12.3433 4.02658 12.4467 4.07421 12.9824 4.28027L15.0254 5.06641C15.4114 5.21493 15.6659 5.58639 15.666 6C15.6659 6.41357 15.4114 6.78407 15.0254 6.93262L12.9824 7.71875C12.4466 7.92483 12.3433 7.97248 12.2646 8.02832H12.2637C12.1727 8.09306 12.0931 8.17268 12.0283 8.26367V8.26465C11.9725 8.34325 11.9248 8.44662 11.7188 8.98242L10.9326 11.0254C10.7841 11.4114 10.4136 11.6659 10 11.666C9.58639 11.6659 9.21493 11.4114 9.06641 11.0254L8.28027 8.98242C8.07415 8.44653 8.02658 8.34326 7.9707 8.26465V8.26367C7.90597 8.1728 7.82628 8.09298 7.73535 8.02832C7.65674 7.97249 7.5525 7.92487 7.0166 7.71875L4.97363 6.93262C4.58803 6.7839 4.33314 6.41333 4.33301 6C4.33314 5.58655 4.58785 5.21504 4.97363 5.06641L7.0166 4.28027C7.55318 4.07389 7.65667 4.02665 7.73535 3.9707L7.86328 3.86328C7.9026 3.82396 7.93827 3.78092 7.9707 3.73535C8.0267 3.65659 8.07394 3.5531 8.28027 3.0166L9.06641 0.973633L9.13184 0.835938C9.30793 0.528384 9.63797 0.333125 10 0.333008ZM9.99902 4.1123C9.88413 4.39956 9.76681 4.66078 9.60059 4.89453C9.40644 5.16746 9.16791 5.4062 8.89453 5.60059C8.6608 5.76681 8.39955 5.88413 8.1123 5.99902C8.39958 6.11391 8.66075 6.23222 8.89453 6.39844C9.16742 6.59249 9.40542 6.8317 9.59961 7.10449H9.60059C9.76658 7.33785 9.88431 7.59907 9.99902 7.88574C10.1138 7.59881 10.2323 7.33803 10.3984 7.10449C10.5927 6.83141 10.8314 6.59268 11.1045 6.39844C11.338 6.23232 11.5988 6.11382 11.8857 5.99902C11.5992 5.88435 11.3387 5.76644 11.1055 5.60059C10.832 5.40617 10.5926 5.16751 10.3984 4.89453C10.2322 4.66073 10.1139 4.39961 9.99902 4.1123ZM0.00976562 0.00976562H0V0H0.00976562V0.00976562Z" fill="#FE9A00"/>
                        </svg>
                        <span className="text-orange-500 font-medium">Alkam</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <Button variant="ghost" size="sm" className="h-8 gap-1 text-sm bg-secondary">
                            <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor">
                                <path d="M8 4v8M4 8h8" strokeWidth="2" strokeLinecap="round"/>
                            </svg>
                            New Chat
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 bg-secondary">
                            <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor">
                                <path d="M14 8a6 6 0 11-12 0 6 6 0 0112 0z" strokeWidth="1.5"/>
                                <path d="M8 4v4l2 2" strokeWidth="1.5" strokeLinecap="round"/>
                            </svg>
                        </Button>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={closeChat}
                            className="h-8 w-8 bg-secondary"
                        >
                            <X className="w-4 h-4" />
                        </Button>
                    </div>
                </div>

                {/* Main Content Container */}
                <div className="flex flex-col gap-4 p-6 flex-1 overflow-hidden">
                    {/* Reference Section */}
                    <div className="flex items-center gap-2">
                        <span className="text-sm">Ref:</span>
                            <Button
                                variant="outline"
                                className="px-[8px] py-[5.5px] gap-2 text-foreground border-border hover:bg-accent"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 14 14" fill="none">
                                    <path d="M4.75 8.66699C5.5324 8.66699 6.16699 9.30158 6.16699 10.084V12.084C6.16664 12.8661 5.53219 13.5 4.75 13.5H1.41699C0.634806 13.5 0.000351737 12.8661 0 12.084V10.084C0 9.30158 0.634589 8.66699 1.41699 8.66699H4.75ZM12.083 6C12.8654 6 13.5 6.63459 13.5 7.41699V12.083C13.5 12.8654 12.8654 13.5 12.083 13.5H8.75C7.96775 13.4998 7.33301 12.8653 7.33301 12.083V7.41699C7.33301 6.6347 7.96775 6.00018 8.75 6H12.083ZM1.5 12H4.66699V10.167H1.5V12ZM8.83301 12H12V7.5H8.83301V12ZM4.75 0C5.5324 1.28852e-07 6.16699 0.634589 6.16699 1.41699V6.08301C6.16699 6.86541 5.5324 7.5 4.75 7.5H1.41699C0.634589 7.5 0 6.86541 0 6.08301V1.41699C0 0.634589 0.634589 0 1.41699 0H4.75ZM1.5 6H4.66699V1.5H1.5V6ZM12.083 0C12.8654 1.28852e-07 13.5 0.634589 13.5 1.41699V3.41699C13.4998 4.19925 12.8653 4.83301 12.083 4.83301H8.75C7.96785 4.83283 7.33318 4.19914 7.33301 3.41699V1.41699C7.33301 0.634697 7.96775 0.000175814 8.75 0H12.083ZM8.83301 3.33301H12V1.5H8.83301V3.33301Z" fill="#020617"/>
                                </svg>
                                AICoE Health & AI
                            </Button>
                    </div>

                    {/* Chat Content Area */}
                    <div className="flex-1 flex flex-col w-[399px] justify-end overflow-y-auto bg-muted rounded-md">
                        <div className="flex flex-col items-end text-right mb-6">
                            <h3 className="text-sm font-semibold text-foreground mb-2">Quick suggestion to ask.</h3>
                            <p className="text-xs text-muted-foreground mb-4">You can pick can from below or ask anything in chat.</p>
                            
                            <div className="w-full space-y-2">
                                <Button 
                                    variant="outline" 
                                    className="w-auto justify-start text-sm h-auto py-2.5 px-3 text-left font-normal"
                                >
                                    How much budget utilised by each project
                                </Button>
                                <Button 
                                    variant="outline" 
                                    className="w-auto justify-start text-sm h-auto py-2.5 px-3 text-left font-normal"
                                >
                                    Projects having more than 5 MRL Metric
                                </Button>
                                <Button 
                                    variant="outline" 
                                    className="w-auto justify-start text-sm h-auto py-2.5 px-3 text-left font-normal"
                                >
                                    Summarise Goals and Impact of the CoE
                                </Button>
                            </div>
                        </div>
                    
                    </div>

                    {/* Input Area */}
                    <div className="relative">
                        <div className="relative rounded-lg p-[2px] bg-gradient-to-r from-orange-400 to-pink-400">
                            <div className="relative bg-white rounded-lg flex items-center gap-2 px-4 py-2.5">
                                <Plus className="w-4 h-4 text-orange-500 shrink-0" />
                                <input
                                    type="text"
                                    placeholder="Ask me about the project"
                                    className="flex-1 text-sm text-foreground placeholder:text-muted-foreground bg-transparent border-none outline-none focus:outline-none"
                                />
                                <svg className="w-5 h-5 text-orange-500 shrink-0" viewBox="0 0 20 20" fill="none">
                                    <path d="M3 10L17 10M17 10L11 4M17 10L11 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatPanel;
