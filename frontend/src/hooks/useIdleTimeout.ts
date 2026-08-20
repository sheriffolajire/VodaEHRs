/**
 * Idle session timeout hook.
 * 
 * Automatically logs out the user after a period of inactivity.
 * Resets the timer on user activity (mouse, keyboard, touch).
 * 
 * Security: Prevents session hijacking from abandoned browser sessions.
 */

import { useEffect, useRef, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";

const IDLE_TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes
const WARNING_BEFORE_MS = 60 * 1000; // 1 minute warning

export function useIdleTimeout(
  onWarning?: (remainingSeconds: number) => void,
  onTimeout?: () => void
) {
  const { logout } = useAuth();
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const warningRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastActivityRef = useRef<number>(Date.now());

  const resetTimer = useCallback(() => {
    lastActivityRef.current = Date.now();

    // Clear existing timers
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    if (warningRef.current) {
      clearTimeout(warningRef.current);
    }

    // Set warning timer
    warningRef.current = setTimeout(() => {
      onWarning?.(60); // 60 seconds remaining
    }, IDLE_TIMEOUT_MS - WARNING_BEFORE_MS);

    // Set logout timer
    timeoutRef.current = setTimeout(async () => {
      onTimeout?.();
      await logout();
      window.location.href = "/login?reason=session_expired";
    }, IDLE_TIMEOUT_MS);
  }, [logout, onWarning, onTimeout]);

  useEffect(() => {
    // Activity events to monitor
    const events = [
      "mousedown",
      "mousemove",
      "keypress",
      "scroll",
      "touchstart",
      "click",
      "keydown",
    ];

    // Add event listeners
    const handleActivity = () => {
      resetTimer();
    };

    events.forEach((event) => {
      document.addEventListener(event, handleActivity);
    });

    // Initial timer setup
    resetTimer();

    // Cleanup
    return () => {
      events.forEach((event) => {
        document.removeEventListener(event, handleActivity);
      });
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (warningRef.current) {
        clearTimeout(warningRef.current);
      }
    };
  }, [resetTimer]);

  return { resetTimer, lastActivity: lastActivityRef.current };
}
