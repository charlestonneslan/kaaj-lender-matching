import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function NewLender() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [slug, setSlug] = useState("");
  const [name, setName] = useState("");
  const [contact, setContact] = useState("");
  const [notes, setNotes] = useState("");

  const mut = useMutation({
    mutationFn: () =>
      api.createLender({
        slug,
        name,
        contact: contact || null,
        notes: notes || null,
      }),
    onSuccess: (lender) => {
      qc.invalidateQueries({ queryKey: ["lenders"] });
      navigate(`/lenders/${lender.id}`);
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        mut.mutate();
      }}
      className="bg-white border border-slate-200 rounded p-5 space-y-4 max-w-xl"
    >
      <div>
        <h2 className="font-semibold">Add a lender</h2>
        <p className="text-sm text-slate-500 mt-1">
          Start with the basics. Add programs and rules from the lender detail page.
        </p>
      </div>
      <Field label="Slug (unique, lowercase)">
        <input
          required
          className="input"
          value={slug}
          onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/\s+/g, "_"))}
        />
      </Field>
      <Field label="Name">
        <input
          required
          className="input"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </Field>
      <Field label="Contact">
        <input
          className="input"
          value={contact}
          onChange={(e) => setContact(e.target.value)}
        />
      </Field>
      <Field label="Notes">
        <textarea
          className="input min-h-24"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </Field>
      <div className="flex gap-3 items-center">
        <button
          type="submit"
          disabled={mut.isPending}
          className="bg-slate-900 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
        >
          {mut.isPending ? "Saving…" : "Create lender"}
        </button>
        {mut.isError ? (
          <span className="text-red-600 text-sm">{(mut.error as Error).message}</span>
        ) : null}
      </div>
      <style>{`
        .input { width: 100%; border: 1px solid rgb(203 213 225); padding: 6px 10px; border-radius: 4px; font-size: 14px; background: white; }
        .input:focus { outline: 2px solid rgb(15 23 42); outline-offset: -1px; }
      `}</style>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="text-slate-600 block mb-1">{label}</span>
      {children}
    </label>
  );
}
