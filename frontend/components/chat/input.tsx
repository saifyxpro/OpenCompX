"use client";

import React, { useMemo } from "react";
import { PromptBox } from "@/components/ui/prompt-box";
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
 * Modern chat input component using PromptBox
 */
export function ChatInput({
  input,
  setInput,
  onSubmit,
  isLoading,
  onStop,
  disabled = false,
  placeholder = "Ask the agent to do something...",
  image,
  setImage,
  selectedTool,
  setSelectedTool,
  className,
}: ChatInputProps & {
  image?: string | null;
  setImage?: (img: string | null) => void;
  selectedTool?: string | null;
  setSelectedTool?: (tool: string | null) => void;
}) {

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((!input.trim() && !image) || disabled || isLoading) return;
    onSubmit(e);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={cn("w-full", className)}>
      <PromptBox
        value={input}
        onChange={(e) => setInput(e.target.value)}
        image={image}
        onImageChange={setImage}
        selectedTool={selectedTool}
        onToolChange={setSelectedTool}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full"
      />
    </form>
  );
}
