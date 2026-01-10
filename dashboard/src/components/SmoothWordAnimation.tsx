import { motion, type Variants } from 'framer-motion';
import { useEffect, useMemo, useState, useRef } from 'react';
import MarkdownRenderer from './MarkdownRenderer';


const chunkText = (text: string, min = 2, max = 5) => {
  if (!text) return [];
  const words = text.split(' ');
  const chunks: string[] = [];

  let i = 0;
  while (i < words.length) {
    const size = Math.floor(Math.random() * (max - min + 1)) + min;
    chunks.push(words.slice(i, i + size).join(' '));
    i += size;
  }

  return chunks;
};


const wordVariants: Variants = {
  hidden: { opacity: 0, y: 4 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.18, ease: [0.22, 1, 0.36, 1] } 
  },
};

interface SmoothWordAnimationProps {
  text: string;
  useMarkdown?: boolean;
}

const SmoothWordAnimation: React.FC<SmoothWordAnimationProps> = ({ text, useMarkdown = false }) => {
  const [visibleCount, setVisibleCount] = useState(0);
  const animationRef = useRef<number>();

  // Memoize chunks to keep them stable
  const chunks = useMemo(() => chunkText(text), [text]);

  useEffect(() => {
    // Reset when chunks change (new message)
    setVisibleCount(0);
    
    // If text is very short, explain it instantly, otherwise animate
    if (chunks.length === 0) return;

    let currentIndex = 0;

    const animate = () => {
        // Calculate delay based on punctuation/content (simple version)
        const currentChunk = chunks[currentIndex];
        const isPunctuation = /[.!?]$/.test(currentChunk || '');
        const delay = isPunctuation ? 30 : 15; // Faster base speed

        const timeoutId = setTimeout(() => {
            currentIndex++;
            setVisibleCount(currentIndex);

            if (currentIndex < chunks.length) {
                animate();
            }
        }, delay);
        
         animationRef.current = timeoutId as unknown as number;
    };

    animate();

    return () => {
        if (animationRef.current) clearTimeout(animationRef.current);
    };
  }, [chunks]);

  // Derived state: Safe and deterministic!
  const visibleText = chunks.slice(0, visibleCount).join(' ');

  if (useMarkdown) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <MarkdownRenderer content={visibleText} />
      </motion.div>
    );
  }

  return (
    <p className="flex flex-wrap leading-relaxed">
      {chunks.slice(0, visibleCount).map((chunk, i) => (
        <motion.span
          key={`${i}-${chunk}`}
          variants={wordVariants}
          initial="hidden"
          animate="visible"
          className="mr-1.5 inline-block"
        >
          {chunk}
        </motion.span>
      ))}
    </p>
  );
};

export default SmoothWordAnimation;
