import { exportFile, QTableColumn } from 'quasar';

/**
 * Export QTable data to a CSV file.
 * @param columns QTable columns definition
 * @param rows rows with data
 * @param fileName target file name
 */
export function exportTable(
  columns: QTableColumn[],
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  rows: any[],
  fileName = 'table-export',
) {
  // Format the headers (column titles)
  const headers = columns
    .filter((col) => !!col.field)
    .map((col) => col.label || col.name)
    .join(',');

  // Format the data rows
  const data = rows
    .map((row) => {
      return columns
        .map((col) => {
          let value =
            typeof col.field === 'function' ? col.field(row) : row[col.field];

          // Handle nested object paths
          if (typeof col.field === 'string' && col.field.includes('.')) {
            value = col.field.split('.').reduce((obj, key) => obj?.[key], row);
          }

          // Format the value for CSV
          value = formatValueForCSV(value);

          return value;
        })
        .join(',');
    })
    .join('\n');

  // Combine headers and data
  const content = `${headers}\n${data}`;

  // Use Quasar's exportFile utility
  const status = exportFile(`${fileName}.csv`, content, 'text/csv');

  if (!status) {
    throw new Error('Browser denied file download');
  }

  return status;
}

// Helper function to format values for CSV
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function formatValueForCSV(value: any) {
  if (value === null || value === undefined) {
    return '';
  }

  if (typeof value === 'object') {
    value = JSON.stringify(value);
  }

  // Escape quotes and wrap in quotes if contains comma or newline
  value = String(value).replace(/"/g, '""');
  if (value.includes(',') || value.includes('\n') || value.includes('"')) {
    value = `"${value}"`;
  }

  return value;
}
