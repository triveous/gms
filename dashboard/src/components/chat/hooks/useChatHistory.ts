import { useEffect } from 'react';
import { useFrappeGetCall } from 'frappe-react-sdk';


interface UseChatHistoryProps {
    threadId: string;
    isHistoryRequested: boolean;
    setMessages: (messages: any[]) => void;
    onHistoryLoaded: () => void;
}

export const useChatHistory = ({
    threadId,
    isHistoryRequested,
    setMessages,
    onHistoryLoaded
}: UseChatHistoryProps) => {
    const { data: conversationHistoryData, isLoading, error } = useFrappeGetCall(
        'gms.api.ai.history',
        { thread_id: threadId },
        (threadId && isHistoryRequested) ? undefined : null
    );

    useEffect(() => {
        if (conversationHistoryData?.message) {
            const transformedMessages = conversationHistoryData.message
                .map((msg: { id: string; role: 'user' | 'assistant'; parts: Record<string, unknown>[] }) => {
                    const sortedParts = msg.parts ? [...msg.parts].sort((a: any, b: any) => {
                        const isTextA = a.type === 'text';
                        const isTextB = b.type === 'text';
                        if (isTextA && !isTextB) return 1;
                        if (!isTextA && isTextB) return -1;
                        return 0;
                    }) : [];

                    return {
                        id: msg.id,
                        role: msg.role,
                        parts: sortedParts,
                        content: '' // SDK expects content, we use parts mostly
                    };
                })
                .filter((msg: { id: string; role: string; parts: Record<string, unknown>[] }) => {
                    if (msg.role === 'user') return true;
                    // Keep text or data-block parts
                    return msg.parts?.some((p) => p['type'] === 'text' || p['type'] === 'data-block' || p['type'] === 'data-task');
                });

            // Cast to any to bypass strict AI SDK message type checks if necessary, 
            // but ideally we confirm to Message type.
            // The SDK Message type has complex content structure. 
            // Here we assume setMessages can handle what we pass or we match it.
            setMessages(transformedMessages as any);
            onHistoryLoaded();
        }
    }, [conversationHistoryData, setMessages, onHistoryLoaded]);

    return { isLoading, error };
};
