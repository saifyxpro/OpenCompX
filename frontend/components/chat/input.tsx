"use client";

import React, { useMemo } from "react";
import { Send, StopCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  input: string;
  setInput: (input: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  onStop: () => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

/**
 * Modern chat input component
 */
export function ChatInput({
  input,
  setInput,
  onSubmit,
  isLoading,
  onStop,
  disabled = false,
  placeholder = "Ask the agent to do something...",
  className,
}: ChatInputProps) {
  const isInputEmpty = useMemo(() => input.trim() === "", [input]);

  return (
    <form onSubmit={onSubmit} className={cn(className)}>
      <div className="relative">
        <input
          type="text"
          placeholder={placeholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          autoFocus
          disabled={disabled}
          className={cn(
            "w-full h-12 px-4 pr-14",
            "bg-white border border-slate-200 rounded-xl",
            "text-sm text-slate-900 placeholder:text-slate-400",
            "focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500",
            "transition-all duration-200",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        />
        
        <div className="absolute right-2 top-1/2 -translate-y-1/2">
          {isLoading ? (
            <Button
              type="button"
              onClick={onStop}
              size="icon"
              className="h-8 w-8 bg-red-500 hover:bg-red-600 text-white rounded-lg"
              disabled={disabled}
              title="Stop generating"
            >
              <StopCircle className="w-4 h-4" />
            </Button>
          ) : (
            <Button
              type="submit"
              size="icon"
              className={cn(
                "h-8 w-8 rounded-lg transition-all",
                isInputEmpty 
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed" 
                  : "bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
              )}
              disabled={disabled || isInputEmpty}
              title="Send message"
            >
              <Send className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    </form>
  );
}
