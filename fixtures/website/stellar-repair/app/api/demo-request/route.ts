import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  let form: FormData;
  try { form = await request.formData(); }
  catch { return NextResponse.json({ error: "Please submit the form again." }, { status: 400 }); }
  const repair = form.get("repair");
  const email = form.get("email");
  if (typeof repair !== "string" || repair.trim().length < 8 || repair.length > 500 ||
      typeof email !== "string" || email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: "Enter a repair description and a valid email." }, { status: 400 });
  }
  // Deliberately do not store, log, echo or forward submitted fields.
  return NextResponse.json({ message: "Demo complete. No service request was sent or saved." }, { status: 200 });
}
