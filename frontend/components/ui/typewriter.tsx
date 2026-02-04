"use client";

import { useEffect, useState } from "react";

interface TypewriterProps {
    content: string;
    speed?: number;
    onComplete?: () => void;
    className?: string;
    children: (displayedContent: string) => React.ReactNode;
}

export function Typewriter({
    content,
    speed = 10,
    onComplete,
    className,
    children,
}: TypewriterProps) {
    const [displayedContent, setDisplayedContent] = useState("");
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        // If content resets or changes drastically, we might want to reset or just jump to end.
        // For now, let's assume valid streaming appends.

        // If we've already displayed everything, do nothing.
        if (currentIndex >= content.length) {
            if (onComplete) onComplete();
            return;
        }

        const timeout = setTimeout(() => {
            // Calculate how many characters to add. 
            // For very fast streaming, we might want to add chunks.
            const chunk = content.slice(currentIndex, currentIndex + 2);
            setDisplayedContent((prev) => prev + chunk);
            setCurrentIndex((prev) => prev + 2);
        }, speed);

        return () => clearTimeout(timeout);
    }, [content, currentIndex, speed, onComplete]);

    // If content shrinks (e.g. clear chat), reset
    useEffect(() => {
        if (content.length < displayedContent.length) {
            setDisplayedContent("");
            setCurrentIndex(0);
        }
    }, [content]);

    return <div className={className}>{children(displayedContent)}</div>;
}
