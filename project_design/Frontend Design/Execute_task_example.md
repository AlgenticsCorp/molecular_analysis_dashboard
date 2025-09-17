
# Page purpose

“Execute” wizard for launching a **Classic molecular docking (AutoDock 4)** job. Step 1 of 4: **Configure Parameters** → then Upload Files → Review & Execute → Monitor.

# Visual structure (center content)

* **Inline title row** (inside page body):

  * Title: `Classic molecular docking using AutoDock 4 algorithm for protein-ligand binding prediction`
  * Small **pills** to the right of the title (same line): `Docking` · `v4.2.6` · `CPU: medium` · `Duration: 5–30 minutes`
* **Wizard card** (white, soft shadow, rounded, generous padding)

  * **Left mini-stepper** (inside the card, not the global sidebar): 1–4 vertical dots with labels; step 1 active.
  * **Right content column** (the form):

    * Section heading: **Configure Parameters**
    * Group 1: **Required Parameters**

      * Four numeric inputs in the first row: `Search Space X Size*`, `Y*`, `Z*`, `GA Runs*`
      * One select below X (2nd row, col 1): `Output Format*` (value `pdbqt`)
      * Each field shows helper text; labels have optional “?” tooltip icon.
    * Group 2 (collapsible, default **open**): **Advanced Parameters (1)**

      * `Energy Evaluations` (default `2,500,000`) with helper: *Maximum number of energy evaluations*
    * **Footer actions** for this step (within the card): `BACK` (secondary) and `NEXT` (primary)

# Responsive layout

* Max content width \~1200–1280px, centered.
* Grid for Required Parameters:

  * ≥1200px: 4 columns.
  * 768–1199px: 2 columns.
  * <768px: 1 column.
* Tooltips anchored to the label’s `?` icon.

# Field details (exact copies of what’s in the screenshot)

**Required**

* Search Space X Size\* (number, default `20`) — helper: *Size of the search space in the X dimension (Angstroms)*
* Search Space Y Size\* (number, default `20`) — helper: *…Y dimension (Angstroms)*
* Search Space Z Size\* (number, default `20`) — helper: *…Z dimension (Angstroms)*
* GA Runs\* (integer, default `10`) — helper: *Number of genetic algorithm runs*
* Output Format\* (select, default `pdbqt`) — helper: *Format for the output files*
  **Advanced**
* Energy Evaluations (integer, default `2,500,000`) — helper: *Maximum number of energy evaluations*

# Navigation logic

* `BACK`: returns to the task card/details page.
* `NEXT`: validates, persists params to a wizard context, then routes to **Step 2: Upload Files**.

# State & validation (TypeScript)

```ts
// types
export type DockingParams = {
  xSize: number; // Å > 0
  ySize: number; // Å > 0
  zSize: number; // Å > 0
  gaRuns: number; // int >= 1
  outputFormat: "pdbqt";
  energyEvals?: number; // int >= 0
};

export const defaultParams: DockingParams = {
  xSize: 20,
  ySize: 20,
  zSize: 20,
  gaRuns: 10,
  outputFormat: "pdbqt",
  energyEvals: 2_500_000,
};
```

Using `react-hook-form + zod`:

```ts
import { z } from "zod";

export const schema = z.object({
  xSize: z.number({ required_error: "Required" }).positive(),
  ySize: z.number({ required_error: "Required" }).positive(),
  zSize: z.number({ required_error: "Required" }).positive(),
  gaRuns: z.number({ required_error: "Required" }).int().min(1),
  outputFormat: z.literal("pdbqt"),
  energyEvals: z.number().int().min(0).optional(),
});

export type FormValues = z.infer<typeof schema>;
```

# React component skeleton (Tailwind + RHF)

