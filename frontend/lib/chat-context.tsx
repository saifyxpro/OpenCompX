"use client";

import React, {
  createContext,
  useContext,
  useState,
  useRef,
  useCallback,
} from "react";
import {
  ChatMessage,
  ChatState,
  ParsedSSEEvent,
  SendMessageOptions,
  ActionChatMessage,
  UserChatMessage,
  AssistantChatMessage,
  SystemChatMessage,
} from "@/types/chat";
import { ComputerModel, SSEEventType } from "@/types/api";
import { logDebug, logError } from "./logger";

interface ChatContextType extends ChatState {
  sendMessage: (options: SendMessageOptions) => Promise<void>;
  stopGeneration: () => void;
  clearMessages: () => void;
  setInput: (input: string) => void;
  input: string;
  handleSubmit: (e: React.FormEvent) => string | undefined;
  onSandboxCreated: (
    callback: (sandboxId: string, vncUrl: string) => void
  ) => void;
  model: ComputerModel;
  setModel: (model: ComputerModel) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

interface ChatProviderProps {
  children: React.ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const abortControllerRef = useRef<AbortController | null>(null);
  const onSandboxCreatedRef = useRef<
    ((sandboxId: string, vncUrl: string) => void) | undefined
  >(undefined);
  const [model, setModel] = useState<ComputerModel>("openai");

  const parseSSEEvent = (data: string): ParsedSSEEvent<typeof model> | null => {
    try {
      if (!data || data.trim() === "") {
        return null;
      }

      let eventType: string | null = null;
      let cleanData = data;

      // Parse lines to find 'event:' and 'data:'
      if (data.includes("\n")) {
        const lines = data.split("\n");
        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventType = line.substring(6).trim();
          } else if (line.startsWith("data:")) {
            cleanData = line.substring(5).trim();
          }
        }
      } else if (data.startsWith("data: ")) {
        cleanData = data.substring(6).trim();
      }

      if (!cleanData) {
        return null;
      }

