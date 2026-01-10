import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
    content: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
    return (
        <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:font-semibold prose-a:text-blue-600 prose-code:text-sm prose-pre:bg-muted">
            <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                    // Custom table styling to override prose defaults
                    table: ({ ...props }) => (
                        <div className="overflow-x-auto my-4">
                            <table className="min-w-full border-collapse rounded-lg overflow-hidden" {...props} />
                        </div>
                    ),
                    thead: ({ ...props }) => (
                        <thead className="bg-[#E2E8F0]" {...props} />
                    ),
                    th: ({ ...props }) => (
                        <th className="px-6 py-4 text-left font-medium text-foreground border border-[#F2F2F2]" {...props} />
                    ),
                    td: ({ ...props }) => (
                        <td className="px-6 py-4 bg-white border border-[#F2F2F2]" {...props} />
                    ),
                    tr: ({ ...props }) => (
                        <tr {...props} />
                    ),
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
};

export default MarkdownRenderer;
