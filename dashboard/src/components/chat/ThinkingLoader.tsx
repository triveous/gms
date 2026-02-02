import React from 'react';

const ThinkingLoader = () => (
    <div className="flex space-x-1 items-center h-5">
        <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
        <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
        <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
    </div>
);

export default ThinkingLoader;