      // Try parsing as JSON
      try {
        const parsed = JSON.parse(cleanData);

        // If we found an event type header, force it onto the object
        // This handles cases like "event: sandbox_created" where the data doesn't contain the type
        if (eventType) {
          // Map backend event names to frontend enum if needed, or assume match
          // Backend sends: sandbox_created, reasoning, action, done, error
          // Frontend keys: SANDBOX_CREATED="sandbox_created", etc.
          return {
            ...parsed,
            type: eventType
          };
        }

        return parsed;
      } catch (e) {
        // If not JSON, treat as reasoning/content
        // Use eventType if available, else default to REASONING
        return {
          type: eventType || SSEEventType.REASONING,
          content: cleanData
        } as any;
      }
    } catch (error) {
      logError(
        "Error parsing SSE event:",
        error,
        "Data:",
        data.substring(0, 200) + (data.length > 200 ? "..." : "")
      );
      return null;
    }
  };

  const sendMessage = async ({
    content,
    sandboxId,
    environment,
    resolution,
  }: SendMessageOptions) => {
    if (isLoading) return;

    setIsLoading(true);
    setError(null);

    const userMessage: ChatMessage = {
      role: "user",
      content,
      id: Date.now().toString(),
    };

    setMessages((prev) => [...prev, userMessage]);

    abortControllerRef.current = new AbortController();

    try {
      const apiMessages = messages
        .concat(userMessage)
        .filter((msg) => msg.role === "user" || msg.role === "assistant")
        .map((msg) => {
          const typedMsg = msg as UserChatMessage | AssistantChatMessage;
          return {
            role: typedMsg.role,
            content: typedMsg.content,
          };
        });

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: apiMessages,
          sandboxId,
          environment,
          resolution,
          model,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("Response body is null");

      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          id: `system-message-${Date.now()}`,
          content: "Task started",
        },
      ]);

      const decoder = new TextDecoder();
      let assistantMessage = "";
      let buffer = "";
      let responseCounter = 0; // Local counter to ensure unique IDs during rapid SSE updates

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          if (buffer.trim()) {
            const parsedEvent = parseSSEEvent(buffer);
            if (parsedEvent) {
              if (parsedEvent.type === SSEEventType.DONE) {
                setMessages((prev) => {
                  const systemMessage: SystemChatMessage = {
                    role: "system",
                    id: `system-${Date.now()}-${responseCounter++}`, // Unique ID
                    content: "Task completed",
                  };

                  return [...prev, systemMessage];
                });
                setIsLoading(false);
              }
            }
          }
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        const events = buffer.split("\n\n");

        buffer = events.pop() || "";

        for (const event of events) {
          if (!event.trim()) continue;

          const parsedEvent = parseSSEEvent(event);
          if (!parsedEvent) continue;

          if (process.env.NODE_ENV === "development") {
            logDebug("Parsed event:", parsedEvent);
          }

          switch (parsedEvent.type) {
            case SSEEventType.ACTION:
              if (parsedEvent.action) {
                const actionMessage: ActionChatMessage<typeof model> = {
                  role: "action",
                  id: `action-${Date.now()}-${responseCounter++}`, // Unique ID
                  action: parsedEvent.action,
                  status: "pending",
                  model,
                };

                setMessages((prev) => [...prev, actionMessage]);
              }
              break;

            case SSEEventType.REASONING:
              if (typeof parsedEvent.content === "string") {
                setMessages((prev) => {
                  const lastMsg = prev[prev.length - 1];
                  // Append to previous assistant message if it exists
                  if (lastMsg && lastMsg.role === "assistant") {
                    const updatedMsg = {
                      ...lastMsg,
                      content: lastMsg.content + "\n" + parsedEvent.content
                    };
                    return [...prev.slice(0, -1), updatedMsg];
                  } else {
                    // Start new assistant message block
                    const reasoningMessage: AssistantChatMessage = {
                      role: "assistant",
                      id: `assistant-${Date.now()}-${responseCounter++}`,
                      content: parsedEvent.content,
                      model,
                    };
                    return [...prev, reasoningMessage];
                  }
                });
              }
              break;

            case SSEEventType.DONE:
              setMessages((prev) => {
                const systemMessage: SystemChatMessage = {
                  role: "system",
                  id: `system-${Date.now()}`,
                  content: parsedEvent.content || "Task completed",
                };

                return [...prev, systemMessage];
              });
              setIsLoading(false);
              break;

            case SSEEventType.ERROR:
              setError(parsedEvent.content);
              setMessages((prev) => [
                ...prev,
                {
                  role: "system",
                  id: `system-${Date.now()}`,
                  content: parsedEvent.content,
                  isError: true,
                },
              ]);
              setIsLoading(false);
              break;

            case SSEEventType.SANDBOX_CREATED:
              if (
                parsedEvent.sandboxId &&
                parsedEvent.vncUrl &&
                onSandboxCreatedRef.current
              ) {
                onSandboxCreatedRef.current(
                  parsedEvent.sandboxId,
                  parsedEvent.vncUrl
                );
              }
              break;

            case SSEEventType.ACTION_COMPLETED:
              setMessages((prev) => {
                const lastActionIndex = [...prev]
                  .reverse()
                  .findIndex((msg) => msg.role === "action");

                if (lastActionIndex !== -1) {
                  const actualIndex = prev.length - 1 - lastActionIndex;

                  return prev.map((msg, index) =>
                    index === actualIndex
                      ? { ...msg, status: "completed" }
                      : msg
                  );
                }

                return prev;
              });
              break;
          }
        }
      }
    } catch (error) {
      logError("Error sending message:", error);
      setError(error instanceof Error ? error.message : "An error occurred");
      setIsLoading(false);
    }
  };

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      try {
        abortControllerRef.current.abort(
          new DOMException("Generation stopped by user", "AbortError")
        );
        setIsLoading(false);
      } catch (error) {
        logError("Error stopping generation:", error);
        setIsLoading(false);
      }
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent): string | undefined => {
      e.preventDefault();
      if (!input.trim()) return;

      const content = input.trim();
      setInput("");
      return content;
    },
    [input]
  );

  const value = {
    messages,
    isLoading,
    error,
    input,
    setInput,
    sendMessage,
    stopGeneration,
    clearMessages,
    handleSubmit,
    model,
    setModel,
    onSandboxCreated: (
      callback: (sandboxId: string, vncUrl: string) => void
    ) => {
      onSandboxCreatedRef.current = callback;
    },
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
