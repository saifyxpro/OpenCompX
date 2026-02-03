
import { logError } from "@/lib/logger";

export const maxDuration = 300;

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { messages, sandboxId } = body;

    // Forward request to Python Agent-S3 Backend
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const response = await fetch(`${backendUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messages,
        sandboxId,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      logError("Backend Error:", errorText);
      return new Response(errorText || "Error communicating with Agent Backend", { status: 500 });
    }

    // Stream the response from the backend to the frontend
    // The backend already returns text/event-stream
    return new Response(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });

  } catch (error) {
    logError("Proxy Error:", error);
    return new Response("Internal Server Error", { status: 500 });
  }
}
