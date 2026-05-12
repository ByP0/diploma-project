import type { ReactNode } from "react";
import { EmptyState } from "./EmptyState";

export type DataTableColumn<TRow> = {
  align?: "center" | "left" | "right";
  key: string;
  render: (row: TRow) => ReactNode;
  title: string;
};

type DataTableProps<TRow> = {
  columns: DataTableColumn<TRow>[];
  empty?: ReactNode;
  getRowKey: (row: TRow, index: number) => string;
  rows: TRow[];
};

export function DataTable<TRow,>({ columns, empty, getRowKey, rows }: DataTableProps<TRow>) {
  if (!rows.length) {
    return empty ?? <EmptyState description="There is no data to display yet." title="No records" />;
  }

  return (
    <div className="ds-table-wrap">
      <table className="ds-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th className={column.align ? `is-${column.align}` : undefined} key={column.key} scope="col">
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={getRowKey(row, index)}>
              {columns.map((column) => (
                <td className={column.align ? `is-${column.align}` : undefined} key={column.key}>
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
