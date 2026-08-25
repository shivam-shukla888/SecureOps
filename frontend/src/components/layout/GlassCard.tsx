import React from 'react';
import { motion } from 'framer-motion';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: 'cyan' | 'emerald' | 'rose' | 'none';
  onClick?: () => void;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  glow = 'none',
  onClick,
}) => {
  const glowStyles = {
    cyan: 'shadow-glow-cyan border-cyan-500/30',
    emerald: 'shadow-glow-emerald border-emerald-500/30',
    rose: 'shadow-glow-rose border-rose-500/30',
    none: 'border-slate-800/80',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      onClick={onClick}
      className={`bg-[#111827]/80 backdrop-blur-md rounded-xl border ${glowStyles[glow]} p-5 transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:border-cyan-500/50 hover:bg-[#161e31]/90' : ''
      } ${className}`}
    >
      {children}
    </motion.div>
  );
};
