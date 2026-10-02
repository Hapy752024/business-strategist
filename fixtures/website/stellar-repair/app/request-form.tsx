"use client";

import { FormEvent, useState } from "react";

type State = "idle" | "pending" | "success" | "error";

export function RequestForm() {
  const [state, setState] = useState<State>("idle");
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state === "pending") return;
    const form = event.currentTarget;
    setState("pending"); setMessage("Sending demo request…");
    try {
      const response = await fetch("/api/demo-request", { method: "POST", body: new FormData(form) });
      const payload = await response.json();
      if (!response.ok) { setState("error"); setMessage(payload.error || "Please check the form and try again."); return; }
      setState("success"); setMessage(payload.message); form.reset();
    } catch {
      setState("error"); setMessage("The demo request could not be sent. Your entries are still here; please retry.");
    }
  }

  return <form onSubmit={submit}>
    <label htmlFor="repair">What needs repair?</label>
    <textarea id="repair" name="repair" required minLength={8} maxLength={500} />
    <label htmlFor="email">Email for a reply</label>
    <input id="email" name="email" type="email" required maxLength={254} />
    <button type="submit" disabled={state === "pending"}>{state === "pending" ? "Sending…" : "Send demo request"}</button>
    <p role="status" aria-live="polite">{message}</p>
  </form>;
}
