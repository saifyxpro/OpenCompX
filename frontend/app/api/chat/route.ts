
import { logError } from "@/lib/logger";

export const maxDuration = 600; // 10 minutes

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { messages, sandboxId, model, resolution, environment, image, selectedTool } = body;

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
        model,
        resolution,
        environment,
        image,
        selectedTool,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      logError(`Backend Error (${response.status}):`, errorText || response.statusText);
      return new Response(errorText || `Error communicating with Agent Backend: ${response.status}`, { status: response.status });
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
