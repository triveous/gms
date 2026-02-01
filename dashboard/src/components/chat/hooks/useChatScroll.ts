import { useEffect, type RefObject } from 'react';

export const useChatScroll = (
    ref: RefObject<any>,
    dependencies: any[]
) => {
    useEffect(() => {
        if (ref.current) {
            ref.current.scrollTop = 0;
        }
    }, dependencies);
};
