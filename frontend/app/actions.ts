"use server";

/**
 * Server actions for local Docker container management.
 * No E2B dependency - uses local Docker container.
 */

export async function increaseTimeout(sandboxId: string) {
  // Local Docker doesn't need timeout management
  console.log("Local Docker mode - timeout management not needed");
  return true;
}

export async function stopSandboxAction(sandboxId: string) {
  try {
    // For local Docker, we could stop the container but it's better to leave it running
    console.log("Local Docker mode - container will continue running for reuse");
    return true;
  } catch (error) {
    console.error("Failed to stop sandbox:", error);
    return false;
  }
}
