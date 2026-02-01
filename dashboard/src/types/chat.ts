export interface SDKMessage {
    id: string;
    role: 'user' | 'assistant' | 'system' | 'data';
    content?: string;
    parts?: { type: string; data?: unknown; text?: string }[];
}

export interface QuickQuestion {
    name: string;
    question: string;
    creation: string;
}

export interface Conversation {
    name: string;
    title: string;
}