```tsx
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { schema, defaultParams, FormValues } from "./schema";
import { useWizard } from "../context/WizardContext"; // your context for multi-step state
import { useNavigate } from "react-router-dom";

export default function ExecuteDockingStep1() {
  const navigate = useNavigate();
  const { setParams, params } = useWizard(); // read/merge prior state
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: params ?? defaultParams,
    mode: "onBlur",
  });

  const onSubmit = (values: FormValues) => {
    setParams(values);
    navigate("/execute/upload"); // Step 2 route
  };

  return (
    <div className="mx-auto max-w-screen-xl space-y-4">
      {/* Inline title + pills */}
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="text-xl font-semibold">
          Classic molecular docking using AutoDock 4 algorithm for protein-ligand binding prediction
        </h1>
        <div className="flex flex-wrap gap-2 text-xs">
          {["Docking", "v4.2.6", "CPU: medium", "Duration: 5–30 minutes"].map((t) => (
            <span key={t} className="rounded-full bg-slate-100 px-2 py-1">{t}</span>
          ))}
        </div>
      </div>

      {/* Wizard card */}
      <div className="rounded-xl bg-white p-6 shadow">
        <div className="grid grid-cols-12 gap-6">
          {/* Mini stepper */}
          <aside className="col-span-12 md:col-span-2">
            <ol className="relative space-y-6 pl-4">
              {[
                { n: 1, label: "Configure Parameters", active: true },
                { n: 2, label: "Upload Files" },
                { n: 3, label: "Review & Execute" },
                { n: 4, label: "Monitor Progress" },
              ].map((s) => (
                <li key={s.n} className="flex items-start gap-3">
                  <span
                    className={`mt-0.5 inline-flex h-6 w-6 items-center justify-center rounded-full ${
                      s.active ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-600"
                    }`}
                  >
                    {s.n}
                  </span>
                  <span className={s.active ? "font-medium text-slate-900" : "text-slate-500"}>
                    {s.label}
                  </span>
                </li>
              ))}
              <span className="absolute left-6 top-3 h-[calc(100%-1.5rem)] w-px bg-slate-200" />
            </ol>
          </aside>

          {/* Form content */}
          <section className="col-span-12 md:col-span-10">
            <h2 className="mb-4 text-lg font-semibold">Configure Parameters</h2>

            {/* Required Parameters */}
            <fieldset className="mb-6 rounded-lg border border-slate-200 p-4">
              <legend className="px-1 text-sm font-medium text-slate-700">Required Parameters</legend>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
                {/* X */}
                <FormNumber
                  label="Search Space X Size*"
                  hint="Size of the search space in the X dimension (Angstroms)"
                  error={errors.xSize?.message}
                  {...register("xSize", { valueAsNumber: true })}
                />
                {/* Y */}
                <FormNumber
                  label="Search Space Y Size*"
                  hint="Size of the search space in the Y dimension (Angstroms)"
                  error={errors.ySize?.message}
                  {...register("ySize", { valueAsNumber: true })}
                />
                {/* Z */}
                <FormNumber
                  label="Search Space Z Size*"
                  hint="Size of the search space in the Z dimension (Angstroms)"
                  error={errors.zSize?.message}
                  {...register("zSize", { valueAsNumber: true })}
                />
                {/* GA runs */}
                <FormNumber
                  label="GA Runs*"
                  hint="Number of genetic algorithm runs"
                  error={errors.gaRuns?.message}
                  {...register("gaRuns", { valueAsNumber: true })}
                />
                {/* Output format (second row, first col) */}
                <div className="xl:col-span-1 md:col-span-2">
                  <FormSelect
                    label="Output Format*"
                    options={[{ label: "pdbqt", value: "pdbqt" }]}
                    hint="Format for the output files"
                    error={errors.outputFormat?.message}
                    {...register("outputFormat")}
                  />
                </div>
              </div>
            </fieldset>

            {/* Advanced */}
            <details open className="mb-6 rounded-lg border border-slate-200 p-4">
              <summary className="cursor-pointer text-sm font-medium text-slate-700">
                Advanced Parameters (1)
              </summary>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <FormNumber
                  label="Energy Evaluations"
                  hint="Maximum number of energy evaluations"
                  error={errors.energyEvals?.message}
                  {...register("energyEvals", { valueAsNumber: true })}
                />
              </div>
            </details>

            {/* Footer actions */}
            <div className="flex items-center justify-start gap-3">
              <button
                type="button"
                className="rounded-lg border border-slate-300 px-4 py-2 text-slate-700 hover:bg-slate-50"
                onClick={() => navigate(-1)}
              >
                BACK
              </button>
              <button
                type="button"
                onClick={handleSubmit(onSubmit)}
                className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
              >
                NEXT
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

/** Minimal form controls used above */
type FieldProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string;
};

function FormNumber({ label, hint, error, ...rest }: FieldProps) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      <input
        {...rest}
        inputMode="decimal"
        type="number"
        className={`w-full rounded-lg border px-3 py-2 outline-none ${
          error ? "border-red-500" : "border-slate-300 focus:border-blue-500"
        }`}
      />
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </label>
  );
}

function FormSelect({
  label,
  hint,
  error,
  options,
  ...rest
}: FieldProps & { options: { label: string; value: string }[] }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      <select
        {...(rest as any)}
        className={`w-full rounded-lg border px-3 py-2 outline-none ${
          error ? "border-red-500" : "border-slate-300 focus:border-blue-500"
        }`}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </label>
  );
}
```

# Accessibility & UX notes

* Associate each label with `id`/`htmlFor`. Add `aria-describedby` to tie errors/help text.
* Use `inputMode="numeric"` on GA Runs and Energy Evaluations for better mobile keyboards.
* Add tooltip content to the “?” icons (e.g., `title` or a popover component).
  Example texts:

  * Search Space sizes: “Docking grid edge length in Å (Angstroms).”
  * GA Runs: “Independent genetic algorithm runs; higher = more thorough, slower.”
  * Output Format: “AutoDock-compatible PDBQT result files.”
* Persist step state in context or URL query to survive refresh.
