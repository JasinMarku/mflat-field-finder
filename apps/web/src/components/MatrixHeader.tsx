import { format } from "date-fns";

type Props = { days: Date[] };

export function MatrixHeader({ days }: Props) {
  return (
    <div className="sticky top-0 z-10 flex items-end gap-1 border-b border-zinc-200 bg-white px-3 py-2">
      <div className="w-64 shrink-0 text-xs font-medium uppercase tracking-wide text-zinc-500">
        Field
      </div>
      <div className="flex flex-1 gap-1">
        {days.map((day) => (
          <div
            key={day.toISOString()}
            className="flex-1 text-center text-xs leading-tight text-zinc-600"
          >
            <div className="font-medium text-zinc-900">{format(day, "EEE")}</div>
            <div className="text-zinc-500">{format(day, "M/d")}</div>
          </div>
        ))}
      </div>
      <div className="w-20 shrink-0 text-right text-xs font-medium uppercase tracking-wide text-zinc-500">
        Free hrs
      </div>
    </div>
  );
}
