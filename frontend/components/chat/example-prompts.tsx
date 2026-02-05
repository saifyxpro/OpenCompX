"use client";

import React from "react";
import { Code, FileEdit, Globe, Table } from "lucide-react";
import { cn } from "@/lib/utils";

interface ExamplePromptProps {
  icon: React.ReactNode;
  text: string;
  onClick: () => void;
  disabled?: boolean;
}

/**
 * Individual example prompt card
 */
function ExamplePromptCard({ icon, text, onClick, disabled }: ExamplePromptProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "flex items-center gap-3 px-4 py-3 w-full",
        "bg-white border border-slate-200 rounded-xl",
        "text-left text-sm text-slate-700",
        "hover:border-blue-300 hover:bg-blue-50/50 hover:text-slate-900",
        "focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500",
        "transition-all duration-200",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-slate-200"
      )}
    >
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-500">
        {icon}
      </div>
      <span className="font-medium">{text}</span>
    </button>
  );
}

interface ExamplePromptsProps {
  onPromptClick: (prompt: string) => void;
  prompts?: Array<{ text: string; prompt: string; icon: React.ReactNode }>;
  disabled?: boolean;
  className?: string;
}

/**
 * Example prompts grid
 */
export function ExamplePrompts({
  onPromptClick,
  prompts,
  disabled = false,
  className,
}: ExamplePromptsProps) {
  const defaultPrompts = [
    {
      icon: <Code className="w-4 h-4" />,
      text: "Create a JavaScript script",
      prompt: "Create a simple JavaScript script that calculates the Fibonacci sequence and save it to a file",
    },
    {
      icon: <FileEdit className="w-4 h-4" />,
      text: "Edit a document in VS Code",
      prompt: "Open VS Code and create a simple React component that displays a counter",
    },
    {
      icon: <Globe className="w-4 h-4" />,
      text: "Browse GitHub",
      prompt: "Open Firefox and go to GitHub to search for popular machine learning repositories",
    },
    {
      icon: <Table className="w-4 h-4" />,
      text: "Create a spreadsheet",
      prompt: "Open LibreOffice Calc and create a simple budget spreadsheet with formulas",
    },
  ];

  const items = prompts || defaultPrompts;

  return (
    <div className={cn("flex flex-col gap-4 w-full max-w-md mx-auto", className)}>
      <div className="text-center">
        <p className="text-sm font-medium text-slate-500">Try an example</p>
      </div>
      
      <div className="grid gap-2">
        {items.map((item, index) => (
          <ExamplePromptCard
            key={index}
            icon={item.icon}
            text={item.text}
            onClick={() => onPromptClick(item.prompt)}
            disabled={disabled}
          />
        ))}
      </div>
    </div>
  );
}
