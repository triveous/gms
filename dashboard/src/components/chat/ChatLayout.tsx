import React from 'react';
import {
    Conversation,
    ConversationContent,
    ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import { Message, MessageContent } from '@/components/ai-elements/message';
import { type PromptInputMessage } from '@/components/ai-elements/prompt-input';
import ChatMessageItem from './ChatMessageItem';
import type { SDKMessage, Conversation as ConversationType } from '@/types/chat';
import BeforeThinkingLoader from './BeforeThinkingLoader';
import ChainOfThoughtComponent from './ChainofThought';
import type { QuickQuestion } from '@/types/chat';
import QuickQuestions from './QuickQuestions';
import ChatHeader from './ChatHeader';
import ChatInputArea from './ChatInputArea';
import { toast } from 'sonner';
import { ReviewDialog } from './ReviewDialog';

/** Deeply find a value by key in a nested object structure (handles backend nesting variations) */
const findDeep = (obj: any, key: string): any => {
    if (!obj || typeof obj !== 'object') return undefined;
    if (obj[key] !== undefined && obj[key] !== null) return obj[key];
    for (const k in obj) {
        if (obj[k] && typeof obj[k] === 'object') {
            const found = findDeep(obj[k], key);
            if (found !== undefined) return found;
        }
    }
    return undefined;
};

/** Map backend task status strings to progress step numbers */
const statusToStep = (backendStatus: string): number => {
    console.log("backendStatus", backendStatus)
    switch (backendStatus?.toLowerCase()) {
        case 'extracting': return 2;
        case 'validating': return 3;
        case 'reviewing': return 4;
        case 'approved': return 6;
        case 'rejected': return 4;
        default: return 0;
    }
};



const getInitialUploadStep = (parts: any[]): any => {
    const taskPart = parts.find((p: any) => p.type === 'data-task');
    if (!taskPart) return null;

    const data = taskPart.data || {};

    const status = (data.status || '').toLowerCase();
    if (status === 'submitting' || !status) return 0;

    const step = statusToStep(status);
    return step;
};

const getInitialReviewData = (parts: any[]): any => {
    const taskPart = parts.find((p: any) => p.type === 'data-task');
    if (!taskPart) return null;

    const data = taskPart.data || {};
    const llm_response = data.llm_response;

    if (llm_response) {
        return {
            ...llm_response,
            task_id: data?.task,
            file_id: data?.file,
            filename: data?.filename
        };
    }
    return null;
};



interface ChatLayoutProps {
    onNewChat: () => void;
    onClose: () => void;
    conversationList: ConversationType[];
    onSelectConversation: (id: string) => void;
    threadId: string;

    messages: SDKMessage[];
    status: 'error' | 'submitted' | 'streaming' | 'ready';
    error: any;

    quickQuestions: QuickQuestion[];
    handleSend: (message: PromptInputMessage) => void;

    input: string;
    setInput: React.Dispatch<React.SetStateAction<string>>;

    isAssistantResponding: boolean;
    hasTextPart: boolean;
    showBeforeThinking: boolean;
    showThinkingActive: boolean;
    hasDataBlockPart: boolean;

    isDrawerMode?: boolean;
}

const ChatLayout: React.FC<ChatLayoutProps> = ({
    onNewChat,
    onClose,
    conversationList,
    onSelectConversation,
    threadId,
    messages,
    status,
    error,
    quickQuestions,
    handleSend,
    input,
    setInput,
    isAssistantResponding,
    hasTextPart,
    showBeforeThinking,
    showThinkingActive,
    hasDataBlockPart,
    isDrawerMode = false,
}) => {
    const [taskStates, setTaskStates] = React.useState<Record<string, { uploadStep: number; reviewData: any; isSubmitting: boolean; isRejected: boolean; errorStep: number | null; errorMessage: string | null }>>({});
    const [reviewDialogState, setReviewDialogState] = React.useState<{ open: boolean; type: 'progress' | 'plan' | 'dpr'; activeMessageId: string | null }>({
        open: false,
        type: 'progress',
        activeMessageId: null
    });

    const updateTaskState = (messageId: string, updates: Partial<{ uploadStep: number; reviewData: any; isSubmitting: boolean; isRejected: boolean; errorStep: number | null; errorMessage: string | null }>) => {
        setTaskStates(prev => ({
            ...prev,
            [messageId]: {
                ...(prev[messageId] || { uploadStep: 0, reviewData: null, isSubmitting: false, isRejected: false, errorStep: null, errorMessage: null }),
                ...updates
            }
        }));
    };

    // Initialize/Sync task states from messages
    React.useEffect(() => {
        const newStates = { ...taskStates };
        let hasChanges = false;

        messages.forEach(msg => {

            if (msg.role !== 'assistant') return;
            if (newStates[msg.id]) return;

            const parts = msg.parts || (msg.content ? [{ type: 'text', text: msg.content }] : []);

            // Try to find if this message has a task
            const hasTask = parts.find((p: any) => p.type === 'data-task');

            if (hasTask) {
                const initialStep = getInitialUploadStep(parts);
                const taskData = hasTask.data || {};
                const isError = findDeep(taskData, 'isError') === true;
                const errorMessage = findDeep(taskData, 'errorMessage');

                newStates[msg.id] = {
                    uploadStep: initialStep,
                    reviewData: getInitialReviewData(parts),
                    isSubmitting: false,
                    isRejected: false,
                    errorStep: isError ? initialStep : null,
                    errorMessage: isError ? errorMessage : (hasTask?.data?.errorMessage || null)
                };
                hasChanges = true;
            }
        });

        if (hasChanges) {
            setTaskStates(newStates);
        }
    }, [messages]);

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>, taskId: string, messageId: string) => {
        const file = event.target.files?.[0];
        if (!file) return;

        updateTaskState(messageId, { uploadStep: 1 });
        const formData = new FormData();
        formData.append('file', file);
        formData.append('thread_id', threadId);
        formData.append('task_id', taskId);

        try {
            const response = await fetch('/api/method/gms.api.submit_file.resume_with_file', {
                method: 'POST',
                headers: {
                    'X-Frappe-CSRF-Token': (window as any).csrf_token
                },
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Upload failed');
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            if (reader) {
                updateTaskState(messageId, { uploadStep: 2 });
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        const trimmedLine = line.trim();
                        if (trimmedLine.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(trimmedLine.slice(6));
                                if (data.type === 'data-task') {
                                    const taskData = data;
                                    const statusStr = (findDeep(taskData, 'status') || '').toLowerCase();
                                    const step = statusToStep(statusStr);

                                    const isError = findDeep(taskData, 'isError') === true;
                                    const errorMessage = findDeep(taskData, 'errorMessage');

                                    // Always update step, even if it's 0 (allows resetting to upload prompt on rejection)
                                    updateTaskState(messageId, {
                                        uploadStep: step,
                                        isRejected: statusStr === 'rejected',
                                        errorStep: isError ? step : null,
                                        errorMessage: isError ? errorMessage : null
                                    });

                                    // Deep search for llm_response and metadata
                                    const llm_response = findDeep(taskData, 'llm_response');
                                    if (llm_response && Object.keys(llm_response).length > 0) {
                                        updateTaskState(messageId, {
                                            reviewData: {
                                                ...llm_response,
                                                file_id: findDeep(taskData, 'file_id'),
                                                filename: findDeep(taskData, 'filename'),
                                                task_id: taskData?.id
                                            },
                                            uploadStep: 4
                                        });
                                    }
                                } else if (data.type === 'data-resume-data' || data.type === 'resume-data') {
                                    const resumeData = data;
                                    updateTaskState(messageId, { reviewData: resumeData, uploadStep: 4 });
                                } else if (data.type === 'data-submit-result') {
                                    if (data?.status === 'submitted') {
                                        toast.success('Submitted successfully');
                                        updateTaskState(messageId, { uploadStep: 6 });
                                        setReviewDialogState(prev => ({ ...prev, open: false }));
                                    } else if (data?.status === 'rejected') {
                                        toast.info(data?.message || 'Submission discarded');
                                        updateTaskState(messageId, { uploadStep: 0, isRejected: true });
                                        setReviewDialogState(prev => ({ ...prev, open: false }));
                                    }
                                }
                            } catch (e) { }
                        }
                    }
                }
            }
        } catch (error: any) {
            console.error('File upload error:', error);
            toast.error(error.message || 'Failed to upload file');
            updateTaskState(messageId, { uploadStep: 0 });
        }
    };

    const handleReviewSubmit = async (messageId: string, isSubmit: boolean = true) => {
        const state = taskStates[messageId];
        if (!state?.reviewData) {
            toast.error('No data to submit');
            return;
        }

        updateTaskState(messageId, { isSubmitting: true, uploadStep: isSubmit ? 5 : 4, isRejected: false });

        try {
            console.log("state.reviewData", state);
            const formData = new FormData();
            formData.append('submit', isSubmit.toString());
            formData.append('file_id', state.reviewData.file_id || '');
            formData.append('extracted_data', JSON.stringify(state.reviewData));
            formData.append('thread_id', threadId);
            formData.append('task_id', state.reviewData.task_id || '');

            const response = await fetch('/api/method/gms.api.submit_file.submit_extracted_milestone', {
                method: 'POST',
                headers: {
                    'X-Frappe-CSRF-Token': (window as any).csrf_token
                },
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Submission failed');
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            if (reader) {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        const trimmedLine = line.trim();
                        if (trimmedLine.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(trimmedLine.slice(6));
                                if (data.type === 'data-task') {
                                    if (data?.status === 'approved') {
                                        updateTaskState(messageId, { uploadStep: 6, isRejected: false });
                                    }
                                } else if (data.type === 'data-submit-result') {
                                    if (data?.data?.status === 'submitted') {
                                        updateTaskState(messageId, { uploadStep: 6, isRejected: false });
                                        setReviewDialogState(prev => ({ ...prev, open: false }));
                                    } else if (data?.data?.status === 'rejected') {
                                        updateTaskState(messageId, { uploadStep: 4, isRejected: true });
                                        setReviewDialogState(prev => ({ ...prev, open: false }));
                                    }
                                }
                            } catch (e) { }
                        }
                    }
                }
            }
        } catch (error: any) {
            console.error('Submission error:', error);
            toast.error(error.message || 'Failed to submit data');
            updateTaskState(messageId, { uploadStep: 4 });
        } finally {
            updateTaskState(messageId, { isSubmitting: false });
        }
    };
    const containerWidthClass = isDrawerMode
        ? 'w-[399px] max-w-[399px]'
        : 'w-full';

    return (
        <div className="flex flex-col h-full">
            <ChatHeader
                onNewChat={onNewChat}
                onClose={onClose}
                conversationList={conversationList}
                onSelectConversation={onSelectConversation}
            />

            <div className="flex flex-col gap-4 p-6 pt-0 flex-1 overflow-hidden">

                <Conversation className={`relative flex-1 min-h-0 ${containerWidthClass}`}>
                    <ConversationContent
                        className={`h-full ${containerWidthClass} flex flex-col-reverse overflow-y-auto bg-[#F8FAFC] rounded-md p-4 remove-scrollbar`}
                    >
                        {(status === 'error' || error) && (
                            <div className="flex w-full justify-center py-2">
                                <span className="text-sm text-red-500">
                                    Oops! Something went wrong. Please try again.
                                </span>
                            </div>
                        )}

                        {showBeforeThinking && (
                            <Message from="assistant">
                                <MessageContent className="rounded-tl-none p-1">
                                    <BeforeThinkingLoader />
                                </MessageContent>
                            </Message>
                        )}

                        {showThinkingActive && !hasDataBlockPart && (
                            <Message from="assistant">
                                <MessageContent className="rounded-tl-none p-1">
                                    <ChainOfThoughtComponent
                                        open={true}
                                        data={[]}
                                        status={status}
                                    />
                                </MessageContent>
                            </Message>
                        )}

                        {messages.length === 0 ? (
                            <QuickQuestions
                                questions={quickQuestions}
                                onQuestionClick={(text) =>
                                    handleSend({ text, files: [] })
                                }
                                disabled={status !== 'ready'}
                            />
                        ) : (
                            [...messages].reverse().map((message) => {
                                const lastMessage = messages[messages.length - 1];
                                const isLastMessage = message.id === lastMessage?.id;
                                const isAssistant = message.role === 'assistant';
                                const messageStatus =
                                    isLastMessage && isAssistant ? status : 'ready';

                                return (
                                    <ChatMessageItem
                                        key={message.id}
                                        message={message}
                                        status={messageStatus}
                                        isLast={isLastMessage && isAssistant}
                                        // threadId={threadId}
                                        taskState={taskStates[message.id] || { uploadStep: 0, reviewData: null, isSubmitting: false, isRejected: false }}
                                        onFileChange={(e, taskId) => handleFileChange(e, taskId, message.id)}
                                        onOpenReview={(type) => setReviewDialogState({ open: true, type, activeMessageId: message.id })}
                                    />
                                );
                            })
                        )}
                    </ConversationContent>

                    <ConversationScrollButton />

                    <div className="absolute top-0 left-0 right-0 h-10 bg-gradient-to-b from-[#F8FAFC] to-transparent pointer-events-none rounded-t-md z-10" />
                </Conversation>

                <ChatInputArea
                    input={input}
                    setInput={setInput}
                    onSend={handleSend}
                    status={status}
                    disabled={
                        (status !== 'ready' && status !== 'error')
                    }
                    isAssistantResponding={isAssistantResponding}
                    hasTextPart={hasTextPart}
                    showBeforeThinking={showBeforeThinking}
                    showThinkingActive={showThinkingActive}
                />
            </div>
            <ReviewDialog
                open={reviewDialogState.open}
                onOpenChange={(open) => setReviewDialogState(prev => ({ ...prev, open }))}
                type={reviewDialogState.type}
                data={reviewDialogState.activeMessageId ? taskStates[reviewDialogState.activeMessageId]?.reviewData : null}
                onSubmit={async () => {
                    if (reviewDialogState.activeMessageId) {
                        await handleReviewSubmit(reviewDialogState.activeMessageId, true);
                    }
                }}
                onCancel={async () => {
                    if (reviewDialogState.activeMessageId) {
                        await handleReviewSubmit(reviewDialogState.activeMessageId, false);
                    }
                }}
                isSubmitting={reviewDialogState.activeMessageId ? taskStates[reviewDialogState.activeMessageId]?.isSubmitting : false}
            />
        </div>
    );
};

export default ChatLayout;


