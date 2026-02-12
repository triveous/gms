import React from 'react';

/**
 * Formats text containing numbers with separate styling for numeric and text parts
 * Examples: "300 persons", "20 cities", "50% chance"
 * @param text - The text containing numbers and units
 * @returns JSX element with styled number and text parts
 */
export const formatTextWithNumber = (text: string): React.JSX.Element => {
    if (!text || typeof text !== 'string') {
        return <span className="text-muted-foreground">--</span>;
    }

    // Regular expression to match numbers (including decimals and percentages)
    const regex = /^([\d,.]+%?)\s*(.*)$/;
    const match = text.trim().match(regex);

    if (match) {
        const numberPart = match[1]; // e.g., "300", "50%", "1.5"
        const textPart = match[2];   // e.g., "persons", "cities", "chance"

        return (
            <div className="flex items-baseline gap-1">
                <span className="text-3xl font-semibold text-foreground">{numberPart}</span>
                {textPart && (
                    <span className="text-sm font-normal text-gray-500">{textPart}</span>
                )}
            </div>
        );
    }

    // If no number pattern found, return the original text
    return <span className="text-foreground">{text}</span>;
};
