"use client";

import React, { useState } from "react";
import {
  ChatMessage as ChatMessageType,
  ActionChatMessage,
} from "@/types/chat";
import { cn } from "@/lib/utils";
import {
  Terminal,
  Clock,
  User,
  Bot,
  ChevronDown,
  ChevronUp,
  Cpu,
  MousePointer2,
  Keyboard,
  AppWindow,
  Copy,
  Check,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Markdown as MemoizedReactMarkdown } from "@/components/markdown";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

// Helper to parse pyautogui actions into human-readable text
const parseAction = (code: string) => {
  if (!code) return { title: "Executing Action", icon: Cpu };

  if (code.includes("write") || code.includes("type")) {
    const match = code.match(/write\(['"](.+?)['"]\)/);
    return {
      title: match ? `Typing "${match[1].slice(0, 30)}${match[1].length > 30 ? '...' : ''}"` : "Typing text...",
      icon: Keyboard
    };
  }
  if (code.includes("click")) {
    return { title: "Clicking element", icon: MousePointer2 };
  }
  if (code.includes("launch")) {
    const match = code.match(/launch\(['"](.+?)['"]\)/);
    return {
      title: match ? `Opening ${match[1]}` : "Opening application...",
      icon: AppWindow
    };
  }
  if (code.includes("open_url") || code.includes("open(")) {
    const match = code.match(/open(?:_url)?\(['"](.+?)['"]\)/);
    return {
      title: match ? `Opening ${new URL(match[1]).hostname}` : "Opening URL...",
      icon: AppWindow
    };
  }
  if (code.includes("scroll")) return { title: "Scrolling...", icon: MousePointer2 };
  if (code.includes("wait")) return { title: "Waiting...", icon: Clock };
  if (code.includes("hotkey")) return { title: "Keyboard shortcut", icon: Keyboard };
  if (code.includes("drag")) return { title: "Dragging element", icon: MousePointer2 };

  return { title: "Running command", icon: Terminal };
};

// Helper to check if content is raw code that should be hidden
const isRawCode = (content: string): boolean => {
  if (!content) return false;
  const codePatterns = [
    /^pyautogui\./,
    /^import\s+/,
    /^\s*#/,
    /\.open\(/,
    /\.click\(/,
    /\.write\(/,
    /\.launch\(/,
    /\.hotkey\(/,
    /\.scroll\(/,
    /\.moveTo\(/,
    /\.dragRel\(/,
    /```python/,
  ];
  return codePatterns.some(pattern => pattern.test(content.trim()));
};

interface ActionMessageProps {
  message: ActionChatMessage;
  className?: string;
}

function ActionMessage({ message, className }: ActionMessageProps) {
  const { action, status } = message;
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const codeString = typeof action === 'string'
    ? action
    : (action as any)?.code || JSON.stringify(action, null, 2);

  const { title, icon: Icon } = parseAction(codeString);

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isPending = status === "pending";
  const isCompleted = status === "completed";
  const isFailed = status === "failed";

  return (
    <div className={cn("w-full pl-11 pr-4", className)}>
      <div className={cn(
        "rounded-lg overflow-hidden transition-all border",
        isPending && "border-amber-200/50 bg-amber-50/50",
        isCompleted && "border-emerald-200/50 bg-emerald-50/50",
        isFailed && "border-red-200/50 bg-red-50/50",
        !isPending && !isCompleted && !isFailed && "border-slate-200/60 bg-slate-50/50 hover:bg-slate-100/80"
      )}>
        {/* Action Header */}
        <div className="flex items-center justify-between px-3 py-2">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-6 h-6 rounded flex items-center justify-center shadow-sm",
              isPending && "bg-amber-100 text-amber-600",
              isCompleted && "bg-emerald-100 text-emerald-600",
              isFailed && "bg-red-100 text-red-600",
              !isPending && !isCompleted && !isFailed && "bg-white border border-slate-200 text-slate-500"
            )}>
              <Icon className="w-3.5 h-3.5" />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-700 font-mono">{title}</span>
              {isPending && (
                <span className="text-[10px] uppercase tracking-wider font-bold text-amber-600 flex items-center gap-1 bg-amber-100/50 px-1.5 py-0.5 rounded">
                  Running
                </span>
              )}
            </div>
          </div>

          <Collapsible open={isOpen} onOpenChange={setIsOpen}>
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 text-slate-400 hover:text-slate-600"
              >
                {isOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              </Button>
            </CollapsibleTrigger>
          </Collapsible>
        </div>

        {/* Code Expandable */}
        <Collapsible open={isOpen}>
          <CollapsibleContent>
            <div className="px-3 pb-3">
              <div className="relative bg-slate-900 rounded-[6px] p-3 group border border-slate-800 shadow-inner">
                <Button
                  size="icon"
                  variant="ghost"
                  className="absolute right-2 top-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-slate-500 hover:text-slate-300 hover:bg-slate-800"
                  onClick={handleCopy}
                >
                  {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                </Button>
                <pre className="text-[11px] leading-relaxed text-slate-300 font-mono overflow-x-auto whitespace-pre-wrap">
                  {codeString}
                </pre>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>
    </div>
  );
}

interface ChatMessageProps {
  message: ChatMessageType;
  className?: string;
}

export function ChatMessage({ message, className }: ChatMessageProps) {
  const role = message.role;
  const isUser = role === "user";
  const isAssistant = role === "assistant";
  const isAction = role === "action";
  const isSystem = role === "system";
  const isError = "isError" in message && message.isError;

  // System messages
  if (isSystem) {
    return (
      <div className={cn("flex justify-center py-3", className)}>
        <Badge
          variant={isError ? "error" : "muted"}
          className={cn(
            "px-3 py-1 text-xs font-medium",
            isError ? "bg-red-100 text-red-700 border-red-200" : "bg-slate-100 text-slate-600 border-slate-200"
          )}
        >
          {message.content}
        </Badge>
      </div>
    );
  }

  // Action messages
  if (isAction) {
    return <ActionMessage message={message as ActionChatMessage} className={className} />;
  }

  // User messages
  if (isUser) {
    return (
      <div className={cn("flex justify-end group", className)}>
        <div className="flex items-start gap-3 max-w-full">
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white px-5 py-3.5 rounded-2xl rounded-tr-sm shadow-md min-w-0 max-w-[calc(100%-3rem)] ring-1 ring-blue-700/50">
            <p className="text-sm leading-relaxed break-words font-medium">{message.content}</p>
          </div>
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100/50 flex items-center justify-center ring-2 ring-white shadow-sm">
            <User className="w-4 h-4 text-blue-700" />
          </div>
        </div>
      </div>
    );
  }

  // Assistant messages - filter out raw code
  if (isAssistant) {
    // Skip rendering if content is raw pyautogui code
    if (isRawCode(message.content)) {
      return null;
    }

    return (
      <div className={cn("flex justify-start group", className)}>
        <div className="flex items-start gap-3 max-w-full">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center ring-2 ring-white shadow-md">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div className="bg-white/90 backdrop-blur-sm border border-slate-200/60 px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm min-w-0 max-w-[calc(100%-3rem)] hover:shadow-md transition-all duration-300">
            <div className="text-sm text-slate-700 prose prose-sm prose-slate max-w-none overflow-hidden break-words prose-p:leading-relaxed prose-pre:bg-slate-900 prose-pre:text-slate-50">
              <MemoizedReactMarkdown>
                {(() => {
                  try {
                    // Try to parse content as JSON to extract natural language reflection
                    const parsed = JSON.parse(message.content);
                    if (typeof parsed === 'object' && parsed !== null) {
                      // Prefer reflection, then thoughts, then plan
                      const naturalText = parsed.reflection || parsed.thoughts || parsed.reflection_thoughts || parsed.plan;
                      if (naturalText) return naturalText;
                    }
                    return message.content;
                  } catch (e) {
                    // Not JSON, return original content
                    return message.content;
                  }
                })()}
              </MemoizedReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
