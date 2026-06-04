import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { ApplicationCreate } from "../types";

const INITIAL: ApplicationCreate = {
  borrower: {
    legal_name: "Acme Equipment LLC",
    industry: "construction",
    state: "TX",
    years_in_business: 5,
    annual_revenue: 500000,
    is_us_citizen: true,
    has_physical_location: true,
    is_startup: false,
  },
  guarantor: {
    name: "Pat Owner",
    fico: 720,
    revolving_balance: 10000,
    unsecured_debt: 5000,
    homeowner: true,
    has_bankruptcy: false,
    bk_discharge_years: null,
    has_judgments: false,
    has_foreclosure: false,
    has_repossession: false,
    has_tax_lien: false,
    has_recent_collections: false,
  },
  business_credit: {
    paynet_score: 690,
    comparable_credit_pct: 85,
    trade_lines_count: 6,
    clean_payment_history_months: 24,
  },
  loan_request: {
    amount: 100000,
    term_months: 60,
    equipment_type: "skid_steer",
    equipment_year: 2024,
    equipment_age_years: 1,
    down_payment_pct: 15,
    is_private_party: false,
  },
};

export default function NewApplication() {
  const [form, setForm] = useState<ApplicationCreate>(INITIAL);
  const navigate = useNavigate();

  const createMut = useMutation({
    mutationFn: api.createApplication,
    onSuccess: async (app) => {
      await api.evaluate(app.id);
      navigate(`/applications/${app.id}`);
    },
  });

  const update = <K extends keyof ApplicationCreate>(
    section: K,
    patch: Partial<ApplicationCreate[K]>,
  ) => setForm((f) => ({ ...f, [section]: { ...f[section], ...patch } }));

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        createMut.mutate(form);
      }}
      className="space-y-6"
    >
      <Section title="Borrower / Business">
        <Field label="Legal name">
          <input
            className="input"
            value={form.borrower.legal_name}
            onChange={(e) => update("borrower", { legal_name: e.target.value })}
          />
        </Field>
        <Field label="Industry">
          <select
            className="input"
            value={form.borrower.industry}
            onChange={(e) => update("borrower", { industry: e.target.value })}
          >
            <option value="construction">Construction</option>
            <option value="manufacturing">Manufacturing</option>
            <option value="machine_tools">Machine Tools</option>
            <option value="trucking">Trucking</option>
            <option value="logging">Logging</option>
            <option value="medical">Medical</option>
            <option value="restaurant">Restaurant</option>
            <option value="cannabis">Cannabis</option>
            <option value="oil_gas">Oil & Gas</option>
            <option value="other">Other</option>
          </select>
        </Field>
        <Field label="State (2 letter)">
          <input
            className="input uppercase"
            maxLength={2}
            value={form.borrower.state}
            onChange={(e) => update("borrower", { state: e.target.value.toUpperCase() })}
          />
        </Field>
        <Field label="Years in business">
          <input
            type="number"
            step="0.5"
            className="input"
            value={form.borrower.years_in_business}
            onChange={(e) =>
              update("borrower", { years_in_business: Number(e.target.value) })
            }
          />
        </Field>
        <Field label="Annual revenue">
          <input
            type="number"
            className="input"
            value={form.borrower.annual_revenue}
            onChange={(e) =>
              update("borrower", { annual_revenue: Number(e.target.value) })
            }
          />
        </Field>
        <Field label="">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.borrower.is_us_citizen}
              onChange={(e) => update("borrower", { is_us_citizen: e.target.checked })}
            />
            US Citizen
          </label>
        </Field>
        <Field label="">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.borrower.has_physical_location}
              onChange={(e) =>
                update("borrower", { has_physical_location: e.target.checked })
              }
            />
            Physical location
          </label>
        </Field>
        <Field label="">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.borrower.is_startup}
              onChange={(e) => update("borrower", { is_startup: e.target.checked })}
            />
            Startup
          </label>
        </Field>
      </Section>

      <Section title="Personal Guarantor">
        <Field label="Name">
          <input
            className="input"
            value={form.guarantor.name}
            onChange={(e) => update("guarantor", { name: e.target.value })}
          />
        </Field>
        <Field label="FICO">
          <input
            type="number"
            className="input"
            value={form.guarantor.fico}
            onChange={(e) => update("guarantor", { fico: Number(e.target.value) })}
          />
        </Field>
        <Field label="Revolving balance">
          <input
            type="number"
            className="input"
            value={form.guarantor.revolving_balance}
            onChange={(e) =>
              update("guarantor", { revolving_balance: Number(e.target.value) })
            }
          />
        </Field>
        <Field label="Unsecured debt">
          <input
            type="number"
            className="input"
            value={form.guarantor.unsecured_debt}
            onChange={(e) =>
              update("guarantor", { unsecured_debt: Number(e.target.value) })
            }
          />
        </Field>
        <Field label="">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.guarantor.homeowner}
              onChange={(e) => update("guarantor", { homeowner: e.target.checked })}
            />
            Homeowner
          </label>
        </Field>
        <Field label="">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.guarantor.has_bankruptcy}
              onChange={(e) =>
                update("guarantor", { has_bankruptcy: e.target.checked })
              }
            />
            Has bankruptcy
          </label>
        </Field>
        <Field label="BK discharge years (if any)">
          <input
            type="number"
            step="0.5"
            className="input"
            value={form.guarantor.bk_discharge_years ?? ""}
            onChange={(e) =>
              update("guarantor", {
                bk_discharge_years: e.target.value === "" ? null : Number(e.target.value),
              })
            }
          />
        </Field>
        <FlagRow
          flags={[
            ["has_judgments", "Judgments"],
            ["has_foreclosure", "Foreclosure"],
            ["has_repossession", "Repossession"],
            ["has_tax_lien", "Tax lien"],
            ["has_recent_collections", "Recent collections"],
          ]}
          form={form}
          update={update}
        />
      </Section>

      <Section title="Business Credit">
        <Field label="PayNet score">
          <input
            type="number"
            className="input"
            value={form.business_credit.paynet_score ?? ""}
            onChange={(e) =>
              update("business_credit", {
                paynet_score: e.target.value === "" ? null : Number(e.target.value),
              })
            }
          />
        </Field>
        <Field label="Comparable credit (% of request)">
          <input
            type="number"
            className="input"
            value={form.business_credit.comparable_credit_pct}
            onChange={(e) =>
              update("business_credit", {
                comparable_credit_pct: Number(e.target.value),
              })
            }
          />
        </Field>
      </Section>

      <Section title="Loan Request">
        <Field label="Amount ($)">
          <input
            type="number"
            className="input"
            value={form.loan_request.amount}
            onChange={(e) =>
              update("loan_request", { amount: Number(e.target.value) })
            }
          />
        </Field>
        <Field label="Term (months)">
          <input
            type="number"
            className="input"
            value={form.loan_request.term_months}
            onChange={(e) =>
              update("loan_request", { term_months: Number(e.target.value) })
            }
          />
        </Field>
        <Field label="Equipment type">
          <input
            className="input"
            value={form.loan_request.equipment_type}
            onChange={(e) =>
              update("loan_request", { equipment_type: e.target.value })
            }
          />
        </Field>
        <Field label="Equipment age (years)">
          <input
            type="number"
            step="0.5"
            className="input"
            value={form.loan_request.equipment_age_years ?? ""}
            onChange={(e) =>
              update("loan_request", {
                equipment_age_years:
                  e.target.value === "" ? null : Number(e.target.value),
              })
            }
          />
        </Field>
        <Field label="Down payment (%)">
          <input
            type="number"
            className="input"
            value={form.loan_request.down_payment_pct}
            onChange={(e) =>
              update("loan_request", { down_payment_pct: Number(e.target.value) })
            }
          />
        </Field>
        <Field label="">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.loan_request.is_private_party}
              onChange={(e) =>
                update("loan_request", { is_private_party: e.target.checked })
              }
            />
            Private party sale
          </label>
        </Field>
      </Section>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={createMut.isPending}
          className="bg-slate-900 text-white px-5 py-2 rounded text-sm disabled:opacity-50"
        >
          {createMut.isPending ? "Submitting…" : "Submit & Evaluate"}
        </button>
        {createMut.isError ? (
          <span className="text-red-600 text-sm self-center">
            {(createMut.error as Error).message}
          </span>
        ) : null}
      </div>

      <style>{`
        .input { width: 100%; border: 1px solid rgb(203 213 225); padding: 6px 10px; border-radius: 4px; font-size: 14px; background: white; }
        .input:focus { outline: 2px solid rgb(15 23 42); outline-offset: -1px; }
      `}</style>
    </form>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-white border border-slate-200 rounded p-5">
      <h2 className="font-semibold mb-4">{title}</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">{children}</div>
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      {label ? <span className="text-slate-600 block mb-1">{label}</span> : null}
      {children}
    </label>
  );
}

function FlagRow({
  flags,
  form,
  update,
}: {
  flags: [keyof ApplicationCreate["guarantor"], string][];
  form: ApplicationCreate;
  update: <K extends keyof ApplicationCreate>(
    section: K,
    patch: Partial<ApplicationCreate[K]>,
  ) => void;
}) {
  return (
    <>
      {flags.map(([key, label]) => (
        <Field key={key} label="">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={Boolean(form.guarantor[key])}
              onChange={(e) => update("guarantor", { [key]: e.target.checked } as Partial<ApplicationCreate["guarantor"]>)}
            />
            {label}
          </label>
        </Field>
      ))}
    </>
  );
}
